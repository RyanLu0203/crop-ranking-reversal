"""Benchmark allocation policies for comparison with CVaR optimization."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional

import numpy as np
import pandas as pd
from scipy.optimize import linprog, minimize

from .cvar_optimizer import solve_cvar_allocation, solve_expected_profit_allocation
from .evaluation import allocation_metrics


def _array_by_crop(mapping: Dict[str, float], crop_names: List[str]) -> np.ndarray:
    return np.asarray([mapping[crop] for crop in crop_names], dtype=float)


def repair_allocation_to_feasible(
    target_allocation: Iterable[float],
    costs: Iterable[float],
    total_acres: float,
    budget: float,
    lower_bounds: Iterable[float],
    upper_bounds: Iterable[float],
    rotation_caps: Optional[Dict[str, float]],
    crop_names: List[str],
    contract_minimums: Optional[Dict[str, float]] = None,
    shared_capacity_constraints: Optional[Mapping[str, Mapping[str, Any]]] = None,
    *,
    tie_break_weights: Optional[Iterable[float]] = None,
    objective_tolerance: float = 1e-10,
) -> Dict[str, object]:
    """Find an L1-closest full-investment allocation with a declared tie-break."""

    target = np.asarray(list(target_allocation), dtype=float)
    costs_arr = np.asarray(list(costs), dtype=float)
    lb = np.asarray(list(lower_bounds), dtype=float)
    ub = np.asarray(list(upper_bounds), dtype=float)
    n = target.size

    # Variables: x, d_plus, d_minus. x - target = d_plus - d_minus.
    c = np.r_[np.zeros(n), np.ones(n), np.ones(n)]
    a_eq = []
    b_eq = []
    for idx in range(n):
        row = np.zeros(3 * n)
        row[idx] = 1.0
        row[n + idx] = -1.0
        row[2 * n + idx] = 1.0
        a_eq.append(row)
        b_eq.append(target[idx])

    # Suitability proportional allocation is a full-acreage prescription;
    # repair keeps full acreage if the stated constraints allow it.
    row = np.zeros(3 * n)
    row[:n] = 1.0
    a_eq.append(row)
    b_eq.append(float(total_acres))

    a_ub = []
    b_ub = []
    row = np.zeros(3 * n)
    row[:n] = costs_arr
    a_ub.append(row)
    b_ub.append(float(budget))
    if rotation_caps:
        for crop, cap in rotation_caps.items():
            row = np.zeros(3 * n)
            row[crop_names.index(crop)] = 1.0
            a_ub.append(row)
            b_ub.append(float(cap))
    if contract_minimums:
        for crop, minimum in contract_minimums.items():
            row = np.zeros(3 * n)
            row[crop_names.index(crop)] = -1.0
            a_ub.append(row)
            b_ub.append(-float(minimum))
    if shared_capacity_constraints:
        for spec in shared_capacity_constraints.values():
            raw = spec["coefficients"]
            coefficients = (
                np.asarray([float(raw.get(crop, 0.0)) for crop in crop_names])
                if isinstance(raw, Mapping)
                else np.asarray(list(raw), dtype=float)
            )
            row = np.zeros(3 * n)
            row[:n] = coefficients
            a_ub.append(row)
            b_ub.append(float(spec["capacity"]))

    bounds = [(float(lb[i]), float(ub[i])) for i in range(n)]
    bounds.extend((0.0, None) for _ in range(2 * n))
    result = linprog(
        c,
        A_ub=np.vstack(a_ub) if a_ub else None,
        b_ub=np.asarray(b_ub) if b_ub else None,
        A_eq=np.vstack(a_eq),
        b_eq=np.asarray(b_eq),
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        return {"status": "infeasible_or_failed", "message": result.message, "allocation": target}
    l1_optimum = float(c @ result.x)
    weights = np.asarray(
        list(tie_break_weights) if tie_break_weights is not None
        else np.arange(1.0, n + 1.0),
        dtype=float,
    )
    if weights.shape != (n,):
        raise ValueError("tie_break_weights must match the allocation dimension")
    distance_row = c.reshape(1, -1)
    tie_objective = np.r_[weights, np.zeros(2 * n)]
    tie_result = linprog(
        tie_objective,
        A_ub=np.vstack([
            np.vstack(a_ub) if a_ub else np.empty((0, 3 * n)),
            distance_row,
        ]),
        b_ub=np.r_[
            np.asarray(b_ub) if b_ub else np.empty(0),
            l1_optimum + float(objective_tolerance),
        ],
        A_eq=np.vstack(a_eq),
        b_eq=np.asarray(b_eq),
        bounds=bounds,
        method="highs",
    )
    chosen = tie_result if tie_result.success else result
    allocation = np.maximum(chosen.x[:n], 0.0)
    return {
        "status": "projected",
        "message": chosen.message,
        "allocation": allocation,
        "projection_method": "l1_lexicographic",
        "projection_distance_l1": float(np.abs(allocation - target).sum()),
        "projection_distance_l2": float(np.linalg.norm(allocation - target)),
        "tie_break_rule": (
            "minimize crop-order weighted allocation on the L1-optimal face"
        ),
        "tie_break_weights": weights,
    }


def euclidean_projection_to_feasible(
    target_allocation: Iterable[float],
    costs: Iterable[float],
    total_acres: float,
    budget: float,
    lower_bounds: Iterable[float],
    upper_bounds: Iterable[float],
    rotation_caps: Optional[Dict[str, float]],
    crop_names: List[str],
    contract_minimums: Optional[Dict[str, float]] = None,
    shared_capacity_constraints: Optional[Mapping[str, Mapping[str, Any]]] = None,
    *,
    objective_tolerance: float = 1e-10,
) -> Dict[str, object]:
    """Unique Euclidean projection onto the declared operational comparison set."""

    target = np.asarray(list(target_allocation), dtype=float)
    costs_arr = np.asarray(list(costs), dtype=float)
    lower = np.asarray(list(lower_bounds), dtype=float)
    upper = np.asarray(list(upper_bounds), dtype=float)
    start_result = repair_allocation_to_feasible(
        target,
        costs_arr,
        total_acres,
        budget,
        lower,
        upper,
        rotation_caps,
        crop_names,
        contract_minimums,
        shared_capacity_constraints,
        objective_tolerance=objective_tolerance,
    )
    if start_result["status"] == "infeasible_or_failed":
        return start_result

    constraints: list[dict[str, object]] = [
        {
            "type": "eq",
            "fun": lambda allocation: float(
                np.sum(allocation) - float(total_acres)
            ),
        },
        {
            "type": "ineq",
            "fun": lambda allocation: float(
                float(budget) - costs_arr @ allocation
            ),
        },
    ]
    for crop, cap in (rotation_caps or {}).items():
        index = crop_names.index(crop)
        constraints.append({
            "type": "ineq",
            "fun": lambda allocation, index=index, cap=float(cap): float(
                cap - allocation[index]
            ),
        })
    for crop, minimum in (contract_minimums or {}).items():
        index = crop_names.index(crop)
        constraints.append({
            "type": "ineq",
            "fun": lambda allocation, index=index, minimum=float(minimum): float(
                allocation[index] - minimum
            ),
        })
    for capacity_spec in (shared_capacity_constraints or {}).values():
        raw = capacity_spec["coefficients"]
        coefficients = (
            np.asarray([float(raw.get(crop, 0.0)) for crop in crop_names])
            if isinstance(raw, Mapping)
            else np.asarray(list(raw), dtype=float)
        )
        capacity = float(capacity_spec["capacity"])
        constraints.append({
            "type": "ineq",
            "fun": (
                lambda allocation, coefficients=coefficients, capacity=capacity:
                float(capacity - coefficients @ allocation)
            ),
        })

    result = minimize(
        lambda allocation: float(
            0.5 * np.square(allocation - target).sum()
        ),
        x0=np.asarray(start_result["allocation"], dtype=float),
        method="SLSQP",
        bounds=[
            (float(lower[index]), float(upper[index]))
            for index in range(target.size)
        ],
        constraints=constraints,
        options={
            "maxiter": 2000,
            "ftol": float(objective_tolerance),
        },
    )
    if not result.success:
        return {
            "status": "infeasible_or_failed",
            "message": result.message,
            "allocation": target,
        }
    allocation = np.maximum(np.asarray(result.x, dtype=float), 0.0)
    return {
        "status": "projected",
        "message": result.message,
        "allocation": allocation,
        "projection_method": "euclidean_l2",
        "projection_distance_l1": float(np.abs(allocation - target).sum()),
        "projection_distance_l2": float(np.linalg.norm(allocation - target)),
        "tie_break_rule": "not required: strictly convex objective",
    }


def suitability_proportional_policy(
    suitability_scores: Iterable[float],
    total_acres: float,
    costs: Iterable[float],
    budget: float,
    lower_bounds: Iterable[float],
    upper_bounds: Iterable[float],
    rotation_caps: Optional[Dict[str, float]],
    crop_names: List[str],
    contract_minimums: Optional[Dict[str, float]] = None,
    shared_capacity_constraints: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> Dict[str, object]:
    scores = np.asarray(list(suitability_scores), dtype=float)
    target = total_acres * scores / scores.sum()
    repaired = repair_allocation_to_feasible(
        target,
        costs,
        total_acres,
        budget,
        lower_bounds,
        upper_bounds,
        rotation_caps,
        crop_names,
        contract_minimums,
        shared_capacity_constraints,
    )
    repaired["target_allocation"] = target
    return repaired


def mean_variance_policy(
    profit_scenarios: np.ndarray,
    costs: Iterable[float],
    total_acres: float,
    budget: float,
    lower_bounds: Iterable[float],
    upper_bounds: Iterable[float],
    rotation_caps: Optional[Dict[str, float]],
    crop_names: List[str],
    gamma: float,
    start: Optional[np.ndarray] = None,
    contract_minimums: Optional[Dict[str, float]] = None,
    shared_capacity_constraints: Optional[Mapping[str, Mapping[str, Any]]] = None,
    full_investment: bool = False,
) -> Dict[str, object]:
    means = profit_scenarios.mean(axis=0)
    cov = np.cov(profit_scenarios, rowvar=False)
    costs_arr = np.asarray(list(costs), dtype=float)
    lb = np.asarray(list(lower_bounds), dtype=float)
    ub = np.asarray(list(upper_bounds), dtype=float)
    n = len(means)

    if start is None:
        start_result = solve_expected_profit_allocation(
            means,
            costs_arr,
            total_acres,
            budget,
            lb,
            ub,
            rotation_caps,
            crop_names,
            contract_minimums,
            shared_capacity_constraints,
        )
        start = start_result.allocation if start_result.allocation is not None else np.maximum(lb, total_acres / n)

    def objective(x: np.ndarray) -> float:
        return float(-(means @ x) + gamma * (x @ cov @ x))

    constraints = [
        {"type": "ineq", "fun": lambda x: total_acres - np.sum(x)},
        {"type": "ineq", "fun": lambda x: budget - costs_arr @ x},
    ]
    if full_investment:
        constraints[0] = {
            "type": "eq",
            "fun": lambda x: np.sum(x) - total_acres,
        }
    if rotation_caps:
        for crop, cap in rotation_caps.items():
            idx = crop_names.index(crop)
            constraints.append({"type": "ineq", "fun": lambda x, idx=idx, cap=cap: cap - x[idx]})
    if contract_minimums:
        for crop, minimum in contract_minimums.items():
            idx = crop_names.index(crop)
            constraints.append({
                "type": "ineq",
                "fun": lambda x, idx=idx, minimum=minimum: x[idx] - float(minimum),
            })
    if shared_capacity_constraints:
        for spec in shared_capacity_constraints.values():
            raw = spec["coefficients"]
            coefficients = (
                np.asarray([float(raw.get(crop, 0.0)) for crop in crop_names])
                if isinstance(raw, Mapping)
                else np.asarray(list(raw), dtype=float)
            )
            capacity = float(spec["capacity"])
            constraints.append({
                "type": "ineq",
                "fun": lambda x, coefficients=coefficients, capacity=capacity:
                    capacity - coefficients @ x,
            })

    result = minimize(
        objective,
        x0=np.asarray(start, dtype=float),
        method="SLSQP",
        bounds=[(float(lb[i]), float(ub[i])) for i in range(n)],
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-8},
    )
    if not result.success:
        return {"status": "failed", "message": result.message, "allocation": np.asarray(start, dtype=float)}
    return {"status": "optimal", "message": result.message, "allocation": np.maximum(result.x, 0.0)}


def run_policy_comparison(
    profit_scenarios: np.ndarray,
    config: Dict[str, object],
) -> pd.DataFrame:
    crop_names = list(config["crop_names"])
    costs = _array_by_crop(config["costs"], crop_names)
    means = profit_scenarios.mean(axis=0)
    suitability = _array_by_crop(config["suitability_scores"], crop_names)
    lower_bounds = _array_by_crop(config["lower_bounds"], crop_names)
    upper_bounds = _array_by_crop(config["upper_bounds"], crop_names)
    rotation_caps = dict(config.get("rotation_caps") or {})
    contract_minimums = dict(config.get("contract_minimums") or {})
    shared_capacity_constraints = dict(config.get("shared_capacity_constraints") or {})
    total_acres = float(config["total_acres"])
    budget = float(config["budget"])
    alpha = float(config["alpha"])
    cvar_limit = float(config["cvar_limit"])

    policies: Dict[str, Dict[str, object]] = {}
    policies["SU"] = suitability_proportional_policy(
        suitability,
        total_acres,
        costs,
        budget,
        lower_bounds,
        upper_bounds,
        rotation_caps,
        crop_names,
        contract_minimums,
        shared_capacity_constraints,
    )
    eo = solve_expected_profit_allocation(
        means,
        costs,
        total_acres,
        budget,
        lower_bounds,
        upper_bounds,
        rotation_caps,
        crop_names,
        contract_minimums,
        shared_capacity_constraints,
    )
    policies["EO"] = {"status": eo.status, "message": eo.message, "allocation": eo.allocation}
    policies["MV"] = mean_variance_policy(
        profit_scenarios,
        costs,
        total_acres,
        budget,
        lower_bounds,
        upper_bounds,
        rotation_caps,
        crop_names,
        gamma=float(config.get("mean_variance_gamma", 1e-5)),
        start=eo.allocation,
        contract_minimums=contract_minimums,
        shared_capacity_constraints=shared_capacity_constraints,
    )
    cvar = solve_cvar_allocation(
        profit_scenarios,
        costs,
        total_acres,
        budget,
        alpha,
        cvar_limit,
        lower_bounds,
        upper_bounds,
        rotation_caps,
        crop_names,
        contract_minimums,
        shared_capacity_constraints=shared_capacity_constraints,
    )
    policies["CVaR"] = {"status": cvar.status, "message": cvar.message, "allocation": cvar.allocation}

    rows = []
    for policy_name, policy in policies.items():
        allocation = policy.get("allocation")
        if allocation is None:
            row = {"policy": policy_name, "status": policy["status"], "message": policy["message"]}
        else:
            row = allocation_metrics(
                allocation,
                profit_scenarios,
                costs,
                total_acres,
                budget,
                alpha,
                cvar_limit,
                crop_names,
                lower_bounds,
                upper_bounds,
                rotation_caps,
                contract_minimums,
                shared_capacity_constraints,
            )
            row.update({"policy": policy_name, "status": policy["status"], "message": str(policy["message"])})
        rows.append(row)

    df = pd.DataFrame(rows)
    violation_columns = [
        column for column in (
            "cvar_violation", "budget_violation", "acreage_violation",
            "lower_bound_violation", "upper_bound_violation",
            "rotation_violation", "contract_violation",
            "shared_capacity_violation",
        ) if column in df.columns
    ]
    feasible_mask = ~df[violation_columns].fillna(True).any(axis=1)
    feasible = df.loc[feasible_mask]
    best_feasible_profit = feasible["expected_profit"].max() if not feasible.empty else df["expected_profit"].max()
    df["regret_vs_best_feasible"] = np.nan
    df.loc[feasible_mask, "regret_vs_best_feasible"] = best_feasible_profit - df.loc[
        feasible_mask, "expected_profit"
    ]
    ordered_columns = [
        "policy",
        "status",
        "acres_Corn",
        "acres_Soybean",
        "acres_Winter Wheat",
        "expected_profit",
        "cvar_loss",
        "var_loss",
        "worst_decile_profit",
        "cvar_violation",
        "budget_violation",
        "acreage_violation",
        "lower_bound_violation",
        "upper_bound_violation",
        "rotation_violation",
        "contract_violation",
        "shared_capacity_violation",
        "budget_usage",
        "acreage_usage",
        "regret_vs_best_feasible",
    ]
    return df[[col for col in ordered_columns if col in df.columns]]
