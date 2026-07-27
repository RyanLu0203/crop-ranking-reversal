#!/usr/bin/env python3
"""Run the registered Issue #34 full-model reconstruction experiment.

The workflow starts from the official-data-derived Kansas state crop panel,
constructs a pre-decision historical-yield-potential score, calibrates margin
scenarios, solves the complete operational model, and writes tidy source data
for manuscript tables and figures.  Simulated scenarios remain structural
stress-test evidence; they are never counted as empirical observations.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

import numpy as np
import pandas as pd
import yaml
from scipy import stats
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "simulation/src"), str(ROOT / "optimization/src")]

from crop_optimization.benchmark_policies import (
    mean_variance_policy,
    repair_allocation_to_feasible,
    suitability_proportional_policy,
)
from crop_optimization.cvar_optimizer import (
    AllocationResult,
    solve_cvar_allocation,
    solve_expected_profit_allocation,
    solve_minimum_cvar_allocation,
)
from crop_optimization.evaluation import allocation_metrics
from crop_optimization.optimal_face_audit import audit_reversal_optimal_face
from crop_simulation.panel_calibration import (
    clayton_theta_from_kendall_tau,
    equicorrelation_from_kendall_tau,
)
from crop_simulation.scenario_generation import generate_profit_scenarios


DESIGN_PATH = ROOT / "simulation/configs/issue34_full_model_design.yaml"
PANEL_PATH = ROOT / "empirical/goal16/outputs/extended_state_crop_panel.csv"
OUT = ROOT / "reconstruction/issue34/outputs"
CROPS = ["Corn", "Soybean", "Winter Wheat"]
CROP_MAP = {"corn": "Corn", "soybeans": "Soybean", "winter_wheat": "Winter Wheat"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return [jsonable(item) for item in value.tolist()]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def load_design() -> Dict[str, Any]:
    design = yaml.safe_load(DESIGN_PATH.read_text(encoding="utf-8"))
    if (
        design["status"] != "FROZEN_BEFORE_RESULTS"
        or design["owner_issue"] != 34
        or design.get("repair_issue") != 36
    ):
        raise ValueError("Issue #34 design and Issue #36 repair must be registered")
    design["design_sha256"] = sha256(DESIGN_PATH)
    return design


def load_calibration(design: Mapping[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    panel = pd.read_csv(PANEL_PATH)
    start, end = design["scope"]["calibration_years"]
    calibration = panel.loc[
        panel["state"].eq(design["scope"]["geography"])
        & panel["year"].between(start, end)
    ].copy()
    calibration["crop"] = calibration["crop"].map(CROP_MAP)
    if (
        calibration.shape[0] != 24
        or calibration["year"].nunique() != 8
        or calibration.groupby("year")["crop"].nunique().ne(3).any()
    ):
        raise ValueError("expected a complete Kansas 2016--2023 three-crop panel")
    margin_col = "standardized_operating_margin_real_2024_usd_per_acre"
    rows = []
    for crop in CROPS:
        part = calibration.loc[calibration["crop"].eq(crop)].sort_values("year")
        rows.append({
            "crop": crop,
            "score_name": design["score"]["name"],
            "historical_yield_potential_score": float(part["relative_yield"].mean()),
            "score_training_start": int(start),
            "score_training_end": int(end),
            "score_observations": int(len(part)),
            "mean_margin_real_2024_usd_per_acre": float(part[margin_col].mean()),
            "sd_margin_real_2024_usd_per_acre": float(part[margin_col].std(ddof=1)),
            "mean_yield_bushels_per_acre": float(part["yield_bushels_per_acre"].mean()),
            "mean_price_usd_per_bushel": float(part["harvest_price_usd_per_bushel"].mean()),
            "mean_operating_cost_nominal_usd_per_acre": float(
                part["operating_cost_usd_per_planted_acre"].mean()
            ),
            "score_uses_evaluation_year": False,
            "evidence_class": design["scope"]["evidence_class"],
        })
    return calibration.sort_values(["year", "crop"]), pd.DataFrame(rows)


def arrays(
    calibration: pd.DataFrame, calibration_summary: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    margin_col = "standardized_operating_margin_real_2024_usd_per_acre"
    margin_matrix = (
        calibration.pivot(index="year", columns="crop", values=margin_col)[CROPS]
        .sort_index()
        .to_numpy()
    )
    indexed = calibration_summary.set_index("crop")
    means = indexed.loc[CROPS, "mean_margin_real_2024_usd_per_acre"].to_numpy(float)
    stds = indexed.loc[CROPS, "sd_margin_real_2024_usd_per_acre"].to_numpy(float)
    scores = indexed.loc[CROPS, "historical_yield_potential_score"].to_numpy(float)
    return margin_matrix, means, stds, scores


def operational_spec(design: Mapping[str, Any], calibration: pd.DataFrame) -> Dict[str, Any]:
    opt = design["optimization"]
    latest = calibration.sort_values("year").groupby("crop").tail(1).set_index("crop")
    costs = np.asarray(
        [
            float(
                latest.loc[crop, "operating_cost_usd_per_planted_acre"]
                * latest.loc[crop, "cpi_u_deflator_to_2024"]
            )
            for crop in CROPS
        ]
    )
    return {
        "crop_names": CROPS,
        "costs": costs,
        "total_land": float(opt["total_land"]),
        "budget": float(opt["operating_budget_2024_usd_per_normalized_acre"]),
        "lower": np.asarray([opt["lower_bounds"][crop] for crop in CROPS], dtype=float),
        "upper": np.asarray([opt["upper_bounds"][crop] for crop in CROPS], dtype=float),
        "rotation_caps": dict(opt["rotation_caps"]),
        "contract_minimums": dict(opt["contract_minimums"]),
        "shared_capacity_constraints": dict(opt["shared_capacity_constraints"]),
    }


def copula_parameters(family: str, tau: float) -> tuple[str, Any]:
    if family == "gaussian":
        return "Gaussian", equicorrelation_from_kendall_tau(tau, len(CROPS))
    if family == "student_t":
        return "Student-t", {
            "df": 4,
            "corr": equicorrelation_from_kendall_tau(tau, len(CROPS)),
        }
    if family == "clayton":
        return "Clayton", clayton_theta_from_kendall_tau(tau)
    raise ValueError(f"unsupported family {family}")


def scenarios(
    means: np.ndarray,
    stds: np.ndarray,
    family: str,
    tau: float,
    n: int,
    seed: int,
    *,
    marginal: str = "student_t_df5",
    empirical_samples: np.ndarray | None = None,
) -> tuple[np.ndarray, Dict[str, Any]]:
    copula_type, copula_param = copula_parameters(family, tau)
    if marginal == "student_t_df5":
        marginal_model = {"type": "student_t", "df": 5}
    elif marginal == "gaussian":
        marginal_model = {"type": "normal"}
    elif marginal == "empirical_quantile":
        if empirical_samples is None:
            raise ValueError("empirical marginal requires historical samples")
        marginal_model = {"type": "empirical_quantile", "samples": empirical_samples.tolist()}
    else:
        raise ValueError(f"unsupported marginal {marginal}")
    return generate_profit_scenarios(
        means, stds, int(n), copula_type, copula_param, int(seed),
        crop_names=CROPS, marginal_model=marginal_model,
    )


def solve_expected(scen: np.ndarray, spec: Mapping[str, Any]) -> AllocationResult:
    return solve_expected_profit_allocation(
        scen.mean(axis=0), spec["costs"], spec["total_land"], spec["budget"],
        spec["lower"], spec["upper"], spec["rotation_caps"], CROPS,
        spec["contract_minimums"],
        shared_capacity_constraints=spec["shared_capacity_constraints"],
    )


def solve_minimum(scen: np.ndarray, spec: Mapping[str, Any], alpha: float) -> AllocationResult:
    return solve_minimum_cvar_allocation(
        scen, spec["costs"], spec["total_land"], spec["budget"], alpha,
        spec["lower"], spec["upper"], spec["rotation_caps"], CROPS,
        spec["contract_minimums"],
        shared_capacity_constraints=spec["shared_capacity_constraints"],
    )


def solve_risk(
    scen: np.ndarray,
    spec: Mapping[str, Any],
    alpha: float,
    kappa: float,
    method: str = "highs",
) -> AllocationResult:
    return solve_cvar_allocation(
        scen, spec["costs"], spec["total_land"], spec["budget"], alpha, kappa,
        spec["lower"], spec["upper"], spec["rotation_caps"], CROPS,
        spec["contract_minimums"], solver_method=method,
        shared_capacity_constraints=spec["shared_capacity_constraints"],
    )


def risk_endpoint(
    scen: np.ndarray, spec: Mapping[str, Any], alpha: float, rho: float
) -> tuple[float, AllocationResult, AllocationResult]:
    expected = solve_expected(scen, spec)
    minimum = solve_minimum(scen, spec, alpha)
    if expected.allocation is None or minimum.allocation is None:
        raise RuntimeError("operational endpoints must be feasible")
    expected_losses = -(scen @ expected.allocation)
    _, expected_cvar = _var_cvar(expected_losses, alpha)
    kappa = float(minimum.cvar_loss + rho * (expected_cvar - minimum.cvar_loss))
    return kappa, expected, minimum


def _var_cvar(losses: np.ndarray, alpha: float) -> tuple[float, float]:
    from crop_optimization.evaluation import empirical_var_cvar_losses

    return empirical_var_cvar_losses(losses, alpha)


def reversal_classification(
    allocation: np.ndarray,
    scores: np.ndarray,
    design: Mapping[str, Any],
    *,
    acreage_tolerance: float | None = None,
    near_zero_tolerance: float | None = None,
) -> Dict[str, Any]:
    taxonomy = design["reversal_taxonomy"]
    tolerance = (
        float(taxonomy["acreage_order_tolerance"])
        if acreage_tolerance is None else float(acreage_tolerance)
    )
    zero_tolerance = (
        float(taxonomy["near_zero_tolerance"])
        if near_zero_tolerance is None else float(near_zero_tolerance)
    )
    score_tolerance = float(taxonomy["score_order_tolerance"])
    score_order = np.argsort(-scores)
    inversions = []
    strong_pairs = []
    for left in range(len(CROPS)):
        for right in range(left + 1, len(CROPS)):
            high = int(score_order[left])
            low = int(score_order[right])
            if scores[high] - scores[low] <= score_tolerance:
                continue
            if allocation[high] + tolerance < allocation[low]:
                inversions.append(f"{CROPS[high]}<{CROPS[low]}")
            if (
                allocation[high] <= zero_tolerance
                and allocation[low] > zero_tolerance + tolerance
            ):
                strong_pairs.append(f"{CROPS[high]}=0<{CROPS[low]}")
    top = int(score_order[0])
    lower_ranked = [
        int(index) for index in score_order[1:]
        if scores[top] - scores[int(index)] > score_tolerance
    ]
    complete = bool(lower_ranked) and all(
        allocation[top] + tolerance < allocation[index]
        for index in lower_ranked
    )
    selected_pairwise = bool(inversions)
    selected_strong = bool(strong_pairs)
    return {
        "pairwise_reversal_count": int(len(inversions)),
        "reversed_pairs": ";".join(inversions),
        "selected_pairwise_reversal": selected_pairwise,
        "selected_complete_rank_reversal": complete,
        "selected_strong_reversal": selected_strong,
        "strong_reversal_pairs": ";".join(strong_pairs),
        "classification": (
            "selected_strong_reversal" if selected_strong
            else "selected_complete_rank_reversal" if complete
            else "selected_pairwise_reversal" if selected_pairwise
            else "no_reversal"
        ),
        "top_ranked_crop": CROPS[top],
        "top_ranked_allocation": float(allocation[top]),
        "acreage_order_tolerance": tolerance,
        "near_zero_tolerance": zero_tolerance,
    }


def result_row(
    policy: str,
    result: AllocationResult | Mapping[str, Any],
    scen: np.ndarray,
    spec: Mapping[str, Any],
    scores: np.ndarray,
    alpha: float,
    kappa: float,
    design: Mapping[str, Any],
) -> Dict[str, Any]:
    allocation = (
        result.allocation if isinstance(result, AllocationResult) else result.get("allocation")
    )
    status = result.status if isinstance(result, AllocationResult) else str(result.get("status"))
    row: Dict[str, Any] = {"policy": policy, "status": status}
    if allocation is None:
        return row
    x = np.asarray(allocation, dtype=float)
    row.update(allocation_metrics(
        x, scen, spec["costs"], spec["total_land"], spec["budget"], alpha, kappa,
        CROPS, spec["lower"], spec["upper"], spec["rotation_caps"],
        spec["contract_minimums"], spec["shared_capacity_constraints"],
    ))
    row.update(reversal_classification(x, scores, design))
    row["idle_land"] = float(spec["total_land"] - x.sum())
    row["profit_variance"] = float(np.var(scen @ x, ddof=1))
    row["risk_feasible"] = bool(row["cvar_loss"] <= kappa + 1e-6)
    return row


def policy_comparison(
    scen: np.ndarray,
    spec: Mapping[str, Any],
    scores: np.ndarray,
    design: Mapping[str, Any],
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    alpha = float(design["optimization"]["alpha_primary"])
    rho = float(design["optimization"]["primary_risk_tolerance"])
    kappa, expected, minimum = risk_endpoint(scen, spec, alpha, rho)
    suitability = suitability_proportional_policy(
        scores, spec["total_land"], spec["costs"], spec["budget"], spec["lower"],
        spec["upper"], spec["rotation_caps"], CROPS, spec["contract_minimums"],
        spec["shared_capacity_constraints"],
    )
    winner_target = np.zeros(len(CROPS))
    winner_target[int(np.argmax(scores))] = spec["total_land"]
    winner = repair_allocation_to_feasible(
        winner_target, spec["costs"], spec["total_land"], spec["budget"],
        spec["lower"], spec["upper"], spec["rotation_caps"], CROPS,
        spec["contract_minimums"], spec["shared_capacity_constraints"],
    )
    equal = repair_allocation_to_feasible(
        np.full(len(CROPS), spec["total_land"] / len(CROPS)),
        spec["costs"], spec["total_land"], spec["budget"], spec["lower"],
        spec["upper"], spec["rotation_caps"], CROPS, spec["contract_minimums"],
        spec["shared_capacity_constraints"],
    )
    mean_variance = mean_variance_policy(
        scen, spec["costs"], spec["total_land"], spec["budget"], spec["lower"],
        spec["upper"], spec["rotation_caps"], CROPS, gamma=2e-5,
        start=expected.allocation, contract_minimums=spec["contract_minimums"],
        shared_capacity_constraints=spec["shared_capacity_constraints"],
    )
    cvar = solve_risk(scen, spec, alpha, kappa)
    rows = [
        result_row("suitability_proportional", suitability, scen, spec, scores, alpha, kappa, design),
        result_row("winner_take_all", winner, scen, spec, scores, alpha, kappa, design),
        result_row("equal_share", equal, scen, spec, scores, alpha, kappa, design),
        result_row("expected_profit_no_CVaR", expected, scen, spec, scores, alpha, kappa, design),
        result_row("mean_variance", mean_variance, scen, spec, scores, alpha, kappa, design),
        result_row("full_CVaR_operational", cvar, scen, spec, scores, alpha, kappa, design),
        result_row("minimum_CVaR_endpoint_not_primary", minimum, scen, spec, scores, alpha, kappa, design),
    ]
    for row in rows:
        row.update({"alpha": alpha, "risk_tolerance": rho, "cvar_limit": kappa})
    endpoint = {
        "alpha": alpha,
        "risk_tolerance": rho,
        "minimum_cvar": minimum.cvar_loss,
        "expected_profit_endpoint_cvar": _var_cvar(-(scen @ expected.allocation), alpha)[1],
        "primary_cvar_limit": kappa,
        "primary_result": cvar,
    }
    return pd.DataFrame(rows), endpoint


def active_set(result: AllocationResult) -> str:
    keys = [
        "land_binds", "budget_binds", "cvar_binds", "rotation_binds",
        "contract_binds", "shared_capacity_binds", "lower_bound_binds",
        "upper_bound_binds",
    ]
    return ";".join(key.removesuffix("_binds") for key in keys if result.diagnostics.get(key))


def phase_diagram(
    means: np.ndarray,
    stds: np.ndarray,
    margin_matrix: np.ndarray,
    scores: np.ndarray,
    spec: Mapping[str, Any],
    design: Mapping[str, Any],
) -> pd.DataFrame:
    rows = []
    opt = design["optimization"]
    dep = design["dependence"]
    seed = int(design["uncertainty"]["base_seed"])
    n = int(design["uncertainty"]["optimization_scenarios"])
    for family_index, family in enumerate(dep["families"]):
        for tau_index, tau in enumerate(dep["kendall_tau_grid"]):
            scen, meta = scenarios(
                means, stds, family, float(tau), n,
                seed + 1000 * family_index + 100 * tau_index,
                empirical_samples=margin_matrix,
            )
            for rho in opt["risk_tolerance_grid"]:
                kappa, _expected, _minimum = risk_endpoint(scen, spec, opt["alpha_primary"], rho)
                result = solve_risk(scen, spec, opt["alpha_primary"], kappa)
                row: Dict[str, Any] = {
                    "copula_family": family,
                    "kendall_tau": float(tau),
                    "risk_tolerance": float(rho),
                    "cvar_limit": float(kappa),
                    "lower_tail_dependence": float(meta["lower_tail_dependence"]),
                    "solver_status": result.status,
                    "active_set": active_set(result) if result.allocation is not None else "",
                }
                if result.allocation is None:
                    row["classification"] = "infeasible"
                else:
                    row.update(reversal_classification(result.allocation, scores, design))
                    row["expected_profit"] = result.expected_profit
                    row["cvar_loss"] = result.cvar_loss
                    row["idle_land"] = float(spec["total_land"] - result.allocation.sum())
                    for crop, value in zip(CROPS, result.allocation):
                        row[f"allocation_{crop.replace(' ', '_')}"] = float(value)
                    taxonomy = design["reversal_taxonomy"]
                    face = audit_reversal_optimal_face(
                        scen, spec["costs"], spec["total_land"], spec["budget"],
                        opt["alpha_primary"], kappa, spec["lower"], spec["upper"],
                        CROPS, scores,
                        rotation_caps=spec["rotation_caps"],
                        contract_minimums=spec["contract_minimums"],
                        shared_capacity_constraints=spec["shared_capacity_constraints"],
                        score_tolerance=float(taxonomy["score_order_tolerance"]),
                        allocation_tolerance=float(taxonomy["acreage_order_tolerance"]),
                        near_zero_tolerance=float(taxonomy["near_zero_tolerance"]),
                        primary_result=result,
                    )
                    for key in [
                        "possible_pairwise_reversal",
                        "universal_pairwise_reversal",
                        "possible_complete_rank_reversal",
                        "universal_complete_rank_reversal",
                        "possible_strong_reversal",
                        "universal_strong_reversal",
                        "multiple_optima",
                        "top_min_allocation",
                        "top_max_allocation",
                    ]:
                        row[key] = face.get(key)
                    for pair_name, pair_result in face.get("pair_results", {}).items():
                        for key, value in pair_result.items():
                            row[f"face_{pair_name}_{key}"] = value
                rows.append(row)
    frame = pd.DataFrame(rows)
    frame["active_set_transition"] = (
        frame.sort_values(["copula_family", "kendall_tau", "risk_tolerance"])
        .groupby(["copula_family", "kendall_tau"])["active_set"]
        .transform(lambda values: values.ne(values.shift()).fillna(False))
    )
    return frame


def pseudo_observations(matrix: np.ndarray) -> np.ndarray:
    n = matrix.shape[0]
    return np.column_stack(
        [stats.rankdata(matrix[:, idx], method="average") / (n + 1.0)
         for idx in range(matrix.shape[1])]
    )


def average_pairwise_kendall(matrix: np.ndarray) -> float:
    values = []
    for left in range(matrix.shape[1]):
        for right in range(left + 1, matrix.shape[1]):
            values.append(stats.kendalltau(matrix[:, left], matrix[:, right]).statistic)
    return float(np.nanmean(values))


def copula_loglik(uniforms: np.ndarray, family: str, tau: float) -> float:
    d = uniforms.shape[1]
    if family == "gaussian":
        corr = equicorrelation_from_kendall_tau(max(0.0, tau), d)
        z = stats.norm.ppf(uniforms)
        return float(
            np.sum(stats.multivariate_normal.logpdf(z, mean=np.zeros(d), cov=corr))
            - np.sum(stats.norm.logpdf(z))
        )
    if family == "student_t":
        df = 4.0
        corr = equicorrelation_from_kendall_tau(max(0.0, tau), d)
        z = stats.t.ppf(uniforms, df=df)
        return float(
            np.sum(stats.multivariate_t.logpdf(z, loc=np.zeros(d), shape=corr, df=df))
            - np.sum(stats.t.logpdf(z, df=df))
        )
    theta = clayton_theta_from_kendall_tau(max(0.0, tau))
    if theta <= 1e-10:
        return 0.0
    constant = sum(math.log1p(k * theta) for k in range(1, d))
    summed = np.sum(uniforms ** (-theta), axis=1) - d + 1.0
    log_density = (
        constant
        + (-1.0 - theta) * np.log(uniforms).sum(axis=1)
        + (-d - 1.0 / theta) * np.log(summed)
    )
    return float(np.sum(log_density))


def dependence_diagnostics(
    margin_matrix: np.ndarray, design: Mapping[str, Any]
) -> pd.DataFrame:
    uniforms = pseudo_observations(margin_matrix)
    tau_hat = average_pairwise_kendall(margin_matrix)
    rng = np.random.default_rng(int(design["uncertainty"]["base_seed"]) + 70000)
    boot = []
    for _ in range(2000):
        indices = rng.integers(0, len(margin_matrix), len(margin_matrix))
        value = average_pairwise_kendall(margin_matrix[indices])
        if np.isfinite(value):
            boot.append(value)
    tau_low, tau_high = np.quantile(boot, [0.025, 0.975])
    empirical_joint_lower_quartile = float(np.mean(np.all(uniforms <= 0.25, axis=1)))
    rows = []
    for family in design["dependence"]["families"]:
        fitted_tau = float(np.clip(tau_hat, 0.0, 0.95))
        _copula_type, parameter = copula_parameters(family, fitted_tau)
        if family == "student_t":
            from crop_simulation.copula_models import lower_tail_dependence

            tail = lower_tail_dependence("Student-t", parameter)
        elif family == "clayton":
            from crop_simulation.copula_models import lower_tail_dependence

            tail = lower_tail_dependence("Clayton", parameter)
        else:
            tail = 0.0
        loglik = copula_loglik(uniforms, family, fitted_tau)
        rows.append({
            "copula_family": family,
            "raw_effective_sample_size": int(len(margin_matrix)),
            "estimated_average_pairwise_kendall_tau": tau_hat,
            "kendall_tau_bootstrap_low": float(tau_low),
            "kendall_tau_bootstrap_high": float(tau_high),
            "family_parameter": json.dumps(jsonable(parameter), sort_keys=True),
            "fixed_student_t_df": 4 if family == "student_t" else np.nan,
            "copula_log_likelihood": loglik,
            "aic": float(2.0 - 2.0 * loglik),
            "theoretical_lower_tail_dependence": float(tail),
            "empirical_joint_lower_quartile_frequency": empirical_joint_lower_quartile,
            "goodness_of_fit_scope": "AIC_DESCRIPTIVE_ONLY_N_EQUALS_8",
            "tail_fit_scope": "LOW_POWER_QUARTILE_DIAGNOSTIC_NOT_EXTREME_TAIL_ESTIMATION",
            "model_use": "REGISTERED_STRESS_PATH_NOT_FARM_LEVEL_ESTIMATE",
        })
    return pd.DataFrame(rows).sort_values("aic")


def diversification_failure(
    means: np.ndarray,
    stds: np.ndarray,
    margin_matrix: np.ndarray,
    scores: np.ndarray,
    spec: Mapping[str, Any],
    design: Mapping[str, Any],
) -> pd.DataFrame:
    tau = float(design["dependence"]["primary_kendall_tau"])
    seed = int(design["uncertainty"]["base_seed"]) + 80000
    n = int(design["uncertainty"]["evaluation_scenarios"])
    registered = design["diversification_failure"]
    gaussian, _ = scenarios(
        means, stds, "gaussian", tau, n, seed, empirical_samples=margin_matrix
    )
    tail, tail_meta = scenarios(
        means, stds, "student_t", tau, n, seed, empirical_samples=margin_matrix
    )
    alpha = float(design["optimization"]["alpha_primary"])
    kappa, expected_tail, _minimum_tail = risk_endpoint(
        tail, spec, alpha, design["optimization"]["primary_risk_tolerance"]
    )
    benchmark = solve_expected(gaussian, spec)
    if benchmark.allocation is None:
        raise RuntimeError("declared diversification benchmark is infeasible")
    frontier: Dict[float, np.ndarray] = {}
    start = np.asarray(benchmark.allocation)
    for gamma_value in registered["gamma_grid"]:
        gamma = float(gamma_value)
        point = mean_variance_policy(
            gaussian, spec["costs"], spec["total_land"], spec["budget"], spec["lower"],
            spec["upper"], spec["rotation_caps"], CROPS, gamma=gamma,
            start=start,
            contract_minimums=spec["contract_minimums"],
            shared_capacity_constraints=spec["shared_capacity_constraints"],
            full_investment=bool(registered["mean_variance_full_investment"]),
        )
        if point["status"] != "optimal":
            raise RuntimeError(f"Gaussian mean-variance frontier failed at gamma={gamma}")
        start = np.asarray(point["allocation"], dtype=float)
        frontier[gamma] = start
    selected_gamma = float(registered["selected_gamma"])
    if selected_gamma not in frontier:
        raise ValueError("selected mean-variance gamma is absent from registered grid")
    mean_variance_allocation = frontier[selected_gamma]
    tail_aware = solve_risk(tail, spec, alpha, kappa)
    if tail_aware.allocation is None:
        raise RuntimeError("tail-aware diversification comparison is infeasible")
    candidates = {
        "x0_expected_profit_under_matched_gaussian": np.asarray(benchmark.allocation),
        "xMV_registered_Gaussian_frontier_point": mean_variance_allocation,
        "xT_CVaR_under_matched_student_t": np.asarray(tail_aware.allocation),
        "expected_profit_under_tail_law_diagnostic": np.asarray(expected_tail.allocation),
    }
    rows = []
    for policy, x in candidates.items():
        tail_profit = tail @ x
        gaussian_profit = gaussian @ x
        _, tail_cvar = _var_cvar(-tail_profit, alpha)
        rows.append({
            "policy": policy,
            "row_type": "registered_policy",
            "gamma": selected_gamma if policy.startswith("xMV_") else np.nan,
            "declared_benchmark": policy.startswith("x0_"),
            "matched_kendall_tau": tau,
            "true_law": "student_t_df4_copula",
            "gaussian_lower_tail_dependence": 0.0,
            "lower_tail_dependence": tail_meta["lower_tail_dependence"],
            "gaussian_profit_variance": float(np.var(gaussian_profit, ddof=1)),
            "gaussian_expected_profit": float(np.mean(gaussian_profit)),
            "true_law_profit_variance": float(np.var(tail_profit, ddof=1)),
            "true_law_loss_CVaR": float(tail_cvar),
            "true_law_expected_profit": float(np.mean(tail_profit)),
            "risk_ceiling": kappa,
            **{f"allocation_{crop.replace(' ', '_')}": float(value)
               for crop, value in zip(CROPS, x)},
            **reversal_classification(x, scores, design),
        })
    for gamma, x in frontier.items():
        gaussian_profit = gaussian @ x
        tail_profit = tail @ x
        _, tail_cvar = _var_cvar(-tail_profit, alpha)
        rows.append({
            "policy": f"Gaussian_MV_frontier_gamma_{gamma:.4f}",
            "row_type": "mean_variance_frontier",
            "gamma": gamma,
            "declared_benchmark": False,
            "matched_kendall_tau": tau,
            "true_law": "student_t_df4_copula",
            "gaussian_lower_tail_dependence": 0.0,
            "lower_tail_dependence": tail_meta["lower_tail_dependence"],
            "gaussian_profit_variance": float(np.var(gaussian_profit, ddof=1)),
            "gaussian_expected_profit": float(np.mean(gaussian_profit)),
            "true_law_profit_variance": float(np.var(tail_profit, ddof=1)),
            "true_law_loss_CVaR": float(tail_cvar),
            "true_law_expected_profit": float(np.mean(tail_profit)),
            "risk_ceiling": kappa,
            **{f"allocation_{crop.replace(' ', '_')}": float(value)
               for crop, value in zip(CROPS, x)},
            **reversal_classification(x, scores, design),
        })
    frame = pd.DataFrame(rows)
    x0 = frame.loc[
        frame["policy"].eq("x0_expected_profit_under_matched_gaussian")
    ].iloc[0]
    mv = frame.loc[
        frame["policy"].eq("xMV_registered_Gaussian_frontier_point")
    ].iloc[0]
    cv = frame.loc[
        frame["policy"].eq("xT_CVaR_under_matched_student_t")
    ].iloc[0]
    variance_tolerance = float(registered["variance_tolerance"])
    cvar_tolerance = float(registered["cvar_tolerance"])
    allocation_threshold = float(registered["allocation_materiality_l1"])
    variance_diversifies = bool(
        mv["gaussian_profit_variance"]
        < x0["gaussian_profit_variance"] - variance_tolerance
    )
    cvar_fails = bool(
        mv["true_law_loss_CVaR"] > cv["true_law_loss_CVaR"] + cvar_tolerance
    )
    allocation_l1 = float(sum(
        abs(mv[f"allocation_{crop.replace(' ', '_')}"]
            - cv[f"allocation_{crop.replace(' ', '_')}"])
        for crop in CROPS
    ))
    allocation_disagrees = bool(allocation_l1 > allocation_threshold)
    strong_failure = bool(
        variance_diversifies
        and cvar_fails
        and allocation_disagrees
        and mv["true_law_loss_CVaR"] > kappa + cvar_tolerance
    )
    frame["variance_diversification_criterion"] = variance_diversifies
    frame["tail_CVaR_failure_criterion"] = cvar_fails
    frame["allocation_disagreement_criterion"] = allocation_disagrees
    frame["strong_risk_ceiling_violation_criterion"] = bool(
        mv["true_law_loss_CVaR"] > kappa + cvar_tolerance
    )
    frame["benchmark_gaussian_variance"] = float(x0["gaussian_profit_variance"])
    frame["selected_xMV_gaussian_variance"] = float(mv["gaussian_profit_variance"])
    frame["gaussian_variance_reduction"] = float(
        x0["gaussian_profit_variance"] - mv["gaussian_profit_variance"]
    )
    frame["gaussian_variance_reduction_fraction"] = float(
        1.0 - mv["gaussian_profit_variance"] / x0["gaussian_profit_variance"]
    )
    frame["xMV_vs_xT_allocation_L1"] = allocation_l1
    frame["xMV_true_law_CVaR_minus_xT"] = float(
        mv["true_law_loss_CVaR"] - cv["true_law_loss_CVaR"]
    )
    frame["diversification_failure_identified"] = (
        variance_diversifies and cvar_fails and allocation_disagrees
    )
    frame["strong_diversification_failure_identified"] = strong_failure
    frame["criterion_definition"] = (
        "xMV must reduce Gaussian variance relative to declared x0, differ "
        "materially from xT, and have worse Student-t-law loss-CVaR; strong "
        "failure additionally requires violation of the true-law ceiling"
    )
    return frame


def margin_mechanism(
    calibration: pd.DataFrame,
    calibration_summary: pd.DataFrame,
    policies: pd.DataFrame,
) -> pd.DataFrame:
    """Record the official-data score--margin mechanism without causal overreach."""

    expected = policies.loc[
        policies["policy"].eq("expected_profit_no_CVaR")
    ].iloc[0]
    full = policies.loc[policies["policy"].eq("full_CVaR_operational")].iloc[0]
    rows = []
    ranked = calibration_summary.copy()
    ranked["score_rank"] = ranked[
        "historical_yield_potential_score"
    ].rank(method="min", ascending=False).astype(int)
    ranked["mean_margin_rank"] = ranked[
        "mean_margin_real_2024_usd_per_acre"
    ].rank(method="min", ascending=False).astype(int)
    for _, crop_row in ranked.iterrows():
        crop = str(crop_row["crop"])
        rows.append({
            "mechanism": "margin_induced",
            "crop": crop,
            "score": crop_row["historical_yield_potential_score"],
            "score_rank": crop_row["score_rank"],
            "mean_margin_real_2024_usd_per_acre": crop_row[
                "mean_margin_real_2024_usd_per_acre"
            ],
            "mean_margin_rank": crop_row["mean_margin_rank"],
            "expected_profit_endpoint_allocation": expected[f"acres_{crop}"],
            "full_CVaR_allocation": full[f"acres_{crop}"],
            "risk_adjustment_to_allocation": (
                full[f"acres_{crop}"] - expected[f"acres_{crop}"]
            ),
            "raw_effective_years": int(calibration["year"].nunique()),
            "interpretation": (
                "OFFICIAL_DATA_SCORE_MARGIN_SEPARATION;"
                "RISK_MODERATES_PRIMARY_TOP_CROP_INVERSION"
            ),
        })
    return pd.DataFrame(rows).sort_values("score_rank")


def risk_induced_mechanism(
    calibration: pd.DataFrame,
    means: np.ndarray,
    stds: np.ndarray,
    margin_matrix: np.ndarray,
    scores: np.ndarray,
    spec: Mapping[str, Any],
    design: Mapping[str, Any],
) -> pd.DataFrame:
    """Registered mean-preserving downside stress for a genuine risk crossing."""

    registered = design["mechanism_isolation"]["risk_induced"]
    scenario_count = int(registered["scenario_count"])
    scen, meta = scenarios(
        means,
        stds,
        str(registered["scenario_family"]),
        float(registered["kendall_tau"]),
        scenario_count,
        int(registered["scenario_seed"]),
        marginal=str(registered["marginal_family"]),
        empirical_samples=margin_matrix,
    )
    high_crop = str(registered["focal_high_rank_crop"])
    low_crop = str(registered["focal_low_rank_crop"])
    high = CROPS.index(high_crop)
    low = CROPS.index(low_crop)
    gross = calibration.assign(
        real_gross_revenue=(
            calibration["yield_bushels_per_acre"]
            * calibration["harvest_price_usd_per_bushel"]
            * calibration["cpi_u_deflator_to_2024"]
        )
    )
    mean_gross = float(
        gross.loc[gross["crop"].eq(high_crop), "real_gross_revenue"].mean()
    )
    shock = (
        mean_gross
        * float(registered["soybean_downside_shock_share_of_mean_real_gross_revenue"])
    )
    event_count = int(round(
        float(registered["soybean_adverse_event_probability"]) * scenario_count
    ))
    rng = np.random.default_rng(int(registered["adverse_event_seed"]))
    adverse = np.zeros(scenario_count, dtype=bool)
    adverse[rng.permutation(scenario_count)[:event_count]] = True
    compensation = shock * event_count / (scenario_count - event_count)
    stressed = scen.copy()
    stressed[adverse, high] -= shock
    stressed[~adverse, high] += compensation
    mean_before = scen.mean(axis=0)
    mean_after = stressed.mean(axis=0)
    if not np.isclose(mean_before[high], mean_after[high], atol=1e-10):
        raise AssertionError("registered downside stress must preserve the finite-sample mean")
    if not (
        scores[high] > scores[low]
        and mean_after[high] > mean_after[low]
    ):
        raise AssertionError("risk mechanism requires higher score and higher mean")

    alpha = float(design["optimization"]["alpha_primary"])
    rows = []
    for rho_value in registered["risk_tolerance_grid"]:
        rho = float(rho_value)
        kappa, expected, minimum = risk_endpoint(stressed, spec, alpha, rho)
        result = solve_risk(stressed, spec, alpha, kappa)
        if result.allocation is None:
            rows.append({
                "mechanism": "risk_induced",
                "risk_tolerance": rho,
                "solver_status": "infeasible",
            })
            continue
        row = {
            "mechanism": "risk_induced",
            "focal_high_rank_crop": high_crop,
            "focal_low_rank_crop": low_crop,
            "score_high": float(scores[high]),
            "score_low": float(scores[low]),
            "mean_margin_high": float(mean_after[high]),
            "mean_margin_low": float(mean_after[low]),
            "mean_margin_gap_high_minus_low": float(
                mean_after[high] - mean_after[low]
            ),
            "official_mean_margin_high": float(means[high]),
            "official_mean_margin_low": float(means[low]),
            "official_mean_margin_gap_high_minus_low": float(
                means[high] - means[low]
            ),
            "mean_preservation_error": float(mean_after[high] - mean_before[high]),
            "adverse_event_probability_realized": event_count / scenario_count,
            "downside_shock_real_2024_usd_per_acre": shock,
            "nonadverse_compensation_real_2024_usd_per_acre": compensation,
            "risk_tolerance": rho,
            "alpha": alpha,
            "cvar_limit": kappa,
            "minimum_cvar": minimum.cvar_loss,
            "expected_endpoint_cvar": _var_cvar(
                -(stressed @ expected.allocation), alpha
            )[1],
            "allocation_high": float(result.allocation[high]),
            "allocation_low": float(result.allocation[low]),
            "allocation_high_minus_low": float(
                result.allocation[high] - result.allocation[low]
            ),
            "selected_focal_pair_reversal": bool(
                result.allocation[high]
                + float(design["reversal_taxonomy"]["acreage_order_tolerance"])
                < result.allocation[low]
            ),
            "expected_profit": result.expected_profit,
            "cvar_loss": result.cvar_loss,
            "active_set": active_set(result),
            "solver_status": result.status,
            "scenario_family": registered["scenario_family"],
            "kendall_tau": registered["kendall_tau"],
            "lower_tail_dependence": meta["lower_tail_dependence"],
            "evidence_class": "REGISTERED_CONTROLLED_STRUCTURAL_STRESS_TEST",
            **{
                f"allocation_{crop.replace(' ', '_')}": float(value)
                for crop, value in zip(CROPS, result.allocation)
            },
            **reversal_classification(result.allocation, scores, design),
        }
        rows.append(row)
    frame = pd.DataFrame(rows).sort_values("risk_tolerance")
    loose = frame.iloc[-1]
    tight = frame.iloc[0]
    crossing = bool(
        loose["allocation_high_minus_low"]
        > float(design["reversal_taxonomy"]["acreage_order_tolerance"])
        and tight["allocation_high_minus_low"]
        < -float(design["reversal_taxonomy"]["acreage_order_tolerance"])
    )
    frame["registered_loose_to_tight_crossing"] = crossing
    return frame


def operational_mechanism(
    means: np.ndarray,
    stds: np.ndarray,
    margin_matrix: np.ndarray,
    scores: np.ndarray,
    spec: Mapping[str, Any],
    design: Mapping[str, Any],
) -> pd.DataFrame:
    """Hold the margin/risk law fixed and vary only operational restrictions."""

    registered = design["mechanism_isolation"]["operational"]
    scen, _meta = scenarios(
        means,
        stds,
        str(registered["scenario_family"]),
        float(registered["kendall_tau"]),
        int(registered["scenario_count"]),
        int(registered["scenario_seed"]),
        empirical_samples=margin_matrix,
    )
    alpha = float(design["optimization"]["alpha_primary"])
    # This ceiling exceeds the worst single-crop scenario loss and is
    # therefore nonbinding for every nonnegative allocation with land <= 1.
    nonbinding_kappa = float(max(0.0, -float(scen.min())) + 1.0)
    high_crop = str(registered["focal_high_rank_crop"])
    low_crop = str(registered["focal_low_rank_crop"])
    high = CROPS.index(high_crop)
    low = CROPS.index(low_crop)
    base = dict(spec)
    base["lower"] = np.zeros(len(CROPS))
    base["upper"] = np.full(len(CROPS), spec["total_land"])
    base["budget"] = 1e12
    base["rotation_caps"] = {}
    base["contract_minimums"] = {}
    base["shared_capacity_constraints"] = {}
    stages: list[tuple[str, Dict[str, Any]]] = [("land_only", copy.deepcopy(base))]
    staged = copy.deepcopy(base)
    staged["lower"] = np.asarray(spec["lower"]).copy()
    staged["upper"] = np.asarray(spec["upper"]).copy()
    stages.append(("crop_bounds", copy.deepcopy(staged)))
    staged["budget"] = spec["budget"]
    stages.append(("budget", copy.deepcopy(staged)))
    staged["rotation_caps"] = dict(spec["rotation_caps"])
    stages.append(("corn_rotation", copy.deepcopy(staged)))
    staged["contract_minimums"] = dict(spec["contract_minimums"])
    stages.append(("soybean_contract", copy.deepcopy(staged)))
    for capacity_name in ("planting_labour", "harvest_equipment"):
        staged["shared_capacity_constraints"] = dict(
            staged["shared_capacity_constraints"]
        )
        staged["shared_capacity_constraints"][capacity_name] = copy.deepcopy(
            spec["shared_capacity_constraints"][capacity_name]
        )
        stages.append((capacity_name, copy.deepcopy(staged)))

    rows = []

    def append_result(
        path: str,
        stage_index: int,
        stage_name: str,
        stage_spec: Mapping[str, Any],
        soybean_cap: float | None = None,
    ) -> None:
        result = solve_risk(scen, stage_spec, alpha, nonbinding_kappa)
        row: Dict[str, Any] = {
            "mechanism": "operational",
            "operational_path": path,
            "stage_index": stage_index,
            "stage": stage_name,
            "soybean_rotation_cap": soybean_cap,
            "fixed_risk_ceiling": nonbinding_kappa,
            "risk_ceiling_declared_nonbinding": True,
            "focal_high_rank_crop": high_crop,
            "focal_low_rank_crop": low_crop,
            "score_high": float(scores[high]),
            "score_low": float(scores[low]),
            "mean_margin_high": float(scen.mean(axis=0)[high]),
            "mean_margin_low": float(scen.mean(axis=0)[low]),
            "solver_status": result.status,
            "evidence_class": "REGISTERED_CONTROLLED_OPERATIONAL_STRESS_TEST",
        }
        if result.allocation is not None:
            row.update({
                "allocation_high": float(result.allocation[high]),
                "allocation_low": float(result.allocation[low]),
                "allocation_high_minus_low": float(
                    result.allocation[high] - result.allocation[low]
                ),
                "selected_focal_pair_reversal": bool(
                    result.allocation[high]
                    + float(design["reversal_taxonomy"]["acreage_order_tolerance"])
                    < result.allocation[low]
                ),
                "expected_profit": result.expected_profit,
                "cvar_loss": result.cvar_loss,
                "cvar_slack": nonbinding_kappa - float(result.cvar_loss),
                "active_set": active_set(result),
                **{
                    f"allocation_{crop.replace(' ', '_')}": float(value)
                    for crop, value in zip(CROPS, result.allocation)
                },
                **reversal_classification(result.allocation, scores, design),
            })
        rows.append(row)

    for stage_index, (stage_name, stage_spec) in enumerate(stages):
        append_result(
            "registered_constraint_sequence", stage_index, stage_name, stage_spec
        )
    full_spec = copy.deepcopy(staged)
    for cap_index, cap_value in enumerate(registered["soybean_rotation_cap_grid"]):
        cap = float(cap_value)
        cap_spec = copy.deepcopy(full_spec)
        cap_spec["rotation_caps"]["Soybean"] = cap
        append_result(
            "soybean_rotation_tightening",
            cap_index,
            f"soybean_rotation_cap_{cap:.2f}",
            cap_spec,
            cap,
        )
    frame = pd.DataFrame(rows)
    rotation = frame.loc[
        frame["operational_path"].eq("soybean_rotation_tightening")
    ].sort_values("stage_index")
    crossing_rows = rotation.loc[
        rotation["selected_focal_pair_reversal"].fillna(False)
    ]
    frame["first_operational_crossing_cap"] = (
        float(crossing_rows["soybean_rotation_cap"].max())
        if len(crossing_rows) else np.nan
    )
    return frame


def reversal_tolerance_sensitivity(
    phase: pd.DataFrame,
    robustness: pd.DataFrame,
    bootstrap: pd.DataFrame,
    scores: np.ndarray,
    design: Mapping[str, Any],
) -> pd.DataFrame:
    """Reclassify every selected allocation at the registered tolerance grid."""

    rows = []
    datasets = {
        "phase_165_cells": phase,
        "robustness": robustness,
        "historical_bootstrap": bootstrap,
    }
    allocation_columns = [
        f"allocation_{crop.replace(' ', '_')}" for crop in CROPS
    ]
    for tolerance_value in design["reversal_taxonomy"]["tolerance_sensitivity"]:
        tolerance = float(tolerance_value)
        for dataset_name, frame in datasets.items():
            classifications = []
            for _, row in frame.dropna(subset=allocation_columns).iterrows():
                allocation = row[allocation_columns].to_numpy(float)
                row_scores = scores
                score_columns = [
                    f"score_{crop.replace(' ', '_')}" for crop in CROPS
                ]
                if all(column in row.index for column in score_columns):
                    row_scores = row[score_columns].to_numpy(float)
                classifications.append(
                    reversal_classification(
                        allocation,
                        row_scores,
                        design,
                        acreage_tolerance=tolerance,
                        near_zero_tolerance=tolerance,
                    )
                )
            rows.append({
                "dataset": dataset_name,
                "tolerance": tolerance,
                "classified_rows": len(classifications),
                "selected_pairwise_reversal_count": sum(
                    bool(item["selected_pairwise_reversal"])
                    for item in classifications
                ),
                "selected_complete_rank_reversal_count": sum(
                    bool(item["selected_complete_rank_reversal"])
                    for item in classifications
                ),
                "selected_strong_reversal_count": sum(
                    bool(item["selected_strong_reversal"])
                    for item in classifications
                ),
            })
    return pd.DataFrame(rows)


def robustness_cases(
    means: np.ndarray,
    stds: np.ndarray,
    margin_matrix: np.ndarray,
    scores: np.ndarray,
    spec: Mapping[str, Any],
    design: Mapping[str, Any],
) -> pd.DataFrame:
    base = {
        "alpha": float(design["optimization"]["alpha_primary"]),
        "family": design["dependence"]["primary_family"],
        "tau": float(design["dependence"]["primary_kendall_tau"]),
        "marginal": design["profit"]["marginal_primary"],
        "n": int(design["uncertainty"]["optimization_scenarios"]),
        "seed": int(design["uncertainty"]["base_seed"]),
        "window_start": 2016,
        "solver": "highs",
        "constraint_regime": "full",
    }
    cases: list[tuple[str, str, Any]] = [("baseline", "baseline", "baseline")]
    cases += [("alpha", "alpha", value) for value in design["optimization"]["alpha_grid"]]
    cases += [("dependence_family", "family", value) for value in design["dependence"]["families"]]
    cases += [("dependence_parameter", "tau", value) for value in design["dependence"]["kendall_tau_grid"]]
    cases += [("marginal", "marginal", value) for value in design["profit"]["marginal_sensitivity"]]
    cases += [("scenario_count", "n", value) for value in design["robustness"]["scenario_counts"]]
    cases += [("seed", "seed", value) for value in design["robustness"]["seeds"]]
    cases += [("solver", "solver", value) for value in design["robustness"]["solver_methods"]]
    cases += [("sample_window", "window_start", value[0]) for value in design["robustness"]["sample_windows"]]
    cases += [("constraint", "constraint_regime", value) for value in design["robustness"]["constraints"]]
    rows = []
    for index, (dimension, field, value) in enumerate(cases):
        settings = dict(base)
        if field != "baseline":
            settings[field] = value
        subset = margin_matrix[settings["window_start"] - 2016:]
        case_means = subset.mean(axis=0)
        case_stds = subset.std(axis=0, ddof=1)
        case_spec = dict(spec)
        case_spec["rotation_caps"] = dict(spec["rotation_caps"])
        case_spec["contract_minimums"] = dict(spec["contract_minimums"])
        case_spec["shared_capacity_constraints"] = dict(spec["shared_capacity_constraints"])
        regime = settings["constraint_regime"]
        if regime == "no_budget":
            case_spec["budget"] = 1e9
        elif regime == "no_rotation":
            case_spec["rotation_caps"] = {}
        elif regime == "no_contract":
            case_spec["contract_minimums"] = {}
        elif regime == "no_shared_capacity":
            case_spec["shared_capacity_constraints"] = {}
        scen, _meta = scenarios(
            case_means, case_stds, settings["family"], float(settings["tau"]),
            int(settings["n"]), int(settings["seed"]) + index,
            marginal=settings["marginal"], empirical_samples=subset,
        )
        kappa, _expected, _minimum = risk_endpoint(
            scen, case_spec, settings["alpha"],
            design["optimization"]["primary_risk_tolerance"],
        )
        result = solve_risk(
            scen, case_spec, settings["alpha"], kappa, method=settings["solver"]
        )
        row: Dict[str, Any] = {
            "dimension": dimension,
            "setting": str(value),
            **settings,
            "solver_status": result.status,
            "cvar_limit": kappa,
        }
        if result.allocation is not None:
            row.update(reversal_classification(result.allocation, scores, design))
            row.update({
                "expected_profit": result.expected_profit,
                "cvar_loss": result.cvar_loss,
                "active_set": active_set(result),
                "kkt_primal_residual": result.diagnostics.get("kkt_primal_residual"),
                "kkt_stationarity_residual": result.diagnostics.get("kkt_stationarity_residual"),
            })
            for crop, amount in zip(CROPS, result.allocation):
                row[f"allocation_{crop.replace(' ', '_')}"] = float(amount)
        rows.append(row)
    return pd.DataFrame(rows)


def bootstrap_uncertainty(
    calibration: pd.DataFrame,
    spec: Mapping[str, Any],
    design: Mapping[str, Any],
) -> pd.DataFrame:
    margin_col = "standardized_operating_margin_real_2024_usd_per_acre"
    years = sorted(calibration["year"].unique())
    rng = np.random.default_rng(int(design["uncertainty"]["base_seed"]) + 90000)
    rows = []
    replications = int(design["uncertainty"]["historical_bootstrap_replications"])
    n_scenarios = int(design["uncertainty"]["optimization_scenarios"])
    tau = float(design["dependence"]["primary_kendall_tau"])
    alpha = float(design["optimization"]["alpha_primary"])
    for replication in range(replications):
        sampled_years = rng.choice(years, size=len(years), replace=True)
        sampled_parts = []
        for draw, year in enumerate(sampled_years):
            part = calibration.loc[calibration["year"].eq(year)].copy()
            part["bootstrap_draw"] = draw
            sampled_parts.append(part)
        sample = pd.concat(sampled_parts, ignore_index=True)
        margin_matrix = (
            sample.pivot(index="bootstrap_draw", columns="crop", values=margin_col)[CROPS]
            .sort_index()
            .to_numpy()
        )
        means = margin_matrix.mean(axis=0)
        stds = margin_matrix.std(axis=0, ddof=1)
        score_series = sample.groupby("crop")["relative_yield"].mean()
        scores = score_series.reindex(CROPS).to_numpy(float)
        scen, _meta = scenarios(
            means, stds, "student_t", tau, n_scenarios,
            int(design["uncertainty"]["base_seed"]) + 100000 + replication,
            empirical_samples=margin_matrix,
        )
        endpoint_cache = {}
        first_reversal = np.nan
        primary_result = None
        for rho in design["optimization"]["risk_tolerance_grid"]:
            kappa, _expected, _minimum = risk_endpoint(scen, spec, alpha, float(rho))
            result = solve_risk(scen, spec, alpha, kappa)
            endpoint_cache[float(rho)] = (kappa, result)
            if result.allocation is not None:
                reversal = reversal_classification(result.allocation, scores, design)
                if (
                    reversal["selected_pairwise_reversal"]
                    and not np.isfinite(first_reversal)
                ):
                    first_reversal = float(rho)
            if np.isclose(rho, design["optimization"]["primary_risk_tolerance"]):
                primary_result = result
        if primary_result is None or primary_result.allocation is None:
            rows.append({
                "bootstrap_replication": replication,
                "solver_status": "infeasible",
                "first_reversal_risk_tolerance": first_reversal,
            })
            continue
        primary_classification = reversal_classification(
            primary_result.allocation, scores, design
        )
        row = {
            "bootstrap_replication": replication,
            "solver_status": primary_result.status,
            "first_reversal_risk_tolerance": first_reversal,
            "expected_profit": primary_result.expected_profit,
            "cvar_loss": primary_result.cvar_loss,
            **primary_classification,
        }
        for crop, amount, score in zip(CROPS, primary_result.allocation, scores):
            key = crop.replace(" ", "_")
            row[f"allocation_{key}"] = float(amount)
            row[f"score_{key}"] = float(score)
        rows.append(row)
    return pd.DataFrame(rows)


def conditional_state_scenarios(
    calibration: pd.DataFrame,
    design: Mapping[str, Any],
) -> tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    margin_col = "standardized_operating_margin_real_2024_usd_per_acre"
    relative_yield = calibration.pivot(
        index="year", columns="crop", values="relative_yield"
    )[CROPS].sort_index()
    yield_state = relative_yield["Corn"] - relative_yield["Soybean"]
    cutoff = float(yield_state.median())
    low_years = yield_state.loc[yield_state <= cutoff].index
    high_years = yield_state.loc[yield_state > cutoff].index
    pivot = calibration.pivot(index="year", columns="crop", values=margin_col)[CROPS]
    state_scenarios = []
    metadata = {
        "state_definition": (
            "annual Kansas corn-minus-soybean relative-yield advantage "
            "below/above its 2016--2023 median"
        ),
        "cutoff": cutoff,
        "low_years": ";".join(map(str, low_years)),
        "high_years": ";".join(map(str, high_years)),
        "low_year_count": int(len(low_years)),
        "high_year_count": int(len(high_years)),
    }
    for state_index, years in enumerate((low_years, high_years)):
        matrix = pivot.loc[years].to_numpy()
        state_scen, _meta = scenarios(
            matrix.mean(axis=0), matrix.std(axis=0, ddof=1),
            "student_t", float(design["dependence"]["primary_kendall_tau"]),
            int(design["uncertainty"]["optimization_scenarios"]),
            int(design["uncertainty"]["base_seed"]) + 120000 + state_index,
            empirical_samples=matrix,
        )
        state_scenarios.append(state_scen)
    return state_scenarios[0], state_scenarios[1], metadata


def posterior_mixture(
    low: np.ndarray, high: np.ndarray, probability_high: float, seed: int
) -> np.ndarray:
    n = len(low)
    n_high = int(round(float(probability_high) * n))
    n_low = n - n_high
    rng = np.random.default_rng(seed)
    low_indices = rng.choice(len(low), n_low, replace=n_low > len(low))
    high_indices = rng.choice(len(high), n_high, replace=n_high > len(high))
    combined = np.vstack([low[low_indices], high[high_indices]])
    rng.shuffle(combined, axis=0)
    return combined


def symmetric_signal_mixtures(
    low: np.ndarray, high: np.ndarray, accuracy: float, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """Build two posterior samples whose union exactly equals the prior sample."""

    if len(low) != len(high):
        raise ValueError("symmetric signal construction requires equal state samples")
    n = len(low)
    rng = np.random.default_rng(seed)
    low_order = rng.permutation(n)
    high_order = rng.permutation(n)
    if np.isclose(accuracy, 0.5):
        prior = np.vstack([low, high])
        rng.shuffle(prior, axis=0)
        return prior.copy(), prior.copy()
    high_in_high_signal = int(round(float(accuracy) * n))
    high_in_low_signal = n - high_in_high_signal
    low_in_low_signal = high_in_high_signal
    low_signal = np.vstack([
        low[low_order[:low_in_low_signal]],
        high[high_order[:high_in_low_signal]],
    ])
    high_signal = np.vstack([
        low[low_order[low_in_low_signal:]],
        high[high_order[high_in_low_signal:]],
    ])
    rng.shuffle(low_signal, axis=0)
    rng.shuffle(high_signal, axis=0)
    return low_signal, high_signal


def solve_signal_contingent(
    signal_scenarios: tuple[np.ndarray, np.ndarray],
    spec: Mapping[str, Any],
    alpha: float,
    kappa: float,
) -> Dict[str, Any]:
    """Solve a two-signal acreage-recourse LP with one ex-ante CVaR ceiling."""

    first, second = signal_scenarios
    if first.shape != second.shape or first.shape[1] != len(CROPS):
        raise ValueError("signal scenario blocks must have equal S x crop shape")
    scenarios_per_signal = first.shape[0]
    n_crops = len(CROPS)
    total_scenarios = 2 * scenarios_per_signal
    x_size = 2 * n_crops
    v_idx = x_size
    q_start = x_size + 1
    n_vars = x_size + 1 + total_scenarios
    operational_rows_per_signal = (
        2
        + len(spec["rotation_caps"])
        + len(spec["contract_minimums"])
        + len(spec["shared_capacity_constraints"])
    )
    n_rows = 2 * operational_rows_per_signal + 1 + total_scenarios
    matrix = lil_matrix((n_rows, n_vars), dtype=float)
    rhs = np.zeros(n_rows)
    row = 0
    for signal_index in range(2):
        offset = signal_index * n_crops
        matrix[row, offset:offset + n_crops] = 1.0
        rhs[row] = spec["total_land"]
        row += 1
        matrix[row, offset:offset + n_crops] = spec["costs"]
        rhs[row] = spec["budget"]
        row += 1
        for crop, cap in spec["rotation_caps"].items():
            matrix[row, offset + CROPS.index(crop)] = 1.0
            rhs[row] = cap
            row += 1
        for crop, minimum in spec["contract_minimums"].items():
            matrix[row, offset + CROPS.index(crop)] = -1.0
            rhs[row] = -minimum
            row += 1
        for shared in spec["shared_capacity_constraints"].values():
            raw = shared["coefficients"]
            coefficients = np.asarray([raw[crop] for crop in CROPS], dtype=float)
            matrix[row, offset:offset + n_crops] = coefficients
            rhs[row] = shared["capacity"]
            row += 1
    matrix[row, v_idx] = 1.0
    matrix[row, q_start:] = 1.0 / ((1.0 - alpha) * total_scenarios)
    rhs[row] = kappa
    row += 1
    for signal_index, block in enumerate((first, second)):
        offset = signal_index * n_crops
        for scenario_index, scenario in enumerate(block):
            global_scenario = signal_index * scenarios_per_signal + scenario_index
            matrix[row, offset:offset + n_crops] = -scenario
            matrix[row, v_idx] = -1.0
            matrix[row, q_start + global_scenario] = -1.0
            row += 1
    objective = np.zeros(n_vars)
    objective[:n_crops] = -0.5 * first.mean(axis=0)
    objective[n_crops:x_size] = -0.5 * second.mean(axis=0)
    bounds = []
    for _signal in range(2):
        bounds.extend(
            (float(spec["lower"][index]), float(spec["upper"][index]))
            for index in range(n_crops)
        )
    bounds.append((None, None))
    bounds.extend((0.0, None) for _ in range(total_scenarios))
    result = linprog(
        objective, A_ub=matrix.tocsr(), b_ub=rhs, bounds=bounds,
        method="highs",
        options={
            "primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9,
            "ipm_optimality_tolerance": 1e-10,
        },
    )
    if not result.success:
        return {"status": "infeasible", "message": result.message}
    allocations = result.x[:x_size].reshape(2, n_crops)
    profits = np.r_[first @ allocations[0], second @ allocations[1]]
    _var, cvar = _var_cvar(-profits, alpha)
    return {
        "status": "optimal",
        "allocations": allocations,
        "expected_profit": float(profits.mean()),
        "cvar_loss": float(cvar),
        "cvar_slack": float(kappa - cvar),
    }


def information_flexibility(
    calibration: pd.DataFrame,
    spec: Mapping[str, Any],
    design: Mapping[str, Any],
) -> pd.DataFrame:
    low, high, state_meta = conditional_state_scenarios(calibration, design)
    prior = np.vstack([low, high])
    alpha = float(design["optimization"]["alpha_primary"])
    kappa, _expected, _minimum = risk_endpoint(prior, spec, alpha, 0.8)
    base_risk = solve_risk(prior, spec, alpha, kappa)
    if base_risk.allocation is None:
        raise RuntimeError("information-flexibility base allocation is infeasible")
    committed = np.asarray(base_risk.allocation)
    rows = []
    grid = design["information_flexibility"]
    for flexibility in grid["post_signal_adjustable_share_grid"]:
        flex = float(flexibility)
        flex_spec = dict(spec)
        flex_spec["lower"] = committed - flex * (np.asarray(spec["upper"]) * 0 + committed - np.asarray(spec["lower"]))
        flex_spec["upper"] = committed + flex * (np.asarray(spec["upper"]) - committed)
        no_info = solve_risk(prior, flex_spec, alpha, kappa)
        for accuracy in grid["signal_accuracy_grid"]:
            accuracy = float(accuracy)
            mixtures = symmetric_signal_mixtures(
                low, high, accuracy,
                int(design["uncertainty"]["base_seed"]) + 130000 + int(100 * flex),
            )
            contingent = solve_signal_contingent(mixtures, flex_spec, alpha, kappa)
            feasible = contingent["status"] == "optimal" and no_info.allocation is not None
            no_info_profit = (
                float(np.vstack(mixtures).mean(axis=0) @ no_info.allocation)
                if no_info.allocation is not None else np.nan
            )
            contingent_profit = (
                float(contingent["expected_profit"]) if feasible else np.nan
            )
            voi = contingent_profit - no_info_profit if feasible else np.nan
            row = {
                "signal": grid["signal"],
                "flexibility_path": "post_signal_acreage_reallocation",
                "flexibility_level": flex,
                "signal_accuracy": accuracy,
                "post_signal_adjustable_share": flex,
                "no_information_expected_profit": no_info_profit,
                "signal_contingent_expected_profit": contingent_profit,
                "value_of_information": voi,
                "risk_ceiling": kappa,
                "all_signal_problems_feasible": feasible,
                "signal_ignorability_available": True,
                "state_sample_size": len(calibration["year"].unique()),
                **state_meta,
            }
            if feasible:
                for signal_name, allocation in zip(
                    ("forecast_low", "forecast_high"), contingent["allocations"]
                ):
                    for crop, amount in zip(CROPS, allocation):
                        row[f"{signal_name}_allocation_{crop.replace(' ', '_')}"] = float(amount)
            rows.append(row)
    # A second, agricultural substitution path represents irrigation,
    # input-switching, or harvest-timing recourse that buffers the realized
    # state itself. As this flexibility closes the low/high payoff gap, the
    # forecast can become less valuable even though both remain useful alone.
    common = 0.5 * (low + high)
    for buffering in grid["state_shock_buffering_share_grid"]:
        buffer_share = float(buffering)
        buffered_low = (1.0 - buffer_share) * low + buffer_share * common
        buffered_high = (1.0 - buffer_share) * high + buffer_share * common
        buffered_prior = np.vstack([buffered_low, buffered_high])
        buffered_kappa, _buffered_expected, _buffered_minimum = risk_endpoint(
            buffered_prior, spec, alpha, 0.8
        )
        no_info = solve_risk(buffered_prior, spec, alpha, buffered_kappa)
        for accuracy in grid["signal_accuracy_grid"]:
            accuracy = float(accuracy)
            mixtures = symmetric_signal_mixtures(
                buffered_low, buffered_high, accuracy,
                int(design["uncertainty"]["base_seed"])
                + 140000 + int(100 * buffer_share),
            )
            contingent = solve_signal_contingent(
                mixtures, spec, alpha, buffered_kappa
            )
            feasible = contingent["status"] == "optimal" and no_info.allocation is not None
            no_info_profit = (
                float(np.vstack(mixtures).mean(axis=0) @ no_info.allocation)
                if no_info.allocation is not None else np.nan
            )
            contingent_profit = (
                float(contingent["expected_profit"]) if feasible else np.nan
            )
            row = {
                "signal": grid["signal"],
                "flexibility_path": "state_shock_buffering_recourse",
                "flexibility_level": buffer_share,
                "signal_accuracy": accuracy,
                "post_signal_adjustable_share": 1.0,
                "yield_shock_buffering_share": buffer_share,
                "no_information_expected_profit": no_info_profit,
                "signal_contingent_expected_profit": contingent_profit,
                "value_of_information": (
                    contingent_profit - no_info_profit if feasible else np.nan
                ),
                "risk_ceiling": buffered_kappa,
                "all_signal_problems_feasible": feasible,
                "signal_ignorability_available": True,
                "state_sample_size": len(calibration["year"].unique()),
                **state_meta,
            }
            if feasible:
                for signal_name, allocation in zip(
                    ("forecast_low", "forecast_high"), contingent["allocations"]
                ):
                    for crop, amount in zip(CROPS, allocation):
                        row[f"{signal_name}_allocation_{crop.replace(' ', '_')}"] = float(amount)
            rows.append(row)
    frame = pd.DataFrame(rows).sort_values(
        ["flexibility_path", "signal_accuracy", "flexibility_level"]
    ).reset_index(drop=True)
    frame["optimized_value"] = frame["signal_contingent_expected_profit"]
    frame["shared_ex_ante_CVaR"] = True
    frame["theorem_scope"] = grid["theorem_scope"]
    frame["numerical_scope"] = grid["numerical_scope"]
    frame["q1"] = np.nan
    frame["q2"] = np.nan
    frame["phi1"] = np.nan
    frame["phi2"] = np.nan
    frame["discrete_cross_difference"] = np.nan
    tolerance = float(grid["cross_difference_tolerance"])
    for path, part in frame.groupby("flexibility_path"):
        q_values = sorted(part["signal_accuracy"].unique())
        phi_values = sorted(part["flexibility_level"].unique())
        lookup = part.set_index(
            ["signal_accuracy", "flexibility_level"]
        )["optimized_value"]
        for q_index in range(1, len(q_values)):
            for phi_index in range(1, len(phi_values)):
                q1, q2 = q_values[q_index - 1], q_values[q_index]
                phi1, phi2 = phi_values[phi_index - 1], phi_values[phi_index]
                delta = (
                    (lookup.loc[(q2, phi2)] - lookup.loc[(q1, phi2)])
                    - (lookup.loc[(q2, phi1)] - lookup.loc[(q1, phi1)])
                )
                target = (
                    frame["flexibility_path"].eq(path)
                    & frame["signal_accuracy"].eq(q2)
                    & frame["flexibility_level"].eq(phi2)
                )
                frame.loc[target, ["q1", "q2", "phi1", "phi2"]] = [
                    q1, q2, phi1, phi2
                ]
                frame.loc[target, "discrete_cross_difference"] = float(delta)
    frame["cross_difference_classification"] = "zero_or_boundary"
    zero_information = frame["value_of_information"].abs() <= tolerance
    frame.loc[
        zero_information, "cross_difference_classification"
    ] = "zero_information"
    has_cross = frame["discrete_cross_difference"].notna() & ~zero_information
    frame.loc[
        has_cross & (frame["discrete_cross_difference"] > tolerance),
        "cross_difference_classification",
    ] = "positive_cross_difference"
    frame.loc[
        has_cross & (frame["discrete_cross_difference"] < -tolerance),
        "cross_difference_classification",
    ] = "negative_cross_difference"
    frame.loc[
        has_cross
        & (frame["discrete_cross_difference"].abs() <= tolerance),
        "cross_difference_classification",
    ] = "zero_or_boundary"
    frame["cross_difference_tolerance"] = tolerance
    return frame


def empirical_external_summary(design: Mapping[str, Any]) -> pd.DataFrame:
    detail = pd.read_csv(ROOT / "empirical/goal16/outputs/rank_metrics_state_year.csv")
    bootstrap = pd.read_csv(ROOT / "empirical/goal16/outputs/rank_metric_summary.csv")
    lagged = pd.read_csv(ROOT / "empirical/goal16/outputs/temporal_model.csv")
    rows = []
    for definition, part in detail.groupby("ranking_definition"):
        summary = bootstrap.loc[bootstrap["ranking_definition"].eq(definition)]
        inversion_ci = summary.loc[summary["metric"].eq("inversion_intensity")]
        top_ci = summary.loc[summary["metric"].eq("top_rank_disagreement")]
        row = {
            "evidence_layer": "external_descriptive",
            "ranking_definition": definition,
            "state_years": int(len(part)),
            "states": int(part["state"].nunique()),
            "years": ";".join(map(str, sorted(part["year"].unique()))),
            "mean_pairwise_inversions": float(part["pairwise_inversions"].mean()),
            "top_rank_reversal_rate": float(part["top_rank_disagreement"].mean()),
            "strong_reversal_rate": np.nan,
            "identification": "AGGREGATE_DESCRIPTIVE_NOT_CVAR_CAUSALITY",
            "mean_pairwise_inversions_ci_low": (
                3.0 * float(inversion_ci["ci_low"].iloc[0]) if len(inversion_ci) else np.nan
            ),
            "mean_pairwise_inversions_ci_high": (
                3.0 * float(inversion_ci["ci_high"].iloc[0]) if len(inversion_ci) else np.nan
            ),
            "top_rank_reversal_rate_ci_low": (
                float(top_ci["ci_low"].iloc[0]) if len(top_ci) else np.nan
            ),
            "top_rank_reversal_rate_ci_high": (
                float(top_ci["ci_high"].iloc[0]) if len(top_ci) else np.nan
            ),
        }
        rows.append(row)
    if len(lagged):
        temporal = lagged.loc[
            lagged["ranking_definition"].eq("relative_yield")
            & lagged["specification"].eq("primary_top")
            & lagged["term"].eq("prior_score_top")
        ]
        rows.append({
            "evidence_layer": "leakage_free_2024",
            "ranking_definition": "lagged_relative_yield_potential",
            "state_years": 651,
            "states": int(temporal["state_clusters"].iloc[0]) if len(temporal) else 31,
            "years": "2017--2024 transitions",
            "mean_pairwise_inversions": np.nan,
            "top_rank_reversal_rate": np.nan,
            "strong_reversal_rate": np.nan,
            "lagged_score_leader_acreage_share_effect": (
                float(temporal["estimate"].iloc[0]) if len(temporal) else np.nan
            ),
            "lagged_effect_ci_low": (
                float(temporal["ci_low"].iloc[0]) if len(temporal) else np.nan
            ),
            "lagged_effect_ci_high": (
                float(temporal["ci_high"].iloc[0]) if len(temporal) else np.nan
            ),
            "identification": "LOW_POWER_LEAKAGE_FREE_DESCRIPTIVE",
        })
    return pd.DataFrame(rows)


def frontier_summary(phase: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (family, tau), part in phase.groupby(["copula_family", "kendall_tau"]):
        part = part.sort_values("risk_tolerance")
        reversal = part.loc[part["selected_pairwise_reversal"].fillna(False)]
        complete = part.loc[
            part["selected_complete_rank_reversal"].fillna(False)
        ]
        strong = part.loc[part["selected_strong_reversal"].fillna(False)]
        transitions = part.loc[part["active_set_transition"].fillna(False)]
        rows.append({
            "copula_family": family,
            "kendall_tau": tau,
            "first_selected_reversal_risk_tolerance": (
                float(reversal["risk_tolerance"].min()) if len(reversal) else np.nan
            ),
            "last_selected_reversal_risk_tolerance": (
                float(reversal["risk_tolerance"].max()) if len(reversal) else np.nan
            ),
            "first_strong_reversal_risk_tolerance": (
                float(strong["risk_tolerance"].min()) if len(strong) else np.nan
            ),
            "selected_pairwise_reversal_cells": int(len(reversal)),
            "selected_complete_rank_reversal_cells": int(len(complete)),
            "selected_strong_reversal_cells": int(len(strong)),
            "possible_pairwise_reversal_cells": int(
                part["possible_pairwise_reversal"].fillna(False).sum()
            ),
            "universal_pairwise_reversal_cells": int(
                part["universal_pairwise_reversal"].fillna(False).sum()
            ),
            "possible_complete_rank_reversal_cells": int(
                part["possible_complete_rank_reversal"].fillna(False).sum()
            ),
            "universal_complete_rank_reversal_cells": int(
                part["universal_complete_rank_reversal"].fillna(False).sum()
            ),
            "possible_strong_reversal_cells": int(
                part["possible_strong_reversal"].fillna(False).sum()
            ),
            "universal_strong_reversal_cells": int(
                part["universal_strong_reversal"].fillna(False).sum()
            ),
            "infeasible_cells": int(part["classification"].eq("infeasible").sum()),
            "multiple_optimum_cells": int(part["multiple_optima"].fillna(False).sum()),
            "active_set_transition_count": int(len(transitions)),
            "reversal_region_connected_on_registered_grid": bool(
                len(reversal) <= 1
                or np.allclose(np.diff(reversal["risk_tolerance"]), 0.1)
            ),
        })
    return pd.DataFrame(rows)


def bootstrap_summary(bootstrap: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for metric in [
        "allocation_Corn", "allocation_Soybean", "allocation_Winter_Wheat",
        "expected_profit", "cvar_loss", "first_reversal_risk_tolerance",
    ]:
        values = bootstrap[metric].dropna().astype(float)
        rows.append({
            "metric": metric,
            "bootstrap_replications": int(len(bootstrap)),
            "finite_replications": int(len(values)),
            "estimate_mean": float(values.mean()) if len(values) else np.nan,
            "bootstrap_standard_error": float(values.std(ddof=1)) if len(values) > 1 else np.nan,
            "percentile_95_low": float(values.quantile(0.025)) if len(values) else np.nan,
            "percentile_95_high": float(values.quantile(0.975)) if len(values) else np.nan,
            "exact_binomial_95_low": np.nan,
            "exact_binomial_95_high": np.nan,
            "interval_method": "historical_resample_percentile",
        })
    for metric, column in [
        ("selected_pairwise_reversal_frequency", "selected_pairwise_reversal"),
        (
            "selected_complete_rank_reversal_frequency",
            "selected_complete_rank_reversal",
        ),
        ("selected_strong_reversal_frequency", "selected_strong_reversal"),
    ]:
        reversal_count = int(bootstrap[column].fillna(False).sum())
        interval = stats.binomtest(
            reversal_count, len(bootstrap)
        ).proportion_ci(confidence_level=0.95, method="exact")
        probability = reversal_count / len(bootstrap)
        rows.append({
            "metric": metric,
            "bootstrap_replications": int(len(bootstrap)),
            "finite_replications": int(len(bootstrap)),
            "event_count": reversal_count,
            "estimate_mean": probability,
            "bootstrap_standard_error": math.sqrt(
                probability * (1 - probability) / len(bootstrap)
            ),
            "percentile_95_low": np.nan,
            "percentile_95_high": np.nan,
            "exact_binomial_95_low": float(interval.low),
            "exact_binomial_95_high": float(interval.high),
            "interval_method": "exact_Clopper_Pearson_binomial",
        })
    return pd.DataFrame(rows)


def write_frame(frame: pd.DataFrame, name: str) -> Path:
    path = OUT / name
    frame.to_csv(path, index=False, float_format="%.12g")
    return path


def build_manifest(paths: Iterable[Path], design: Mapping[str, Any]) -> Dict[str, Any]:
    entries = []
    for path in sorted(paths):
        entries.append({
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        })
    return {
        "analysis_id": design["design_id"],
        "design_sha256": design["design_sha256"],
        "issue": 36,
        "parent_scientific_issue": 34,
        "repair_baseline_commit": design["repair_baseline_commit"],
        "source_panel": PANEL_PATH.relative_to(ROOT).as_posix(),
        "source_panel_sha256": sha256(PANEL_PATH),
        "raw_empirical_observations": 24,
        "raw_effective_years": 8,
        "simulated_scenarios_are_empirical_observations": False,
        "solver": "scipy.optimize.linprog/HiGHS",
        "selection_rule": design["optimization"]["selection_rule"],
        "outputs": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--quick", action="store_true",
        help="Use reduced uncertainty iterations for development only.",
    )
    args = parser.parse_args()
    design = load_design()
    if args.quick:
        design = copy.deepcopy(design)
        design["uncertainty"]["historical_bootstrap_replications"] = 8
        design["uncertainty"]["optimization_scenarios"] = 256
        design["uncertainty"]["evaluation_scenarios"] = 512
    OUT.mkdir(parents=True, exist_ok=True)
    calibration, calibration_summary = load_calibration(design)
    margin_matrix, means, stds, scores = arrays(calibration, calibration_summary)
    spec = operational_spec(design, calibration)

    primary_scenarios, primary_metadata = scenarios(
        means, stds, design["dependence"]["primary_family"],
        design["dependence"]["primary_kendall_tau"],
        design["uncertainty"]["optimization_scenarios"],
        design["uncertainty"]["base_seed"],
        empirical_samples=margin_matrix,
    )
    policies, endpoints = policy_comparison(
        primary_scenarios, spec, scores, design
    )
    phase = phase_diagram(
        means, stds, margin_matrix, scores, spec, design
    )
    dependence = dependence_diagnostics(margin_matrix, design)
    diversification = diversification_failure(
        means, stds, margin_matrix, scores, spec, design
    )
    margin_mechanisms = margin_mechanism(
        calibration, calibration_summary, policies
    )
    risk_mechanisms = risk_induced_mechanism(
        calibration, means, stds, margin_matrix, scores, spec, design
    )
    operational_mechanisms = operational_mechanism(
        means, stds, margin_matrix, scores, spec, design
    )
    robustness = robustness_cases(
        means, stds, margin_matrix, scores, spec, design
    )
    bootstrap = bootstrap_uncertainty(calibration, spec, design)
    information = information_flexibility(calibration, spec, design)
    empirical = empirical_external_summary(design)
    tolerance_sensitivity = reversal_tolerance_sensitivity(
        phase, robustness, bootstrap, scores, design
    )

    paths = [
        write_frame(calibration, "kansas_calibration_panel.csv"),
        write_frame(calibration_summary, "score_and_margin_calibration.csv"),
        write_frame(policies, "policy_comparison.csv"),
        write_frame(phase, "reversal_phase_diagram.csv"),
        write_frame(frontier_summary(phase), "reversal_frontier_summary.csv"),
        write_frame(dependence, "dependence_diagnostics.csv"),
        write_frame(diversification, "diversification_failure.csv"),
        write_frame(margin_mechanisms, "margin_mechanism.csv"),
        write_frame(risk_mechanisms, "risk_induced_reversal.csv"),
        write_frame(operational_mechanisms, "operational_mechanism.csv"),
        write_frame(robustness, "robustness_results.csv"),
        write_frame(bootstrap, "bootstrap_replications.csv"),
        write_frame(bootstrap_summary(bootstrap), "uncertainty_summary.csv"),
        write_frame(information, "information_flexibility.csv"),
        write_frame(tolerance_sensitivity, "reversal_tolerance_sensitivity.csv"),
        write_frame(empirical, "external_descriptive_evidence.csv"),
    ]

    primary = endpoints["primary_result"]
    summary = {
        "design_id": design["design_id"],
        "design_sha256": design["design_sha256"],
        "quick_mode": bool(args.quick),
        "calibration": {
            "geography": design["scope"]["geography"],
            "years": design["scope"]["calibration_years"],
            "crop_rows": len(calibration),
            "raw_effective_years": calibration["year"].nunique(),
            "scores": dict(zip(CROPS, map(float, scores))),
            "score_order": [CROPS[index] for index in np.argsort(-scores)],
            "means": dict(zip(CROPS, map(float, means))),
            "standard_deviations": dict(zip(CROPS, map(float, stds))),
        },
        "primary_scenario_metadata": primary_metadata,
        "primary_model": {
            "alpha": endpoints["alpha"],
            "risk_tolerance": endpoints["risk_tolerance"],
            "minimum_cvar": endpoints["minimum_cvar"],
            "expected_profit_endpoint_cvar": endpoints["expected_profit_endpoint_cvar"],
            "cvar_limit": endpoints["primary_cvar_limit"],
            "solver_status": primary.status,
            "expected_profit": primary.expected_profit,
            "cvar_loss": primary.cvar_loss,
            "allocation": (
                dict(zip(CROPS, map(float, primary.allocation)))
                if primary.allocation is not None else None
            ),
            "idle_land": (
                float(spec["total_land"] - primary.allocation.sum())
                if primary.allocation is not None else None
            ),
            "reversal": (
                reversal_classification(primary.allocation, scores, design)
                if primary.allocation is not None else None
            ),
            "active_set": active_set(primary),
            "kkt_primal_residual": primary.diagnostics.get("kkt_primal_residual"),
            "kkt_stationarity_residual": primary.diagnostics.get("kkt_stationarity_residual"),
            "kkt_complementarity_residual": primary.diagnostics.get("kkt_complementarity_residual"),
        },
        "frontier": {
            "cells": len(phase),
            "selected_pairwise_reversal_cells": int(
                phase["selected_pairwise_reversal"].fillna(False).sum()
            ),
            "selected_complete_rank_reversal_cells": int(
                phase["selected_complete_rank_reversal"].fillna(False).sum()
            ),
            "selected_strong_reversal_cells": int(
                phase["selected_strong_reversal"].fillna(False).sum()
            ),
            "possible_pairwise_reversal_cells": int(
                phase["possible_pairwise_reversal"].fillna(False).sum()
            ),
            "universal_pairwise_reversal_cells": int(
                phase["universal_pairwise_reversal"].fillna(False).sum()
            ),
            "possible_complete_rank_reversal_cells": int(
                phase["possible_complete_rank_reversal"].fillna(False).sum()
            ),
            "universal_complete_rank_reversal_cells": int(
                phase["universal_complete_rank_reversal"].fillna(False).sum()
            ),
            "possible_strong_reversal_cells": int(
                phase["possible_strong_reversal"].fillna(False).sum()
            ),
            "universal_strong_reversal_cells": int(
                phase["universal_strong_reversal"].fillna(False).sum()
            ),
            "infeasible_cells": int(phase["classification"].eq("infeasible").sum()),
            "multiple_optimum_cells": int(phase["multiple_optima"].fillna(False).sum()),
        },
        "diversification_failure_identified": bool(
            diversification["diversification_failure_identified"].iloc[0]
        ),
        "strong_diversification_failure_identified": bool(
            diversification["strong_diversification_failure_identified"].iloc[0]
        ),
        "risk_induced_crossing_identified": bool(
            risk_mechanisms["registered_loose_to_tight_crossing"].iloc[0]
        ),
        "first_operational_crossing_cap": float(
            operational_mechanisms["first_operational_crossing_cap"].iloc[0]
        ),
        "information_cross_difference_regions": information[
            "cross_difference_classification"
        ].value_counts().to_dict(),
        "bootstrap_selected_pairwise_reversal_frequency": float(
            bootstrap["selected_pairwise_reversal"].fillna(False).mean()
        ),
        "bootstrap_selected_complete_rank_reversal_frequency": float(
            bootstrap["selected_complete_rank_reversal"].fillna(False).mean()
        ),
        "bootstrap_selected_strong_reversal_frequency": float(
            bootstrap["selected_strong_reversal"].fillna(False).mean()
        ),
        "empirical_evidence_scope": "AGGREGATE_DESCRIPTIVE_NOT_CAUSAL",
    }
    summary_path = OUT / "summary.json"
    summary_path.write_text(
        json.dumps(jsonable(summary), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths.append(summary_path)
    manifest = build_manifest(paths, design)
    manifest_path = OUT / "analysis_manifest.json"
    manifest_path.write_text(
        json.dumps(jsonable(manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    checksum_path = OUT / "SHA256SUMS.txt"
    checksum_path.write_text(
        "\n".join(f"{sha256(path)}  {path.name}" for path in sorted(paths + [manifest_path]))
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
