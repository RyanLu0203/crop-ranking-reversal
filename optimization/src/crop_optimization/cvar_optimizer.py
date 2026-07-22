"""CVaR-constrained land-allocation optimizer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

from .evaluation import constraint_diagnostics, empirical_var_cvar_losses, portfolio_profit


def highs_tolerance_options(method: str) -> Dict[str, float]:
    """Numerical options needed to honor the frozen direct-CVaR tolerances."""

    options: Dict[str, float] = {
        "primal_feasibility_tolerance": 1e-9,
        "dual_feasibility_tolerance": 1e-9,
    }
    if str(method) in {"highs", "highs-ipm"}:
        options["ipm_optimality_tolerance"] = 1e-10
    return options


@dataclass
class AllocationResult:
    allocation: Optional[np.ndarray]
    expected_profit: Optional[float]
    cvar_loss: Optional[float]
    var_loss: Optional[float]
    status: str
    solver_status: int
    message: str
    diagnostics: Dict[str, Any]

    def to_dict(self, crop_names: Optional[List[str]] = None) -> Dict[str, Any]:
        row: Dict[str, Any] = {
            "status": self.status,
            "solver_status": self.solver_status,
            "message": self.message,
            "expected_profit": self.expected_profit,
            "cvar_loss": self.cvar_loss,
            "var_loss": self.var_loss,
        }
        if self.allocation is not None:
            for idx, value in enumerate(self.allocation):
                name = crop_names[idx] if crop_names else f"crop_{idx + 1}"
                row[f"acres_{name}"] = float(value)
        row.update(self.diagnostics)
        return row


def solve_cvar_allocation(
    profit_scenarios: np.ndarray,
    costs: Iterable[float],
    total_acres: float,
    budget: float,
    alpha: float,
    cvar_limit: float,
    lower_bounds: Iterable[float],
    upper_bounds: Iterable[float],
    rotation_caps: Optional[Dict[str, float]] = None,
    crop_names: Optional[List[str]] = None,
    contract_minimums: Optional[Dict[str, float]] = None,
    solver_method: str = "highs",
) -> AllocationResult:
    """Solve the CVaR-constrained allocation problem with scipy linprog.

    CVaR is imposed on portfolio losses:

        portfolio_profit_s = sum_i x_i * profit_scenarios[s, i]
        portfolio_loss_s = -portfolio_profit_s

    The linear constraint uses the Rockafellar-Uryasev auxiliary variables
    v and q_s with q_s >= loss_s - v.
    """

    scenarios = np.asarray(profit_scenarios, dtype=float)
    if scenarios.ndim != 2:
        raise ValueError("profit_scenarios must be an S x n matrix.")
    n_scenarios, n_crops = scenarios.shape
    costs_arr = np.asarray(list(costs), dtype=float)
    lb = np.asarray(list(lower_bounds), dtype=float)
    ub = np.asarray(list(upper_bounds), dtype=float)
    crop_names = crop_names or [f"Crop {i + 1}" for i in range(n_crops)]

    if costs_arr.size != n_crops or lb.size != n_crops or ub.size != n_crops:
        raise ValueError("costs, lower_bounds, and upper_bounds must match scenario columns.")
    if n_scenarios == 0 or not np.isfinite(scenarios).all():
        raise ValueError("profit_scenarios must be finite and non-empty.")
    if not 0.0 < float(alpha) < 1.0:
        raise ValueError("alpha must be strictly between zero and one.")
    if not np.isfinite(costs_arr).all() or np.any(costs_arr < 0):
        raise ValueError("costs must be finite and nonnegative.")
    if not np.isfinite(lb).all() or not np.isfinite(ub).all() or np.any(lb > ub):
        raise ValueError("bounds must be finite and lower_bounds <= upper_bounds.")
    if float(total_acres) < 0 or not np.isfinite(total_acres) or not np.isfinite(budget):
        raise ValueError("total_acres and budget must be finite; total_acres must be nonnegative.")

    n_vars = n_crops + 1 + n_scenarios
    v_idx = n_crops
    q_start = n_crops + 1

    mean_profit = scenarios.mean(axis=0)
    objective = np.zeros(n_vars)
    objective[:n_crops] = -mean_profit
    # v and q are feasibility auxiliaries. A small weighted penalty would
    # alter the primary expected-profit objective rather than implement an
    # exact lexicographic tie-break, so their coefficients remain zero.

    n_extra = len(rotation_caps or {}) + len(contract_minimums or {})
    a_ub = lil_matrix((3 + n_scenarios + n_extra, n_vars), dtype=float)
    b_ub = np.zeros(3 + n_scenarios + n_extra, dtype=float)
    constraint_names: List[str] = []
    row_idx = 0

    a_ub[row_idx, :n_crops] = 1.0
    b_ub[row_idx] = float(total_acres)
    constraint_names.append("land")
    row_idx += 1

    a_ub[row_idx, :n_crops] = costs_arr
    b_ub[row_idx] = float(budget)
    constraint_names.append("budget")
    row_idx += 1

    a_ub[row_idx, v_idx] = 1.0
    a_ub[row_idx, q_start:] = 1.0 / max((1.0 - alpha) * n_scenarios, 1e-12)
    b_ub[row_idx] = float(cvar_limit)
    constraint_names.append("cvar")
    row_idx += 1

    # q_s >= loss_s - v, where loss_s = -profit_s @ x.
    # Equivalent: (-profit_s) x - v - q_s <= 0.
    for scenario_idx in range(n_scenarios):
        a_ub[row_idx, :n_crops] = -scenarios[scenario_idx, :]
        a_ub[row_idx, v_idx] = -1.0
        a_ub[row_idx, q_start + scenario_idx] = -1.0
        constraint_names.append(f"tail_scenario_{scenario_idx}")
        row_idx += 1

    if rotation_caps:
        for crop, cap in rotation_caps.items():
            if crop not in crop_names:
                raise ValueError(f"rotation cap crop {crop!r} is not in crop_names.")
            a_ub[row_idx, crop_names.index(crop)] = 1.0
            b_ub[row_idx] = float(cap)
            constraint_names.append(f"rotation_{crop}")
            row_idx += 1

    if contract_minimums:
        for crop, minimum in contract_minimums.items():
            if crop not in crop_names:
                raise ValueError(f"contract crop {crop!r} is not in crop_names.")
            idx = crop_names.index(crop)
            minimum = float(minimum)
            if minimum < 0 or minimum > ub[idx]:
                raise ValueError(f"invalid contract minimum for {crop!r}.")
            a_ub[row_idx, idx] = -1.0
            b_ub[row_idx] = -minimum
            constraint_names.append(f"contract_{crop}")
            row_idx += 1

    bounds = [(float(lb[i]), float(ub[i])) for i in range(n_crops)]
    bounds.append((None, None))
    bounds.extend((0.0, None) for _ in range(n_scenarios))

    a_ub_arr = a_ub.tocsr()
    result = linprog(
        objective,
        A_ub=a_ub_arr,
        b_ub=b_ub,
        bounds=bounds,
        method=str(solver_method),
        options=highs_tolerance_options(str(solver_method)),
    )

    if not result.success:
        diagnostics = {
            "minimum_required_budget_at_lower_bounds": float(costs_arr @ lb),
            "lower_bound_acres": float(lb.sum()),
            "total_acres": float(total_acres),
            "budget": float(budget),
            "cvar_limit": float(cvar_limit),
        }
        return AllocationResult(
            allocation=None,
            expected_profit=None,
            cvar_loss=None,
            var_loss=None,
            status="infeasible_or_failed",
            solver_status=int(result.status),
            message=str(result.message),
            diagnostics=diagnostics,
        )

    allocation = np.maximum(result.x[:n_crops], 0.0)
    profits = portfolio_profit(scenarios, allocation)
    losses = -profits
    var_loss, cvar_loss = empirical_var_cvar_losses(losses, alpha)
    diagnostics = constraint_diagnostics(
        allocation,
        costs_arr,
        total_acres,
        budget,
        lb,
        ub,
        rotation_caps,
        crop_names,
        cvar_loss,
        cvar_limit,
    )
    b_ub_arr = b_ub
    constraint_slacks = b_ub_arr - a_ub_arr @ result.x
    active_tol = 1e-4
    shadow_prices = {}
    raw_marginals = {}
    if hasattr(result, "ineqlin") and getattr(result.ineqlin, "marginals", None) is not None:
        for name, marginal in zip(constraint_names, result.ineqlin.marginals):
            if name.startswith("tail_scenario_"):
                continue
            raw_marginals[f"raw_dual_{name}"] = float(marginal)
            # scipy minimizes -profit, so the economic shadow price for a
            # maximization-style <= resource is the negative marginal.
            shadow_prices[f"shadow_price_{name}"] = float(-marginal)
    bounds_diagnostics: Dict[str, Any] = {}
    lower_marginals = getattr(getattr(result, "lower", None), "marginals", None)
    upper_marginals = getattr(getattr(result, "upper", None), "marginals", None)
    for idx, crop in enumerate(crop_names):
        lower_slack = allocation[idx] - lb[idx]
        upper_slack = ub[idx] - allocation[idx]
        bounds_diagnostics[f"lower_bound_slack_{crop}"] = float(lower_slack)
        bounds_diagnostics[f"upper_bound_slack_{crop}"] = float(upper_slack)
        bounds_diagnostics[f"lower_bound_binds_{crop}"] = bool(lower_slack <= active_tol)
        bounds_diagnostics[f"upper_bound_binds_{crop}"] = bool(upper_slack <= active_tol)
        if lower_marginals is not None:
            bounds_diagnostics[f"raw_dual_lower_bound_{crop}"] = float(lower_marginals[idx])
            bounds_diagnostics[f"shadow_price_lower_bound_{crop}"] = float(-lower_marginals[idx])
        if upper_marginals is not None:
            bounds_diagnostics[f"raw_dual_upper_bound_{crop}"] = float(upper_marginals[idx])
            bounds_diagnostics[f"shadow_price_upper_bound_{crop}"] = float(-upper_marginals[idx])

    named_slacks = dict(zip(constraint_names, constraint_slacks))
    land_slack = float(named_slacks.get("land", np.nan))
    budget_slack = float(named_slacks.get("budget", np.nan))
    optimizer_cvar_expression = float(
        result.x[v_idx] + result.x[q_start:].sum() / max((1.0 - alpha) * n_scenarios, 1e-12)
    )
    optimizer_cvar_slack = float(cvar_limit - optimizer_cvar_expression)
    empirical_cvar_slack = float(cvar_limit - cvar_loss)
    rotation_binds_any = False
    if rotation_caps:
        for crop in rotation_caps:
            key = f"rotation_{crop}"
            slack = float(named_slacks.get(key, np.nan))
            diagnostics[f"rotation_slack_{crop}"] = slack
            diagnostics[f"rotation_binds_{crop}"] = bool(slack <= active_tol)
            rotation_binds_any = rotation_binds_any or bool(slack <= active_tol)
    contract_binds_any = False
    if contract_minimums:
        for crop in contract_minimums:
            key = f"contract_{crop}"
            slack = float(named_slacks.get(key, np.nan))
            diagnostics[f"contract_slack_{crop}"] = slack
            diagnostics[f"contract_binds_{crop}"] = bool(slack <= active_tol)
            contract_binds_any = contract_binds_any or bool(slack <= active_tol)

    # Complete LP KKT diagnostics. HiGHS inequality marginals are derivatives
    # with respect to right-hand sides, so their negatives are nonnegative
    # multipliers for A x <= b. Bound marginals follow the analogous signs.
    inequality_marginals = np.asarray(result.ineqlin.marginals, dtype=float)
    inequality_duals = -inequality_marginals
    lower_raw = np.asarray(result.lower.marginals, dtype=float)
    upper_raw = np.asarray(result.upper.marginals, dtype=float)
    lower_duals = lower_raw
    upper_duals = -upper_raw
    stationarity = (
        objective
        + a_ub_arr.T @ inequality_duals
        - lower_duals
        + upper_duals
    )
    lower_residual = np.maximum(
        np.asarray([bound[0] if bound[0] is not None else -np.inf for bound in bounds]) - result.x,
        0.0,
    )
    upper_residual = np.maximum(
        result.x - np.asarray([bound[1] if bound[1] is not None else np.inf for bound in bounds]),
        0.0,
    )
    cvar_index = constraint_names.index("cvar")
    tail_indices = [idx for idx, name in enumerate(constraint_names) if name.startswith("tail_scenario_")]
    risk_dual = float(inequality_duals[cvar_index])
    tail_duals = inequality_duals[tail_indices]
    if risk_dual > 1e-10:
        tail_weights = tail_duals / risk_dual
        tail_weight_sum = float(tail_weights.sum())
        tail_weight_min = float(tail_weights.min())
        tail_weight_max = float(tail_weights.max())
        cvar_subgradient = -(tail_weights @ scenarios)
        tail_weight_cap = float(1.0 / ((1.0 - alpha) * n_scenarios))
        tail_weight_violation = float(
            max(0.0, -tail_weight_min, tail_weight_max - tail_weight_cap)
        )
    else:
        cvar_subgradient = np.zeros(n_crops)
        tail_weight_sum = np.nan
        tail_weight_min = np.nan
        tail_weight_max = np.nan
        tail_weight_cap = float(1.0 / ((1.0 - alpha) * n_scenarios))
        tail_weight_violation = np.nan
    diagnostics.update(
        {
            "optimizer_var_auxiliary": float(result.x[v_idx]),
            "optimizer_cvar_expression": optimizer_cvar_expression,
            "optimizer_cvar_slack": optimizer_cvar_slack,
            "cvar_slack": empirical_cvar_slack,
            "budget_binds": bool(budget_slack <= active_tol),
            "cvar_binds": bool(empirical_cvar_slack <= active_tol),
            "land_binds": bool(land_slack <= active_tol),
            "rotation_binds": bool(rotation_binds_any),
            "contract_binds": bool(contract_binds_any),
            "lower_bound_binds": bool(any(bounds_diagnostics[f"lower_bound_binds_{crop}"] for crop in crop_names)),
            "upper_bound_binds": bool(any(bounds_diagnostics[f"upper_bound_binds_{crop}"] for crop in crop_names)),
            "kkt_primal_residual": float(max(
                np.maximum(a_ub_arr @ result.x - b_ub_arr, 0.0).max(initial=0.0),
                lower_residual.max(initial=0.0),
                upper_residual.max(initial=0.0),
            )),
            "kkt_dual_nonnegativity_violation": float(max(
                np.maximum(-inequality_duals, 0.0).max(initial=0.0),
                np.maximum(-lower_duals, 0.0).max(initial=0.0),
                np.maximum(-upper_duals, 0.0).max(initial=0.0),
            )),
            "kkt_stationarity_residual": float(np.max(np.abs(stationarity))),
            "kkt_complementarity_residual": float(max(
                np.max(np.abs(inequality_duals * constraint_slacks)),
                np.max(np.abs(lower_duals * np.maximum(result.x - np.asarray([
                    bound[0] if bound[0] is not None else result.x[i]
                    for i, bound in enumerate(bounds)
                ]), 0.0))),
                np.max(np.abs(upper_duals * np.maximum(np.asarray([
                    bound[1] if bound[1] is not None else result.x[i]
                    for i, bound in enumerate(bounds)
                ]) - result.x, 0.0))),
            )),
            "risk_dual_eta": risk_dual,
            "tail_weight_sum": tail_weight_sum,
            "tail_weight_min": tail_weight_min,
            "tail_weight_max": tail_weight_max,
            "tail_weight_cap": tail_weight_cap,
            "tail_weight_violation": tail_weight_violation,
        }
    )
    diagnostics.update(raw_marginals)
    diagnostics.update(shadow_prices)
    diagnostics.update(bounds_diagnostics)
    for crop, value in zip(crop_names, cvar_subgradient):
        diagnostics[f"cvar_subgradient_{crop}"] = float(value)
    return AllocationResult(
        allocation=allocation,
        expected_profit=float(np.mean(profits)),
        cvar_loss=float(cvar_loss),
        var_loss=float(var_loss),
        status="optimal",
        solver_status=int(result.status),
        message=str(result.message),
        diagnostics=diagnostics,
    )


def solve_expected_profit_allocation(
    means: Iterable[float],
    costs: Iterable[float],
    total_acres: float,
    budget: float,
    lower_bounds: Iterable[float],
    upper_bounds: Iterable[float],
    rotation_caps: Optional[Dict[str, float]],
    crop_names: List[str],
    contract_minimums: Optional[Dict[str, float]] = None,
) -> AllocationResult:
    """Solve expected-profit allocation without a CVaR constraint."""

    means_arr = np.asarray(list(means), dtype=float)
    costs_arr = np.asarray(list(costs), dtype=float)
    lb = np.asarray(list(lower_bounds), dtype=float)
    ub = np.asarray(list(upper_bounds), dtype=float)
    n_crops = means_arr.size

    a_ub = [np.ones(n_crops), costs_arr]
    b_ub = [float(total_acres), float(budget)]
    constraint_names = ["land", "budget"]
    if rotation_caps:
        for crop, cap in rotation_caps.items():
            row = np.zeros(n_crops)
            row[crop_names.index(crop)] = 1.0
            a_ub.append(row)
            b_ub.append(float(cap))
            constraint_names.append(f"rotation_{crop}")
    if contract_minimums:
        for crop, minimum in contract_minimums.items():
            if crop not in crop_names:
                raise ValueError(f"contract crop {crop!r} is not in crop_names.")
            row = np.zeros(n_crops)
            row[crop_names.index(crop)] = -1.0
            a_ub.append(row)
            b_ub.append(-float(minimum))
            constraint_names.append(f"contract_{crop}")

    result = linprog(
        -means_arr,
        A_ub=np.vstack(a_ub),
        b_ub=np.asarray(b_ub),
        bounds=[(float(lb[i]), float(ub[i])) for i in range(n_crops)],
        method="highs",
    )
    if not result.success:
        return AllocationResult(
            allocation=None,
            expected_profit=None,
            cvar_loss=None,
            var_loss=None,
            status="infeasible_or_failed",
            solver_status=int(result.status),
            message=str(result.message),
            diagnostics={},
        )
    allocation = np.maximum(result.x, 0.0)
    diagnostics = constraint_diagnostics(
        allocation,
        costs_arr,
        total_acres,
        budget,
        lb,
        ub,
        rotation_caps,
        crop_names,
    )
    # HiGHS reports derivatives of the minimized objective (-profit) with
    # respect to <= right-hand sides.  Their negatives are the economically
    # oriented shadow prices for the corresponding maximization resources.
    # The dual-adjusted marginal value below is therefore
    #   mean_i - sum_j lambda_j A_ji.
    # It is an optimizer-derived diagnostic, not an independent ranking rule.
    raw_marginals = getattr(getattr(result, "ineqlin", None), "marginals", None)
    if raw_marginals is not None:
        lambdas = -np.asarray(raw_marginals, dtype=float)
        a_ub_arr = np.vstack(a_ub)
        for name, marginal, shadow in zip(constraint_names, raw_marginals, lambdas):
            diagnostics[f"raw_dual_{name}"] = float(marginal)
            diagnostics[f"shadow_price_{name}"] = float(shadow)
        adjusted = means_arr - a_ub_arr.T @ lambdas
        for crop, value in zip(crop_names, adjusted):
            diagnostics[f"dual_adjusted_value_{crop}"] = float(value)
    lower_marginals = getattr(getattr(result, "lower", None), "marginals", None)
    upper_marginals = getattr(getattr(result, "upper", None), "marginals", None)
    for idx, crop in enumerate(crop_names):
        if lower_marginals is not None:
            diagnostics[f"raw_dual_lower_bound_{crop}"] = float(lower_marginals[idx])
        if upper_marginals is not None:
            diagnostics[f"raw_dual_upper_bound_{crop}"] = float(upper_marginals[idx])
    return AllocationResult(
        allocation=allocation,
        expected_profit=float(means_arr @ allocation),
        cvar_loss=None,
        var_loss=None,
        status="optimal",
        solver_status=int(result.status),
        message=str(result.message),
        diagnostics=diagnostics,
    )
