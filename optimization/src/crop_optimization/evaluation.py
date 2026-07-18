"""Evaluation metrics for crop allocation policies."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np


def portfolio_profit(profit_scenarios: np.ndarray, allocation: Iterable[float]) -> np.ndarray:
    allocation_arr = np.asarray(list(allocation), dtype=float)
    return np.asarray(profit_scenarios, dtype=float) @ allocation_arr


def empirical_var_cvar_losses(losses: np.ndarray, alpha: float) -> Tuple[float, float]:
    """Compute sample VaR and CVaR on losses.

    The sign convention is explicit: losses are negative portfolio profits.
    Larger loss values are worse outcomes.
    """

    losses = np.asarray(losses, dtype=float)
    if losses.size == 0:
        raise ValueError("losses must be non-empty.")
    alpha = float(alpha)
    var = float(np.quantile(losses, alpha, method="higher"))
    cvar = float(var + np.maximum(losses - var, 0.0).mean() / max(1.0 - alpha, 1e-12))
    return var, cvar


def worst_decile_profit(profits: np.ndarray, alpha: float) -> float:
    profits = np.asarray(profits, dtype=float)
    tail_count = max(1, int(np.ceil((1.0 - float(alpha)) * profits.size)))
    return float(np.mean(np.sort(profits)[:tail_count]))


def allocation_metrics(
    allocation: Iterable[float],
    profit_scenarios: np.ndarray,
    costs: Iterable[float],
    total_acres: float,
    budget: float,
    alpha: float,
    cvar_limit: float,
    crop_names: Optional[List[str]] = None,
    lower_bounds: Optional[Iterable[float]] = None,
    upper_bounds: Optional[Iterable[float]] = None,
    rotation_caps: Optional[Dict[str, float]] = None,
    contract_minimums: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    allocation_arr = np.asarray(list(allocation), dtype=float)
    costs_arr = np.asarray(list(costs), dtype=float)
    profits = portfolio_profit(profit_scenarios, allocation_arr)
    losses = -profits
    var, cvar = empirical_var_cvar_losses(losses, alpha)
    metrics: Dict[str, float] = {
        "expected_profit": float(np.mean(profits)),
        "var_loss": var,
        "cvar_loss": cvar,
        "worst_decile_profit": worst_decile_profit(profits, alpha),
        "budget_usage": float(costs_arr @ allocation_arr),
        "acreage_usage": float(allocation_arr.sum()),
        "cvar_violation": bool(cvar > cvar_limit + 1e-6),
        "budget_violation": bool(costs_arr @ allocation_arr > budget + 1e-6),
        "acreage_violation": bool(allocation_arr.sum() > total_acres + 1e-6),
    }
    names = crop_names or [f"crop_{idx + 1}" for idx in range(len(allocation_arr))]
    if lower_bounds is not None:
        lb = np.asarray(list(lower_bounds), dtype=float)
        metrics["lower_bound_violation"] = bool(np.any(allocation_arr < lb - 1e-6))
    if upper_bounds is not None:
        ub = np.asarray(list(upper_bounds), dtype=float)
        metrics["upper_bound_violation"] = bool(np.any(allocation_arr > ub + 1e-6))
    if rotation_caps:
        metrics["rotation_violation"] = bool(any(
            allocation_arr[names.index(crop)] > float(cap) + 1e-6
            for crop, cap in rotation_caps.items()
        ))
    if contract_minimums:
        metrics["contract_violation"] = bool(any(
            allocation_arr[names.index(crop)] < float(minimum) - 1e-6
            for crop, minimum in contract_minimums.items()
        ))
    for idx, value in enumerate(allocation_arr):
        name = names[idx]
        metrics[f"acres_{name}"] = float(value)
    return metrics


def pseudo_diversification_diagnostic(
    allocation: Iterable[float],
    ranking_scores: Iterable[float],
    correlation: np.ndarray,
    lower_tail_dependence: float,
    *,
    dominant_share_threshold: float = 0.80,
    correlation_threshold: float = 0.25,
    tail_threshold: float = 0.10,
) -> Dict[str, object]:
    """Flag a descriptive low-dependence diversification pattern.

    This diagnostic is neither a welfare result nor a sufficient condition
    for exclusion. It records whether the top-ranked crop is not dominant
    while pairwise and lower-tail dependence are below predeclared cutoffs.
    """

    x = np.asarray(list(allocation), dtype=float)
    scores = np.asarray(list(ranking_scores), dtype=float)
    corr = np.asarray(correlation, dtype=float)
    if x.size != scores.size or corr.shape != (x.size, x.size):
        raise ValueError("allocation, ranking scores, and correlation dimensions must agree")
    total = float(x.sum())
    top = int(np.argmax(scores))
    top_share = float(x[top] / total) if total > 0 else 0.0
    off_diagonal = corr[np.triu_indices_from(corr, k=1)]
    max_correlation = float(off_diagonal.max()) if off_diagonal.size else 0.0
    flagged = (
        top_share < float(dominant_share_threshold)
        and max_correlation < float(correlation_threshold)
        and float(lower_tail_dependence) < float(tail_threshold)
    )
    return {
        "pseudo_diversification_flag": bool(flagged),
        "top_ranked_crop_index": top,
        "top_ranked_allocation_share": top_share,
        "max_pairwise_correlation": max_correlation,
        "lower_tail_dependence": float(lower_tail_dependence),
        "interpretation": "DESCRIPTIVE_ONLY_NOT_WELFARE_OR_EXCLUSION",
    }


def ranking_reversal_flags(
    allocation: Iterable[float],
    crop_names: List[str],
    higher_crop: str = "Corn",
    lower_crop: str = "Soybean",
    tolerance: float = 1e-5,
) -> Tuple[bool, bool]:
    values = dict(zip(crop_names, np.asarray(list(allocation), dtype=float)))
    higher = float(values[higher_crop])
    lower = float(values[lower_crop])
    reversal = lower > higher + tolerance
    strong_reversal = higher <= tolerance and lower > tolerance
    return bool(reversal), bool(strong_reversal)


def constraint_diagnostics(
    allocation: Iterable[float],
    costs: Iterable[float],
    total_acres: float,
    budget: float,
    lower_bounds: Iterable[float],
    upper_bounds: Iterable[float],
    rotation_caps: Optional[Dict[str, float]],
    crop_names: List[str],
    cvar_loss: Optional[float] = None,
    cvar_limit: Optional[float] = None,
) -> Dict[str, float]:
    x = np.asarray(list(allocation), dtype=float)
    costs_arr = np.asarray(list(costs), dtype=float)
    lb = np.asarray(list(lower_bounds), dtype=float)
    ub = np.asarray(list(upper_bounds), dtype=float)
    diagnostics: Dict[str, float] = {
        "acreage_usage": float(x.sum()),
        "acreage_slack": float(total_acres - x.sum()),
        "budget_usage": float(costs_arr @ x),
        "budget_slack": float(budget - costs_arr @ x),
        "min_lower_bound_slack": float(np.min(x - lb)),
        "min_upper_bound_slack": float(np.min(ub - x)),
    }
    if rotation_caps:
        for crop, cap in rotation_caps.items():
            idx = crop_names.index(crop)
            diagnostics[f"rotation_slack_{crop}"] = float(cap - x[idx])
    if cvar_loss is not None and cvar_limit is not None:
        diagnostics["cvar_loss"] = float(cvar_loss)
        diagnostics["cvar_slack"] = float(cvar_limit - cvar_loss)
    return diagnostics
