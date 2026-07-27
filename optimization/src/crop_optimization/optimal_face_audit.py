"""Solution-set-aware reversal audit for the finite-scenario CVaR LP."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, lil_matrix, vstack

from .cvar_optimizer import AllocationResult, highs_tolerance_options, solve_cvar_allocation


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
    shared_capacity_constraints: Optional[Mapping[str, Mapping[str, Any]]],
) -> Tuple[csr_matrix, np.ndarray, list[tuple[float | None, float | None]]]:
    scenarios = np.asarray(scenarios, dtype=float)
    n_scenarios, n_crops = scenarios.shape
    n_vars = n_crops + 1 + n_scenarios
    v_idx = n_crops
    q_start = n_crops + 1
    n_extra = (
        len(rotation_caps or {})
        + len(contract_minimums or {})
        + len(shared_capacity_constraints or {})
    )
    matrix = lil_matrix((3 + n_scenarios + n_extra, n_vars), dtype=float)
    rhs = np.zeros(3 + n_scenarios + n_extra, dtype=float)
    row_idx = 0
    matrix[row_idx, :n_crops] = 1.0; rhs[row_idx] = float(total_land); row_idx += 1
    matrix[row_idx, :n_crops] = costs; rhs[row_idx] = float(budget); row_idx += 1
    matrix[row_idx, v_idx] = 1.0
    matrix[row_idx, q_start:] = 1.0 / ((1.0 - float(alpha)) * n_scenarios)
    rhs[row_idx] = float(cvar_limit); row_idx += 1
    for scenario_idx, scenario in enumerate(scenarios):
        matrix[row_idx, :n_crops] = -scenario
        matrix[row_idx, v_idx] = -1.0
        matrix[row_idx, q_start + scenario_idx] = -1.0
        row_idx += 1
    for crop, cap in (rotation_caps or {}).items():
        matrix[row_idx, crop_names.index(crop)] = 1.0
        rhs[row_idx] = float(cap); row_idx += 1
    for crop, minimum in (contract_minimums or {}).items():
        matrix[row_idx, crop_names.index(crop)] = -1.0
        rhs[row_idx] = -float(minimum); row_idx += 1
    for spec in (shared_capacity_constraints or {}).values():
        raw = spec["coefficients"]
        coefficients = (
            np.asarray([float(raw.get(crop, 0.0)) for crop in crop_names])
            if isinstance(raw, Mapping)
            else np.asarray(list(raw), dtype=float)
        )
        matrix[row_idx, :n_crops] = coefficients
        rhs[row_idx] = float(spec["capacity"]); row_idx += 1
    bounds: list[tuple[float | None, float | None]] = [
        (float(lower[i]), float(upper[i])) for i in range(n_crops)
    ]
    bounds.append((None, None))
    bounds.extend((0.0, None) for _ in range(n_scenarios))
    return matrix.tocsr(), rhs, bounds


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
    shared_capacity_constraints: Optional[Mapping[str, Mapping[str, Any]]] = None,
    allocation_tolerance: float = 1e-4,
    objective_relative_tolerance: float = 1e-8,
    primary_result: Optional[AllocationResult] = None,
    solver_method: str = "highs",
) -> Dict[str, object]:
    """Min/max x_high-x_low over the objective-equivalent CVaR-optimal face."""

    scenarios = np.asarray(profit_scenarios, dtype=float)
    costs_arr = np.asarray(list(costs), dtype=float)
    lower = np.asarray(list(lower_bounds), dtype=float)
    upper = np.asarray(list(upper_bounds), dtype=float)
    primary = primary_result or solve_cvar_allocation(
        scenarios, costs_arr, total_land, budget, alpha, cvar_limit,
        lower, upper, rotation_caps, crop_names, contract_minimums,
        solver_method=solver_method,
        shared_capacity_constraints=shared_capacity_constraints,
    )
    if primary.allocation is None:
        return {"status": "indeterminate", "solver_status": primary.solver_status}
    means = scenarios.mean(axis=0)
    z_star = float(means @ primary.allocation)
    objective_tolerance = max(abs(z_star), 1.0) * float(objective_relative_tolerance)
    a_ub, b_ub, bounds = _cvar_feasible_system(
        scenarios, costs_arr, total_land, budget, alpha, cvar_limit,
        lower, upper, crop_names, rotation_caps, contract_minimums,
        shared_capacity_constraints,
    )
    objective_floor = np.zeros(a_ub.shape[1])
    objective_floor[:len(crop_names)] = -means
    a_ub = vstack([a_ub, csr_matrix(objective_floor.reshape(1, -1))], format="csr")
    b_ub = np.r_[b_ub, -(z_star - objective_tolerance)]
    direction = np.zeros(a_ub.shape[1])
    direction[crop_names.index(high_rank_crop)] = 1.0
    direction[crop_names.index(low_rank_crop)] = -1.0
    options = highs_tolerance_options(solver_method)
    minimum = linprog(
        direction, A_ub=a_ub, b_ub=b_ub, bounds=bounds,
        method=solver_method, options=options,
    )
    maximum = linprog(
        -direction, A_ub=a_ub, b_ub=b_ub, bounds=bounds,
        method=solver_method, options=options,
    )
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


def audit_reversal_optimal_face(
    profit_scenarios: np.ndarray,
    costs: Iterable[float],
    total_land: float,
    budget: float,
    alpha: float,
    cvar_limit: float,
    lower_bounds: Iterable[float],
    upper_bounds: Iterable[float],
    crop_names: List[str],
    scores: Iterable[float],
    *,
    rotation_caps: Optional[Dict[str, float]] = None,
    contract_minimums: Optional[Dict[str, float]] = None,
    shared_capacity_constraints: Optional[Mapping[str, Mapping[str, Any]]] = None,
    score_tolerance: float = 1e-6,
    allocation_tolerance: float = 1e-4,
    near_zero_tolerance: float = 1e-4,
    objective_relative_tolerance: float = 1e-8,
    primary_result: Optional[AllocationResult] = None,
    solver_method: str = "highs",
) -> Dict[str, object]:
    """Audit all repaired reversal definitions on the complete optimal face.

    Pairwise and complete-rank statements use ordering tolerance.  Strong
    reversal retains the supervisor-Draft exclusion definition and therefore
    uses the separate near-zero tolerance.
    """

    scenarios = np.asarray(profit_scenarios, dtype=float)
    costs_arr = np.asarray(list(costs), dtype=float)
    lower = np.asarray(list(lower_bounds), dtype=float)
    upper = np.asarray(list(upper_bounds), dtype=float)
    score_arr = np.asarray(list(scores), dtype=float)
    primary = primary_result or solve_cvar_allocation(
        scenarios, costs_arr, total_land, budget, alpha, cvar_limit,
        lower, upper, rotation_caps, crop_names, contract_minimums,
        solver_method=solver_method,
        shared_capacity_constraints=shared_capacity_constraints,
    )
    if primary.allocation is None:
        return {"status": "indeterminate", "solver_status": primary.solver_status}

    means = scenarios.mean(axis=0)
    z_star = float(means @ primary.allocation)
    objective_tolerance = max(abs(z_star), 1.0) * float(objective_relative_tolerance)
    a_ub, b_ub, bounds = _cvar_feasible_system(
        scenarios, costs_arr, total_land, budget, alpha, cvar_limit,
        lower, upper, crop_names, rotation_caps, contract_minimums,
        shared_capacity_constraints,
    )
    objective_floor = np.zeros(a_ub.shape[1])
    objective_floor[:len(crop_names)] = -means
    face_matrix = vstack(
        [a_ub, csr_matrix(objective_floor.reshape(1, -1))], format="csr"
    )
    face_rhs = np.r_[b_ub, -(z_star - objective_tolerance)]
    options = highs_tolerance_options(solver_method)
    zero_objective = np.zeros(face_matrix.shape[1])

    def optimize(direction: np.ndarray, maximize: bool = False):
        return linprog(
            -direction if maximize else direction,
            A_ub=face_matrix,
            b_ub=face_rhs,
            bounds=bounds,
            method=solver_method,
            options=options,
        )

    coordinate_min: Dict[int, float] = {}
    coordinate_max: Dict[int, float] = {}
    for crop_index in range(len(crop_names)):
        direction = np.zeros(face_matrix.shape[1])
        direction[crop_index] = 1.0
        minimum = optimize(direction)
        maximum = optimize(direction, maximize=True)
        if not minimum.success or not maximum.success:
            return {"status": "indeterminate", "z_star": z_star}
        coordinate_min[crop_index] = float(minimum.x[crop_index])
        coordinate_max[crop_index] = float(maximum.x[crop_index])

    ranked_pairs = []
    order = np.argsort(-score_arr)
    for left in range(len(order)):
        for right in range(left + 1, len(order)):
            high = int(order[left])
            low = int(order[right])
            if score_arr[high] - score_arr[low] <= float(score_tolerance):
                continue
            ranked_pairs.append((high, low))

    pair_rows: Dict[str, Dict[str, object]] = {}
    for high, low in ranked_pairs:
        direction = np.zeros(face_matrix.shape[1])
        direction[high] = 1.0
        direction[low] = -1.0
        minimum = optimize(direction)
        maximum = optimize(direction, maximize=True)
        if not minimum.success or not maximum.success:
            return {"status": "indeterminate", "z_star": z_star}
        minimum_difference = float(direction @ minimum.x)
        maximum_difference = float(direction @ maximum.x)
        selected_difference = float(primary.allocation[high] - primary.allocation[low])

        # Is there one face point satisfying exclusion and positive lower crop?
        strong_rows = lil_matrix((2, face_matrix.shape[1]), dtype=float)
        strong_rows[0, high] = 1.0
        strong_rows[1, low] = -1.0
        strong_matrix = vstack([face_matrix, strong_rows.tocsr()], format="csr")
        strong_rhs = np.r_[
            face_rhs,
            float(near_zero_tolerance),
            -(float(near_zero_tolerance) + float(allocation_tolerance)),
        ]
        strong_feasible = linprog(
            zero_objective,
            A_ub=strong_matrix,
            b_ub=strong_rhs,
            bounds=bounds,
            method=solver_method,
            options=options,
        ).success
        key = f"{crop_names[high]}_over_{crop_names[low]}".replace(" ", "_")
        pair_rows[key] = {
            "selected_difference": selected_difference,
            "min_difference": minimum_difference,
            "max_difference": maximum_difference,
            "selected_reversal": bool(
                selected_difference < -float(allocation_tolerance)
            ),
            "possible_reversal": bool(
                minimum_difference < -float(allocation_tolerance)
            ),
            "universal_reversal": bool(
                maximum_difference < -float(allocation_tolerance)
            ),
            "possible_strong_reversal": bool(strong_feasible),
            "universal_strong_reversal": bool(
                coordinate_max[high] <= float(near_zero_tolerance)
                and coordinate_min[low]
                > float(near_zero_tolerance) + float(allocation_tolerance)
            ),
        }

    top = int(order[0])
    top_pairs = [(high, low) for high, low in ranked_pairs if high == top]
    complete_rows = lil_matrix((len(top_pairs), face_matrix.shape[1]), dtype=float)
    for row_index, (_high, low) in enumerate(top_pairs):
        complete_rows[row_index, top] = 1.0
        complete_rows[row_index, low] = -1.0
    complete_matrix = vstack([face_matrix, complete_rows.tocsr()], format="csr")
    complete_rhs = np.r_[
        face_rhs, np.full(len(top_pairs), -float(allocation_tolerance))
    ]
    complete_feasible = bool(top_pairs) and linprog(
        zero_objective,
        A_ub=complete_matrix,
        b_ub=complete_rhs,
        bounds=bounds,
        method=solver_method,
        options=options,
    ).success
    universal_complete = bool(top_pairs) and all(
        pair_rows[
            f"{crop_names[high]}_over_{crop_names[low]}".replace(" ", "_")
        ]["universal_reversal"]
        for high, low in top_pairs
    )
    widths = {
        crop_names[index]: coordinate_max[index] - coordinate_min[index]
        for index in range(len(crop_names))
    }
    return {
        "status": "solved",
        "z_star": z_star,
        "objective_tolerance": objective_tolerance,
        "possible_pairwise_reversal": any(
            bool(row["possible_reversal"]) for row in pair_rows.values()
        ),
        "universal_pairwise_reversal": any(
            bool(row["universal_reversal"]) for row in pair_rows.values()
        ),
        "possible_complete_rank_reversal": bool(complete_feasible),
        "universal_complete_rank_reversal": bool(universal_complete),
        "possible_strong_reversal": any(
            bool(row["possible_strong_reversal"]) for row in pair_rows.values()
        ),
        "universal_strong_reversal": any(
            bool(row["universal_strong_reversal"]) for row in pair_rows.values()
        ),
        "multiple_optima": bool(
            max(widths.values(), default=0.0) > float(allocation_tolerance)
        ),
        "top_crop": crop_names[top],
        "top_min_allocation": coordinate_min[top],
        "top_max_allocation": coordinate_max[top],
        "coordinate_widths": widths,
        "pair_results": pair_rows,
    }
