"""Solution-set-aware reversal audit for the finite-scenario CVaR LP."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
from scipy.optimize import linprog

from .cvar_optimizer import solve_cvar_allocation


def _cvar_feasible_system(
    scenarios: np.ndarray,
    costs: np.ndarray,
    total_land: float,
    budget: float,
    alpha: float,
    cvar_limit: float,
    lower: np.ndarray,
    upper: np.ndarray,
    crop_names: List[str],
    rotation_caps: Optional[Dict[str, float]],
    contract_minimums: Optional[Dict[str, float]],
) -> Tuple[np.ndarray, np.ndarray, list[tuple[float | None, float | None]]]:
    scenarios = np.asarray(scenarios, dtype=float)
    n_scenarios, n_crops = scenarios.shape
    n_vars = n_crops + 1 + n_scenarios
    v_idx = n_crops
    q_start = n_crops + 1
    rows: list[np.ndarray] = []
    rhs: list[float] = []

    row = np.zeros(n_vars); row[:n_crops] = 1.0
    rows.append(row); rhs.append(float(total_land))
    row = np.zeros(n_vars); row[:n_crops] = costs
    rows.append(row); rhs.append(float(budget))
    row = np.zeros(n_vars); row[v_idx] = 1.0
    row[q_start:] = 1.0 / ((1.0 - float(alpha)) * n_scenarios)
    rows.append(row); rhs.append(float(cvar_limit))
    for scenario in scenarios:
        row = np.zeros(n_vars)
        row[:n_crops] = -scenario
        row[v_idx] = -1.0
        row[q_start + len(rows) - 3] = -1.0
        rows.append(row); rhs.append(0.0)
    for crop, cap in (rotation_caps or {}).items():
        row = np.zeros(n_vars); row[crop_names.index(crop)] = 1.0
        rows.append(row); rhs.append(float(cap))
    for crop, minimum in (contract_minimums or {}).items():
        row = np.zeros(n_vars); row[crop_names.index(crop)] = -1.0
        rows.append(row); rhs.append(-float(minimum))
    bounds: list[tuple[float | None, float | None]] = [
        (float(lower[i]), float(upper[i])) for i in range(n_crops)
    ]
    bounds.append((None, None))
    bounds.extend((0.0, None) for _ in range(n_scenarios))
    return np.vstack(rows), np.asarray(rhs), bounds


def audit_pairwise_optimal_face(
    profit_scenarios: np.ndarray,
    costs: Iterable[float],
    total_land: float,
    budget: float,
    alpha: float,
    cvar_limit: float,
    lower_bounds: Iterable[float],
    upper_bounds: Iterable[float],
    crop_names: List[str],
    high_rank_crop: str,
    low_rank_crop: str,
    *,
    rotation_caps: Optional[Dict[str, float]] = None,
    contract_minimums: Optional[Dict[str, float]] = None,
    allocation_tolerance: float = 1e-4,
    objective_relative_tolerance: float = 1e-8,
) -> Dict[str, object]:
    """Min/max x_high-x_low over the objective-equivalent CVaR-optimal face."""

    scenarios = np.asarray(profit_scenarios, dtype=float)
    costs_arr = np.asarray(list(costs), dtype=float)
    lower = np.asarray(list(lower_bounds), dtype=float)
    upper = np.asarray(list(upper_bounds), dtype=float)
    primary = solve_cvar_allocation(
        scenarios, costs_arr, total_land, budget, alpha, cvar_limit,
        lower, upper, rotation_caps, crop_names, contract_minimums,
    )
    if primary.allocation is None:
        return {"status": "indeterminate", "solver_status": primary.solver_status}
    means = scenarios.mean(axis=0)
    z_star = float(means @ primary.allocation)
    objective_tolerance = max(abs(z_star), 1.0) * float(objective_relative_tolerance)
    a_ub, b_ub, bounds = _cvar_feasible_system(
        scenarios, costs_arr, total_land, budget, alpha, cvar_limit,
        lower, upper, crop_names, rotation_caps, contract_minimums,
    )
    objective_floor = np.zeros(a_ub.shape[1])
    objective_floor[:len(crop_names)] = -means
    a_ub = np.vstack([a_ub, objective_floor])
    b_ub = np.r_[b_ub, -(z_star - objective_tolerance)]
    direction = np.zeros(a_ub.shape[1])
    direction[crop_names.index(high_rank_crop)] = 1.0
    direction[crop_names.index(low_rank_crop)] = -1.0
    minimum = linprog(direction, A_ub=a_ub, b_ub=b_ub, bounds=bounds, method="highs")
    maximum = linprog(-direction, A_ub=a_ub, b_ub=b_ub, bounds=bounds, method="highs")
    if not minimum.success or not maximum.success:
        return {"status": "indeterminate", "z_star": z_star}
    min_difference = float(direction @ minimum.x)
    max_difference = float(direction @ maximum.x)
    selected_difference = float(
        primary.allocation[crop_names.index(high_rank_crop)]
        - primary.allocation[crop_names.index(low_rank_crop)]
    )
    tol = float(allocation_tolerance)
    if max_difference < -tol:
        classification = "Universal reversal"
    elif min_difference < -tol:
        classification = "Possible reversal"
    else:
        classification = "No reversal"
    return {
        "status": "solved",
        "z_star": z_star,
        "objective_tolerance": objective_tolerance,
        "selected_difference": selected_difference,
        "min_difference": min_difference,
        "max_difference": max_difference,
        "optimal_face_width": max_difference - min_difference,
        "selected_reversal": bool(selected_difference < -tol),
        "possible_reversal": bool(min_difference < -tol),
        "universal_reversal": bool(max_difference < -tol),
        "classification": classification,
    }
