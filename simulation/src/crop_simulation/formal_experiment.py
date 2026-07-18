"""Formal Issue 6 experiment execution under the frozen design and run protocol."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import numpy as np
import pandas as pd
from scipy.stats import norm

from crop_optimization.benchmark_policies import (
    mean_variance_policy,
    suitability_proportional_policy,
)
from crop_optimization.cvar_optimizer import (
    AllocationResult,
    solve_cvar_allocation,
    solve_expected_profit_allocation,
)
from crop_optimization.evaluation import (
    allocation_metrics,
    empirical_var_cvar_losses,
    pseudo_diversification_diagnostic,
)
from crop_optimization.optimal_face_audit import audit_pairwise_optimal_face

from .panel_calibration import (
    clayton_theta_from_kendall_tau,
    equicorrelation_from_kendall_tau,
    load_margin_matrix,
    panel_calibration,
)
from .scenario_generation import generate_profit_scenarios

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL = ROOT / "simulation/configs/formal_run_protocol.yaml"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scenario_spec(cell: Dict[str, Any], n_crops: int, margin_matrix: np.ndarray) -> Tuple[str, Any, Dict[str, Any]]:
    tau = float(cell["kendall_tau"])
    copula_family = str(cell["copula_family"])
    if copula_family == "gaussian":
        copula_type = "Gaussian"
        copula_param: Any = equicorrelation_from_kendall_tau(tau, n_crops)
    elif copula_family == "student_t_df4":
        copula_type = "Student-t"
        copula_param = {"df": 4, "corr": equicorrelation_from_kendall_tau(tau, n_crops)}
    elif copula_family == "clayton":
        copula_type = "Clayton"
        copula_param = clayton_theta_from_kendall_tau(tau)
    else:
        raise ValueError(f"unknown copula family: {copula_family}")

    marginal_family = str(cell["marginal_family"])
    if marginal_family == "gaussian":
        marginal = {"type": "normal"}
    elif marginal_family == "student_t_df5":
        marginal = {"type": "student_t", "df": 5}
    elif marginal_family == "empirical_resample":
        marginal = {"type": "empirical_resample", "samples": margin_matrix.tolist()}
    else:
        raise ValueError(f"unknown marginal family: {marginal_family}")
    return copula_type, copula_param, marginal


def operational_spec(cell: Dict[str, Any], calibration: Dict[str, Any]) -> Dict[str, Any]:
    crop_names = list(calibration["crop_names"])
    costs = np.asarray([calibration["costs_2024_real"][crop] for crop in crop_names], dtype=float)
    cap = float(cell["dominant_crop_cap_share"])
    contract = float(cell["contract_minimum_share"])
    return {
        "crop_names": crop_names,
        "costs": costs,
        "total_land": 1.0,
        "budget": float(cell["budget_to_max_cost_ratio"]) * float(costs.max()),
        "lower": np.zeros(len(crop_names)),
        "upper": np.ones(len(crop_names)),
        "rotation_caps": {crop_names[0]: cap} if cap < 1.0 else {},
        "contract_minimums": {crop_names[-1]: contract} if contract > 0 else {},
    }


def direct_cvar(scenarios: np.ndarray, allocation: Iterable[float], alpha: float) -> float:
    losses = -(scenarios @ np.asarray(list(allocation), dtype=float))
    return empirical_var_cvar_losses(losses, alpha)[1]


def reference_policies(
    scenarios: np.ndarray,
    means: np.ndarray,
    spec: Dict[str, Any],
    alpha: float,
) -> Tuple[Dict[str, Any], AllocationResult, float, Dict[str, float]]:
    crop_names = spec["crop_names"]
    suitability = suitability_proportional_policy(
        means, spec["total_land"], spec["costs"], spec["budget"], spec["lower"],
        spec["upper"], spec["rotation_caps"], crop_names, spec["contract_minimums"],
    )
    expected = solve_expected_profit_allocation(
        scenarios.mean(axis=0), spec["costs"], spec["total_land"], spec["budget"],
        spec["lower"], spec["upper"], spec["rotation_caps"], crop_names,
        spec["contract_minimums"],
    )
    if suitability.get("allocation") is None or expected.allocation is None:
        raise RuntimeError("risk-frontier reference policy is infeasible")
    risks = {
        "ranking_proportional": direct_cvar(scenarios, suitability["allocation"], alpha),
        "expected_profit": direct_cvar(scenarios, expected.allocation, alpha),
    }
    return suitability, expected, min(risks.values()), risks


def calibrated_risk_limit(risks: Dict[str, float], frontier_quantile: float) -> float:
    low = min(risks.values())
    high = max(risks.values())
    q = float(frontier_quantile)
    if not 0.0 <= q <= 1.0:
        raise ValueError("risk frontier quantile must be in [0, 1]")
    return float(low + q * (high - low))


def _policy_row(
    policy: str,
    stage: str,
    status: str,
    allocation: np.ndarray | None,
    scenarios: np.ndarray,
    spec: Dict[str, Any],
    alpha: float,
    risk_limit: float,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {"policy": policy, "mechanism_stage": stage, "status": status}
    if allocation is None:
        return row
    metrics = allocation_metrics(
        allocation, scenarios, spec["costs"], spec["total_land"], spec["budget"],
        alpha, risk_limit, spec["crop_names"], spec["lower"], spec["upper"],
        spec["rotation_caps"], spec["contract_minimums"],
    )
    row.update(metrics)
    row["selected_reversal"] = bool(
        allocation[spec["crop_names"].index("Soybean")]
        > allocation[spec["crop_names"].index("Corn")] + 1e-4
    )
    return row


def run_replication(
    cell: Dict[str, Any],
    replication_seed: int,
    n_scenarios: int,
    *,
    audit_face: bool = True,
    solver_method: str = "highs",
) -> Tuple[Dict[str, Any], list[Dict[str, Any]]]:
    calibration = panel_calibration()
    margin_matrix = load_margin_matrix().to_numpy()
    crop_names = list(calibration["crop_names"])
    means = np.asarray([calibration["means"][crop] for crop in crop_names], dtype=float)
    stds = np.asarray([calibration["stds"][crop] for crop in crop_names], dtype=float)
    copula_type, copula_param, marginal = scenario_spec(cell, len(crop_names), margin_matrix)
    scenarios, metadata = generate_profit_scenarios(
        means, stds, int(n_scenarios), copula_type, copula_param, int(replication_seed),
        crop_names=crop_names, marginal_model=marginal,
    )
    scenario_hash = hashlib.sha256(np.ascontiguousarray(scenarios).tobytes()).hexdigest()
    spec = operational_spec(cell, calibration)
    alpha = float(cell["alpha"])
    suitability, expected, _, reference_risks = reference_policies(scenarios, means, spec, alpha)
    risk_limit = calibrated_risk_limit(
        reference_risks, float(cell["risk_limit_frontier_quantile"])
    )
    primary = solve_cvar_allocation(
        scenarios, spec["costs"], spec["total_land"], spec["budget"], alpha,
        risk_limit, spec["lower"], spec["upper"], spec["rotation_caps"], crop_names,
        spec["contract_minimums"], solver_method=solver_method,
    )
    if audit_face:
        face = audit_pairwise_optimal_face(
            scenarios, spec["costs"], spec["total_land"], spec["budget"], alpha,
            risk_limit, spec["lower"], spec["upper"], crop_names, "Corn", "Soybean",
            rotation_caps=spec["rotation_caps"],
            contract_minimums=spec["contract_minimums"],
            allocation_tolerance=1e-4,
            objective_relative_tolerance=1e-8,
            primary_result=primary,
            solver_method=solver_method,
        )
    else:
        difference = math.nan
        if primary.allocation is not None:
            difference = float(primary.allocation[0] - primary.allocation[1])
        face = {
            "status": "not_run",
            "selected_difference": difference,
            "selected_reversal": bool(difference < -1e-4),
            "possible_reversal": False,
            "universal_reversal": False,
        }

    row: Dict[str, Any] = {
        "design_id": cell["design_id"],
        "design_sha256": cell["design_sha256"],
        "protocol_sha256": file_sha256(PROTOCOL),
        "cell_id": cell["cell_id"],
        "cell_type": cell["cell_type"],
        "replication_seed": int(replication_seed),
        "n_scenarios": int(n_scenarios),
        "scenario_sha256": scenario_hash,
        "copula_family": cell["copula_family"],
        "marginal_family": cell["marginal_family"],
        "kendall_tau": float(cell["kendall_tau"]),
        "alpha": alpha,
        "risk_limit_frontier_quantile": float(cell["risk_limit_frontier_quantile"]),
        "risk_limit": risk_limit,
        "risk_reference_low": min(reference_risks.values()),
        "risk_reference_high": max(reference_risks.values()),
        "budget_to_max_cost_ratio": float(cell["budget_to_max_cost_ratio"]),
        "budget": spec["budget"],
        "dominant_crop_cap_share": float(cell["dominant_crop_cap_share"]),
        "contract_minimum_share": float(cell["contract_minimum_share"]),
        "solver_method": solver_method,
        "solver_status": primary.status,
        "solver_status_code": primary.solver_status,
        "expected_profit": primary.expected_profit,
        "cvar_loss": primary.cvar_loss,
        "var_loss": primary.var_loss,
        "selected_reversal": bool(face.get("selected_reversal", False)),
        "possible_reversal": bool(face.get("possible_reversal", False)),
        "universal_reversal": bool(face.get("universal_reversal", False)),
        "face_status": face.get("status"),
        "face_min_difference": face.get("min_difference"),
        "face_max_difference": face.get("max_difference"),
        "face_width": face.get("optimal_face_width"),
        "lower_tail_dependence": metadata["lower_tail_dependence"],
        "copula_ordering_scope": metadata["ordering_scope"],
        "manuscript_admissible": "CONDITIONAL_ON_CONVERGENCE_AUDIT",
    }
    if primary.allocation is not None:
        for crop, value in zip(crop_names, primary.allocation):
            row[f"allocation_{crop}"] = float(value)
        pseudo = pseudo_diversification_diagnostic(
            primary.allocation, means, np.corrcoef(scenarios, rowvar=False),
            float(metadata["lower_tail_dependence"]),
        )
        row.update(pseudo)
    row.update({key: value for key, value in primary.diagnostics.items() if np.isscalar(value)})

    mean_variance = mean_variance_policy(
        scenarios, spec["costs"], spec["total_land"], spec["budget"], spec["lower"],
        spec["upper"], spec["rotation_caps"], crop_names, gamma=1e-6,
        start=expected.allocation, contract_minimums=spec["contract_minimums"],
    )
    policies = [
        _policy_row("ranking_proportional_repaired", "ranking", str(suitability["status"]),
                    np.asarray(suitability["allocation"]), scenarios, spec, alpha, risk_limit),
        _policy_row("expected_profit", "economic_plus_operational", expected.status,
                    expected.allocation, scenarios, spec, alpha, risk_limit),
        _policy_row("mean_variance", "variance_penalty", str(mean_variance["status"]),
                    np.asarray(mean_variance["allocation"]), scenarios, spec, alpha, risk_limit),
        _policy_row("loss_CVaR", "economic_operational_plus_CVaR", primary.status,
                    primary.allocation, scenarios, spec, alpha, risk_limit),
    ]
    for policy_row in policies:
        policy_row.update({
            "cell_id": cell["cell_id"],
            "replication_seed": int(replication_seed),
            "scenario_sha256": scenario_hash,
            "copula_family": cell["copula_family"],
            "marginal_family": cell["marginal_family"],
            "kendall_tau": float(cell["kendall_tau"]),
            "alpha": alpha,
            "risk_limit": risk_limit,
        })
    return row, policies


def wilson_interval(successes: int, trials: int, confidence: float = 0.95) -> Tuple[float, float]:
    if trials <= 0:
        return math.nan, math.nan
    z = float(norm.ppf(0.5 + confidence / 2.0))
    phat = successes / trials
    denom = 1.0 + z * z / trials
    center = (phat + z * z / (2.0 * trials)) / denom
    half = z * math.sqrt(phat * (1.0 - phat) / trials + z * z / (4.0 * trials * trials)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def cell_summary(results: pd.DataFrame) -> pd.DataFrame:
    rows: list[Dict[str, Any]] = []
    for cell_id, part in results.groupby("cell_id", sort=False):
        successes = int(part["selected_reversal"].sum())
        lo, hi = wilson_interval(successes, len(part))
        row: Dict[str, Any] = {
            "cell_id": cell_id,
            "replications": int(len(part)),
            "optimal_replications": int(part["solver_status"].eq("optimal").sum()),
            "selected_reversal_probability": successes / len(part),
            "selected_reversal_wilson_low": lo,
            "selected_reversal_wilson_high": hi,
            "selected_reversal_wilson_width": hi - lo,
            "possible_reversal_probability": float(part["possible_reversal"].mean()),
            "universal_reversal_probability": float(part["universal_reversal"].mean()),
            "pseudo_diversification_probability": float(part["pseudo_diversification_flag"].mean()),
        }
        for metric in ("expected_profit", "cvar_loss", "allocation_Corn", "allocation_Soybean", "allocation_Winter Wheat"):
            values = part[metric].dropna().astype(float)
            row[f"{metric}_mean"] = float(values.mean()) if len(values) else math.nan
            row[f"{metric}_mcse"] = float(values.std(ddof=1) / math.sqrt(len(values))) if len(values) > 1 else math.nan
            row[f"{metric}_replication_min"] = float(values.min()) if len(values) else math.nan
            row[f"{metric}_replication_max"] = float(values.max()) if len(values) else math.nan
        for factor in (
            "cell_type", "copula_family", "marginal_family", "kendall_tau", "alpha",
            "risk_limit_frontier_quantile", "budget_to_max_cost_ratio",
            "dominant_crop_cap_share", "contract_minimum_share",
        ):
            row[factor] = part.iloc[0][factor]
        rows.append(row)
    return pd.DataFrame(rows)


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value
