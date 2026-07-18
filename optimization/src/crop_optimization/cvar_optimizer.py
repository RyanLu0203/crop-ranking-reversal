"""CVaR-constrained land-allocation optimizer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
from scipy.optimize import linprog

from .evaluation import constraint_diagnostics, empirical_var_cvar_losses, portfolio_profit


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

    n_vars = n_crops + 1 + n_scenarios
    v_idx = n_crops
    q_start = n_crops + 1

    mean_profit = scenarios.mean(axis=0)
    objective = np.zeros(n_vars)
    objective[:n_crops] = -mean_profit
    # v and q are feasibility auxiliaries. A small weighted penalty would
    # alter the primary expected-profit objective rather than implement an
    # exact lexicographic tie-break, so their coefficients remain zero.

    a_ub = []
    b_ub = []
    constraint_names: List[str] = []

    row = np.zeros(n_vars)
    row[:n_crops] = 1.0
    a_ub.append(row)
    b_ub.append(float(total_acres))
    constraint_names.append("land")

    row = np.zeros(n_vars)
    row[:n_crops] = costs_arr
    a_ub.append(row)
    b_ub.append(float(budget))
    constraint_names.append("budget")

    cvar_row = np.zeros(n_vars)
    cvar_row[v_idx] = 1.0
    cvar_row[q_start:] = 1.0 / max((1.0 - alpha) * n_scenarios, 1e-12)
    a_ub.append(cvar_row)
    b_ub.append(float(cvar_limit))
    constraint_names.append("cvar")

    # q_s >= loss_s - v, where loss_s = -profit_s @ x.
    # Equivalent: (-profit_s) x - v - q_s <= 0.
    for scenario_idx in range(n_scenarios):
        row = np.zeros(n_vars)
        row[:n_crops] = -scenarios[scenario_idx, :]
        row[v_idx] = -1.0
        row[q_start + scenario_idx] = -1.0
        a_ub.append(row)
        b_ub.append(0.0)
        constraint_names.append(f"tail_scenario_{scenario_idx}")

    if rotation_caps:
        for crop, cap in rotation_caps.items():
            if crop not in crop_names:
                raise ValueError(f"rotation cap crop {crop!r} is not in crop_names.")
            row = np.zeros(n_vars)
            row[crop_names.index(crop)] = 1.0
            a_ub.append(row)
            b_ub.append(float(cap))
            constraint_names.append(f"rotation_{crop}")

    bounds = [(float(lb[i]), float(ub[i])) for i in range(n_crops)]
    bounds.append((None, None))
    bounds.extend((0.0, None) for _ in range(n_scenarios))

    result = linprog(
        objective,
        A_ub=np.vstack(a_ub),
        b_ub=np.asarray(b_ub),
        bounds=bounds,
        method="highs",
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
    a_ub_arr = np.vstack(a_ub)
    b_ub_arr = np.asarray(b_ub)
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
            "lower_bound_binds": bool(any(bounds_diagnostics[f"lower_bound_binds_{crop}"] for crop in crop_names)),
            "upper_bound_binds": bool(any(bounds_diagnostics[f"upper_bound_binds_{crop}"] for crop in crop_names)),
        }
    )
    diagnostics.update(raw_marginals)
    diagnostics.update(shadow_prices)
    diagnostics.update(bounds_diagnostics)
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
