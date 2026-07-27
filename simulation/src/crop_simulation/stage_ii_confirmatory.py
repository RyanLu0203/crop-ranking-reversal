"""GOAL-12 controlled confirmatory-simulation utilities.

The functions in this module are design driven.  They never read Stage I
results to select parameters, seeds, cells, tolerances, or stopping points.
"""

from __future__ import annotations

import hashlib
import json
import math
from functools import lru_cache
from itertools import combinations
from math import factorial
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
import yaml
from scipy import stats
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

from crop_optimization.cvar_optimizer import (
    AllocationResult,
    highs_tolerance_options,
    solve_cvar_allocation,
    solve_expected_profit_allocation,
)
from crop_optimization.evaluation import empirical_var_cvar_losses
from crop_optimization.optimal_face_audit import audit_pairwise_optimal_face

from .panel_calibration import (
    clayton_theta_from_kendall_tau,
    equicorrelation_from_kendall_tau,
    load_margin_matrix,
    panel_calibration,
)
from .scenario_generation import generate_profit_scenarios

ROOT = Path(__file__).resolve().parents[3]
DESIGN_PATH = ROOT / "simulation/configs/stage_ii_confirmatory_design.yaml"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_array(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def load_confirmatory_design(path: Path = DESIGN_PATH) -> dict[str, Any]:
    design = yaml.safe_load(path.read_text(encoding="utf-8"))
    validate_confirmatory_design(design, path)
    design["design_sha256"] = sha256_file(path)
    return design


def validate_confirmatory_design(design: Mapping[str, Any], path: Path = DESIGN_PATH) -> None:
    if design.get("status") != "FROZEN_BEFORE_RESULTS":
        raise ValueError("confirmatory design must be frozen before results")
    if int(design.get("owner_issue", -1)) != 22:
        raise ValueError("confirmatory design must be owned by Issue #22")
    if design.get("scope", {}).get("land_unit") != "normalized_share":
        raise ValueError("canonical Stage II land unit must be normalized_share")
    if design.get("scope", {}).get("manuscript_rewrite_allowed") is not False:
        raise ValueError("GOAL-12 cannot authorize a manuscript rewrite")
    panel = ROOT / str(design["dependencies"]["panel"])
    if sha256_file(panel) != str(design["dependencies"]["panel_sha256"]):
        raise ValueError("calibration panel hash differs from the frozen design")
    schedule = list(map(int, design["sequential_replication"]["check_schedule"]))
    if schedule != sorted(set(schedule)) or schedule[0] != int(
        design["sequential_replication"]["minimum_replications"]
    ) or schedule[-1] != int(design["sequential_replication"]["maximum_replications"]):
        raise ValueError("invalid sequential-replication schedule")
    if int(design["randomness"]["optimization_scenarios"]) >= int(
        design["randomness"]["evaluation_scenarios"]
    ):
        raise ValueError("independent evaluation must use more scenarios than optimization")
    required = {"E1", "E2", "E3", "E4", "E5", "E6", "ATTRIBUTION"}
    if set(design["randomness"]["seed_roots"]) != required:
        raise ValueError("seed roots do not cover every experiment")
    if set(design["experiments"]) != {
        "E1_margin", "E2_operations", "E3_risk", "E4_dependence",
        "E5_diversification", "E6_information_flexibility",
    }:
        raise ValueError("experiment set differs from the frozen E1--E6 contract")
    if int(design["attribution"]["all_subsets"]) != 16 or int(
        design["attribution"]["all_orders"]
    ) != 24:
        raise ValueError("four-block attribution must cover 16 subsets and 24 orders")
    if not path.is_file():
        raise ValueError("design path does not exist")


def replication_seed(design: Mapping[str, Any], experiment: str, index: int) -> int:
    maximum = int(design["sequential_replication"]["maximum_replications"])
    if not 1 <= int(index) <= maximum:
        raise ValueError("replication index outside frozen range")
    return int(design["randomness"]["seed_roots"][experiment]) + int(index)


@lru_cache(maxsize=1)
def _governed_panel_calibration() -> dict[str, Any]:
    return panel_calibration()


def calibration_arrays(design: Mapping[str, Any]) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray]:
    crops = list(design["scope"]["crops"])
    calibration = design["calibration"]
    means = np.asarray([calibration["means"][crop] for crop in crops], dtype=float)
    stds = np.asarray(
        [calibration["standard_deviations"][crop] for crop in crops], dtype=float
    )
    costs = np.asarray(
        [calibration["operating_costs_2024_real"][crop] for crop in crops], dtype=float
    )
    observed = _governed_panel_calibration()
    if not np.allclose(means, [observed["means"][crop] for crop in crops], atol=1e-8):
        raise ValueError("frozen mean calibration is not reproduced by the governed panel")
    if not np.allclose(stds, [observed["stds"][crop] for crop in crops], atol=1e-8):
        raise ValueError("frozen standard deviations are not reproduced by the panel")
    if not np.allclose(
        costs, [observed["costs_2024_real"][crop] for crop in crops], atol=1e-8
    ):
        raise ValueError("frozen costs are not reproduced by the governed panel")
    return crops, means, stds, costs


def _student_t_marginal(uniforms: np.ndarray, means: np.ndarray, stds: np.ndarray) -> np.ndarray:
    df = 5.0
    standardized = stats.t.ppf(np.clip(uniforms, 1e-9, 1 - 1e-9), df=df)
    standardized /= math.sqrt(df / (df - 2.0))
    return means[None, :] + stds[None, :] * standardized


@lru_cache(maxsize=1)
def _empirical_rank_uniforms() -> np.ndarray:
    matrix = load_margin_matrix()
    ranks = matrix.rank(axis=0, method="average").to_numpy(dtype=float)
    return (ranks - 0.5) / len(matrix)


def _empirical_copula_uniforms(n: int, seed: int) -> tuple[np.ndarray, float]:
    uniforms = _empirical_rank_uniforms()
    rng = np.random.default_rng(int(seed))
    sampled = uniforms[rng.integers(0, len(uniforms), size=int(n))]
    q = 0.10
    coexceed = []
    for i, j in combinations(range(sampled.shape[1]), 2):
        coexceed.append(float(np.mean((sampled[:, i] <= q) & (sampled[:, j] <= q)) / q))
    return np.clip(sampled, 1e-9, 1 - 1e-9), float(np.mean(coexceed))


def generate_family_scenarios(
    design: Mapping[str, Any],
    family: str,
    tau: float | None,
    seed: int,
    n_scenarios: int,
    *,
    means: np.ndarray | None = None,
    stds: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    crops, frozen_means, frozen_stds, _ = calibration_arrays(design)
    means = frozen_means if means is None else np.asarray(means, dtype=float)
    stds = frozen_stds if stds is None else np.asarray(stds, dtype=float)
    normalized = str(family).lower()
    tau_value = 0.25 if tau is None else float(tau)
    if normalized == "empirical_copula":
        uniforms, tail_metric = _empirical_copula_uniforms(n_scenarios, seed)
        scenarios = _student_t_marginal(uniforms, means, stds)
        metadata = {
            "copula_family": normalized,
            "kendall_tau": None,
            "parameter": "observed_rank_rows_1998_2024",
            "lower_tail_metric": tail_metric,
            "ordering_scope": "EMPIRICAL_COPULA_MODEL_SENSITIVITY_NOT_PARAMETRIC_ORDER",
        }
    else:
        corr = equicorrelation_from_kendall_tau(tau_value, len(crops))
        if normalized == "gaussian":
            copula, parameter = "Gaussian", corr
        elif normalized == "student_t_df4":
            copula, parameter = "Student-t", {"df": 4, "corr": corr}
        elif normalized == "clayton":
            copula, parameter = "Clayton", clayton_theta_from_kendall_tau(tau_value)
        else:
            raise ValueError(f"unknown Stage II dependence family: {family}")
        scenarios, raw = generate_profit_scenarios(
            means,
            stds,
            int(n_scenarios),
            copula,
            parameter,
            int(seed),
            crop_names=crops,
            marginal_model={"type": "student_t", "df": 5},
        )
        metadata = {
            "copula_family": normalized,
            "kendall_tau": tau_value,
            "parameter": raw["copula_param"],
            "lower_tail_metric": raw["lower_tail_dependence"],
            "ordering_scope": raw["ordering_scope"],
        }
    metadata.update(
        {
            "seed": int(seed),
            "n_scenarios": int(n_scenarios),
            "scenario_sha256": sha256_array(scenarios),
            "marginal_family": "student_t_df5",
        }
    )
    return scenarios, metadata


def operational_spec(
    design: Mapping[str, Any],
    *,
    budget_ratio: float = 1.10,
    corn_upper: float = 1.0,
    corn_rotation_cap: float = 1.0,
    soybean_contract_minimum: float = 0.0,
) -> dict[str, Any]:
    crops, _, _, costs = calibration_arrays(design)
    return {
        "crop_names": crops,
        "costs": costs,
        "total_land": 1.0,
        "budget": float(budget_ratio) * float(costs.max()),
        "lower": np.zeros(len(crops)),
        "upper": np.asarray([float(corn_upper), 1.0, 1.0]),
        "rotation_caps": {"Corn": float(corn_rotation_cap)}
        if float(corn_rotation_cap) < 1.0 else {},
        "contract_minimums": {"Soybean": float(soybean_contract_minimum)}
        if float(soybean_contract_minimum) > 0 else {},
    }


def solve_expected(scenarios: np.ndarray, spec: Mapping[str, Any]) -> AllocationResult:
    return solve_expected_profit_allocation(
        scenarios.mean(axis=0),
        spec["costs"],
        spec["total_land"],
        spec["budget"],
        spec["lower"],
        spec["upper"],
        spec["rotation_caps"],
        list(spec["crop_names"]),
        spec["contract_minimums"],
    )


def solve_risk(
    scenarios: np.ndarray,
    spec: Mapping[str, Any],
    alpha: float,
    risk_limit: float,
    method: str = "highs",
) -> AllocationResult:
    return solve_cvar_allocation(
        scenarios,
        spec["costs"],
        spec["total_land"],
        spec["budget"],
        float(alpha),
        float(risk_limit),
        spec["lower"],
        spec["upper"],
        spec["rotation_caps"],
        list(spec["crop_names"]),
        spec["contract_minimums"],
        solver_method=method,
    )


def solve_minimum_cvar(
    scenarios: np.ndarray,
    spec: Mapping[str, Any],
    alpha: float,
    method: str = "highs",
) -> AllocationResult:
    scenarios = np.asarray(scenarios, dtype=float)
    n_scenarios, n_crops = scenarios.shape
    costs = np.asarray(spec["costs"], dtype=float)
    lower = np.asarray(spec["lower"], dtype=float)
    upper = np.asarray(spec["upper"], dtype=float)
    crops = list(spec["crop_names"])
    v_idx = n_crops
    q_start = n_crops + 1
    n_extra = len(spec["rotation_caps"]) + len(spec["contract_minimums"])
    matrix = lil_matrix((2 + n_scenarios + n_extra, n_crops + 1 + n_scenarios))
    rhs = np.zeros(matrix.shape[0])
    row = 0
    matrix[row, :n_crops] = 1.0
    rhs[row] = float(spec["total_land"])
    row += 1
    matrix[row, :n_crops] = costs
    rhs[row] = float(spec["budget"])
    row += 1
    for index, scenario in enumerate(scenarios):
        matrix[row, :n_crops] = -scenario
        matrix[row, v_idx] = -1.0
        matrix[row, q_start + index] = -1.0
        row += 1
    for crop, cap in spec["rotation_caps"].items():
        matrix[row, crops.index(crop)] = 1.0
        rhs[row] = float(cap)
        row += 1
    for crop, minimum in spec["contract_minimums"].items():
        matrix[row, crops.index(crop)] = -1.0
        rhs[row] = -float(minimum)
        row += 1
    objective = np.zeros(n_crops + 1 + n_scenarios)
    objective[v_idx] = 1.0
    objective[q_start:] = 1.0 / ((1.0 - float(alpha)) * n_scenarios)
    bounds: list[tuple[float | None, float | None]] = [
        (float(lower[i]), float(upper[i])) for i in range(n_crops)
    ]
    bounds.append((None, None))
    bounds.extend((0.0, None) for _ in range(n_scenarios))
    result = linprog(
        objective,
        A_ub=matrix.tocsr(),
        b_ub=rhs,
        bounds=bounds,
        method=method,
        options=highs_tolerance_options(method),
    )
    if not result.success:
        return AllocationResult(
            None, None, None, None, "infeasible_or_failed", int(result.status),
            str(result.message), {},
        )
    allocation = np.maximum(result.x[:n_crops], 0.0)
    profits = scenarios @ allocation
    var, cvar = empirical_var_cvar_losses(-profits, alpha)
    return AllocationResult(
        allocation,
        float(profits.mean()),
        float(cvar),
        float(var),
        "optimal",
        int(result.status),
        str(result.message),
        {"minimum_cvar_objective": float(result.fun)},
    )


def face_audit(
    scenarios: np.ndarray,
    spec: Mapping[str, Any],
    alpha: float,
    risk_limit: float,
    result: AllocationResult,
    method: str = "highs",
) -> dict[str, Any]:
    if result.allocation is None:
        return {
            "status": "infeasible",
            "selected_reversal": False,
            "possible_reversal": False,
            "universal_reversal": False,
        }
    return audit_pairwise_optimal_face(
        scenarios,
        spec["costs"],
        spec["total_land"],
        spec["budget"],
        alpha,
        risk_limit,
        spec["lower"],
        spec["upper"],
        list(spec["crop_names"]),
        "Corn",
        "Soybean",
        rotation_caps=spec["rotation_caps"],
        contract_minimums=spec["contract_minimums"],
        allocation_tolerance=1e-4,
        objective_relative_tolerance=1e-8,
        primary_result=result,
        solver_method=method,
    )


def tail_subgradient(scenarios: np.ndarray, allocation: np.ndarray, alpha: float) -> np.ndarray:
    scenarios = np.asarray(scenarios, dtype=float)
    losses = -(scenarios @ np.asarray(allocation, dtype=float))
    order = np.argsort(-losses, kind="mergesort")
    cap = 1.0 / ((1.0 - float(alpha)) * len(losses))
    weights = np.zeros(len(losses))
    remaining = 1.0
    for index in order:
        weight = min(cap, remaining)
        weights[index] = weight
        remaining -= weight
        if remaining <= 1e-14:
            break
    if abs(weights.sum() - 1.0) > 1e-10:
        raise AssertionError("tail subgradient weights do not sum to one")
    return -(weights @ scenarios)


def pairwise_pressure_row(
    result: AllocationResult,
    scenarios: np.ndarray,
    spec: Mapping[str, Any],
    alpha: float,
    crop_i: str = "Corn",
    crop_j: str = "Soybean",
) -> dict[str, float]:
    if result.allocation is None:
        raise ValueError("pressure decomposition requires an optimal allocation")
    crops = list(spec["crop_names"])
    i, j = crops.index(crop_i), crops.index(crop_j)
    means = scenarios.mean(axis=0)
    eta = float(result.diagnostics.get("risk_dual_eta", 0.0))
    if eta > 1e-10:
        tail = np.asarray(
            [result.diagnostics[f"cvar_subgradient_{crop}"] for crop in crops],
            dtype=float,
        )
    else:
        tail = np.zeros(len(crops))
    beta = float(result.diagnostics.get("shadow_price_budget", 0.0))
    shared_rows: list[np.ndarray] = []
    shared_duals: list[float] = []
    for crop in spec["rotation_caps"]:
        vector = np.zeros(len(crops)); vector[crops.index(crop)] = 1.0
        shared_rows.append(vector)
        shared_duals.append(float(result.diagnostics.get(f"shadow_price_rotation_{crop}", 0.0)))
    for crop in spec["contract_minimums"]:
        vector = np.zeros(len(crops)); vector[crops.index(crop)] = -1.0
        shared_rows.append(vector)
        shared_duals.append(float(result.diagnostics.get(f"shadow_price_contract_{crop}", 0.0)))
    shared = np.vstack(shared_rows) if shared_rows else np.zeros((0, len(crops)))
    shared_duals_arr = np.asarray(shared_duals, dtype=float)
    lower = np.asarray(
        [float(result.diagnostics.get(f"raw_dual_lower_bound_{crop}", 0.0)) for crop in crops]
    )
    upper = np.asarray(
        [-float(result.diagnostics.get(f"raw_dual_upper_bound_{crop}", 0.0)) for crop in crops]
    )
    margin = float(means[i] - means[j])
    risk = float(eta * (tail[i] - tail[j]))
    budget = float(beta * (np.asarray(spec["costs"])[i] - np.asarray(spec["costs"])[j]))
    shared_normal = shared.T @ shared_duals_arr if len(shared_duals_arr) else np.zeros(len(crops))
    shared_pressure = float(shared_normal[i] - shared_normal[j])
    boundary = float(-(lower[i] - lower[j]) + (upper[i] - upper[j]))
    return {
        "margin_pressure": margin,
        "tail_risk_pressure": risk,
        "budget_pressure": budget,
        "shared_pressure": shared_pressure,
        "boundary_pressure": boundary,
        "stationarity_residual": float(margin - risk - budget - shared_pressure - boundary),
        "risk_dual_eta": eta,
        "budget_dual": beta,
    }


def allocation_evaluation(
    scenarios: np.ndarray,
    allocation: Iterable[float],
    alpha: float,
    risk_limit: float,
) -> dict[str, float | bool]:
    x = np.asarray(list(allocation), dtype=float)
    profits = np.asarray(scenarios, dtype=float) @ x
    losses = -profits
    var, cvar = empirical_var_cvar_losses(losses, alpha)
    tail_gradient = tail_subgradient(np.asarray(scenarios), x, alpha)
    contributions = x * tail_gradient
    individual_q = np.quantile(np.asarray(scenarios), 0.10, axis=0)
    coexceed = [
        float(np.mean((scenarios[:, i] <= individual_q[i]) & (scenarios[:, j] <= individual_q[j])))
        for i, j in combinations(range(scenarios.shape[1]), 2)
    ]
    result: dict[str, float | bool] = {
        "expected_profit": float(profits.mean()),
        "profit_variance": float(profits.var(ddof=1)),
        "var_loss": float(var),
        "cvar_loss": float(cvar),
        "risk_violation": float(max(0.0, cvar - float(risk_limit))),
        "risk_feasible": bool(cvar <= float(risk_limit) + 1e-7),
        "hhi": float(np.sum(x * x)),
        "effective_crop_count": float(1.0 / np.sum(x * x)) if np.sum(x * x) > 0 else 0.0,
        "tail_coexceedance": float(np.mean(coexceed)),
    }
    for crop, value, contribution in zip(
        ("Corn", "Soybean", "Winter_Wheat"), x, contributions
    ):
        result[f"allocation_{crop}"] = float(value)
        result[f"tail_contribution_{crop}"] = float(contribution)
    return result


def raw_policy_row(
    design: Mapping[str, Any],
    experiment_id: str,
    cell_id: str,
    seed: int,
    scenarios: np.ndarray,
    metadata: Mapping[str, Any],
    spec: Mapping[str, Any],
    alpha: float,
    risk_limit: float,
    result: AllocationResult,
    *,
    model_stage: str,
    audit_optimal_face: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    face = face_audit(scenarios, spec, alpha, risk_limit, result) if audit_optimal_face else {}
    row: dict[str, Any] = {
        "design_id": design["design_id"],
        "design_sha256": design["design_sha256"],
        "experiment_id": experiment_id,
        "cell_id": cell_id,
        "replication_seed": int(seed),
        "model_stage": model_stage,
        "scenario_sha256": metadata["scenario_sha256"],
        "copula_family": metadata["copula_family"],
        "kendall_tau": metadata.get("kendall_tau"),
        "alpha": float(alpha),
        "risk_limit": float(risk_limit),
        "solver_status": result.status,
        "solver_status_code": result.solver_status,
        "expected_profit": result.expected_profit,
        "cvar_loss": result.cvar_loss,
        "var_loss": result.var_loss,
        "face_status": face.get("status", "not_run"),
        "selected_reversal": face.get("selected_reversal", False),
        "possible_reversal": face.get("possible_reversal", False),
        "universal_reversal": face.get("universal_reversal", False),
        "face_min_difference": face.get("min_difference"),
        "face_max_difference": face.get("max_difference"),
        "face_width": face.get("optimal_face_width"),
        "evidence_class": "CONFIRMATORY_SIMULATION_NOT_EMPIRICAL_EVIDENCE",
    }
    if result.allocation is not None:
        for crop, value in zip(spec["crop_names"], result.allocation):
            row[f"allocation_{crop.replace(' ', '_')}"] = float(value)
        for key, value in result.diagnostics.items():
            if np.isscalar(value) and not isinstance(value, str):
                row[key] = value
    face_row = {
        "design_id": design["design_id"],
        "design_sha256": design["design_sha256"],
        "experiment_id": experiment_id,
        "cell_id": cell_id,
        "replication_seed": int(seed),
        "status": face.get("status", "not_run"),
        "selected_difference": face.get("selected_difference"),
        "minimum_difference": face.get("min_difference"),
        "maximum_difference": face.get("max_difference"),
        "face_width": face.get("optimal_face_width"),
        "selected_reversal": face.get("selected_reversal", False),
        "possible_reversal": face.get("possible_reversal", False),
        "universal_reversal": face.get("universal_reversal", False),
    }
    return row, face_row


def t_interval(
    values: Sequence[float], confidence: float, comparisons: int
) -> tuple[float, float, float, float]:
    array = np.asarray(values, dtype=float)
    array = array[np.isfinite(array)]
    if len(array) == 0:
        return math.nan, math.nan, math.nan, math.inf
    mean = float(array.mean())
    if len(array) == 1:
        return mean, math.nan, math.nan, math.inf
    alpha = (1.0 - float(confidence)) / max(int(comparisons), 1)
    critical = float(stats.t.ppf(1.0 - alpha / 2.0, len(array) - 1))
    half = critical * float(array.std(ddof=1)) / math.sqrt(len(array))
    return mean, mean - half, mean + half, half


def wilson_interval(
    successes: int, trials: int, confidence: float, comparisons: int
) -> tuple[float, float, float]:
    if trials <= 0:
        return math.nan, math.nan, math.inf
    alpha = (1.0 - float(confidence)) / max(int(comparisons), 1)
    z = float(stats.norm.ppf(1.0 - alpha / 2.0))
    p = successes / trials
    denom = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denom
    half = z * math.sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials * trials)) / denom
    lo, hi = max(0.0, center - half), min(1.0, center + half)
    return lo, hi, hi - lo


def precision_target(design: Mapping[str, Any], metric: str, binary: bool) -> float:
    targets = design["sequential_replication"]["precision_targets"]
    if binary:
        return float(targets["reversal_probability_interval_width"])
    mapping = {
        "allocation_l1": "allocation_l1_half_width",
        "expected_profit": "expected_profit_half_width",
        "cvar_loss": "cvar_loss_half_width",
        "feasible_regret": "feasible_regret_half_width",
        "information_interaction": "information_interaction_half_width",
    }
    if metric not in mapping:
        raise ValueError(f"no frozen precision target for metric {metric}")
    return float(targets[mapping[metric]])


def stopping_rows(
    design: Mapping[str, Any],
    contrasts: pd.DataFrame,
    experiment_id: str,
    check_n: int,
) -> tuple[list[dict[str, Any]], bool]:
    part = contrasts.loc[contrasts["experiment_id"].eq(experiment_id)]
    groups = list(part.groupby(["contrast_id", "metric"], sort=True))
    comparisons = len(groups)
    confidence = float(design["sequential_replication"]["nominal_familywise_coverage"])
    rows: list[dict[str, Any]] = []
    for (contrast_id, metric), group in groups:
        group = group.sort_values("replication_seed").head(int(check_n))
        binary = bool(group["binary_metric"].astype(bool).all())
        values = group["value"].astype(float).to_numpy()
        finite_n = int(np.isfinite(values).sum())
        complete = bool(len(values) == int(check_n) and finite_n == int(check_n))
        target = precision_target(design, str(metric), binary)
        if binary:
            finite_values = values[np.isfinite(values)]
            lo, hi, width = wilson_interval(
                int(finite_values.sum()), len(finite_values), confidence, comparisons
            )
            estimate = float(finite_values.mean()) if len(finite_values) else math.nan
            half_width = width / 2.0
            precision_pass = complete and width <= target
            interval_width = width
        else:
            estimate, lo, hi, half_width = t_interval(values, confidence, comparisons)
            precision_pass = complete and half_width <= target
            interval_width = 2.0 * half_width
        rows.append(
            {
                "design_id": design["design_id"],
                "design_sha256": design["design_sha256"],
                "experiment_id": experiment_id,
                "contrast_id": contrast_id,
                "metric": metric,
                "check_n": int(len(values)),
                "finite_n": finite_n,
                "estimate": estimate,
                "ci_low": lo,
                "ci_high": hi,
                "half_width": half_width,
                "interval_width": interval_width,
                "precision_target": target,
                "precision_pass": bool(precision_pass),
                "binary_metric": binary,
                "familywise_coverage": confidence,
                "multiplicity_count": comparisons,
            }
        )
    return rows, bool(rows and all(row["precision_pass"] for row in rows))


def finite_state_information_value_subset(
    payoff_by_action_state: np.ndarray,
    prior: Sequence[float],
    signal_given_state: np.ndarray,
    actions: Sequence[int],
) -> dict[str, Any]:
    payoff = np.asarray(payoff_by_action_state, dtype=float)
    prior_array = np.asarray(prior, dtype=float)
    signal = np.asarray(signal_given_state, dtype=float)
    allowed = np.asarray(list(actions), dtype=int)
    no_info_values = payoff[allowed] @ prior_array
    no_info_local = int(np.argmax(no_info_values))
    no_info_action = int(allowed[no_info_local])
    no_info_value = float(no_info_values[no_info_local])
    signal_value = 0.0
    signal_actions: list[int] = []
    for signal_index in range(signal.shape[1]):
        joint = prior_array * signal[:, signal_index]
        conditional = payoff[allowed] @ joint
        local = int(np.argmax(conditional))
        signal_actions.append(int(allowed[local]))
        signal_value += float(conditional[local])
    if signal_value < no_info_value - 1e-10:
        raise AssertionError("ignore-signal policy was not retained")
    return {
        "no_information_action": no_info_action,
        "signal_actions": signal_actions,
        "no_information_value": no_info_value,
        "signal_value": signal_value,
        "value_of_information": signal_value - no_info_value,
        "policy_actionable": bool(any(action != no_info_action for action in signal_actions)),
    }


def symmetric_garbling(high_accuracy: float, low_accuracy: float) -> np.ndarray:
    high, low = float(high_accuracy), float(low_accuracy)
    if not 0.5 <= low <= high <= 1.0:
        raise ValueError("binary accuracies must satisfy 0.5 <= low <= high <= 1")
    if abs(high - 0.5) <= 1e-12:
        return np.asarray([[1.0, 0.0], [0.0, 1.0]])
    keep = (low + high - 1.0) / (2.0 * high - 1.0)
    matrix = np.asarray([[keep, 1.0 - keep], [1.0 - keep, keep]])
    high_matrix = np.asarray([[high, 1.0 - high], [1.0 - high, high]])
    low_matrix = np.asarray([[low, 1.0 - low], [1.0 - low, low]])
    if not np.allclose(high_matrix @ matrix, low_matrix, atol=1e-12):
        raise AssertionError("constructed matrix does not reproduce the lower experiment")
    return matrix


def all_subsets(blocks: Sequence[str]) -> list[frozenset[str]]:
    return [
        frozenset(subset)
        for size in range(len(blocks) + 1)
        for subset in combinations(blocks, size)
    ]


def shapley_values(
    values: Mapping[frozenset[str], Sequence[float]], blocks: Sequence[str]
) -> dict[str, np.ndarray]:
    expected = set(all_subsets(blocks))
    if set(values) != expected:
        raise ValueError("subset lattice mismatch")
    vectors = {key: np.asarray(value, dtype=float) for key, value in values.items()}
    result: dict[str, np.ndarray] = {}
    k = len(blocks)
    for block in blocks:
        total = np.zeros_like(vectors[frozenset()])
        others = [candidate for candidate in blocks if candidate != block]
        for subset in all_subsets(others):
            weight = factorial(len(subset)) * factorial(k - len(subset) - 1) / factorial(k)
            total += weight * (vectors[subset | {block}] - vectors[subset])
        result[block] = total
    return result


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


def stable_records_hash(records: Sequence[Mapping[str, Any]]) -> str:
    payload = json.dumps(json_ready(list(records)), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
