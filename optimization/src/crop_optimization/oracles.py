"""Small independent analytical/enumeration oracles for LP regression tests."""

from __future__ import annotations

from typing import Iterable

import numpy as np


def rockafellar_uryasev_cvar_oracle(losses: Iterable[float], alpha: float) -> tuple[float, float]:
    """Enumerate all loss atoms as candidate VaR auxiliaries."""

    values = np.asarray(list(losses), dtype=float)
    if values.size == 0 or not 0.0 < float(alpha) < 1.0:
        raise ValueError("losses must be non-empty and alpha must lie in (0,1)")
    candidates = np.unique(values)
    objectives = [
        float(v + np.maximum(values - v, 0.0).mean() / (1.0 - float(alpha)))
        for v in candidates
    ]
    index = int(np.argmin(objectives))
    return float(candidates[index]), float(objectives[index])


def two_crop_grid_oracle(
    profit_scenarios: np.ndarray,
    costs: Iterable[float],
    total_land: float,
    budget: float,
    alpha: float,
    cvar_limit: float,
    step: float,
) -> dict[str, object]:
    """Enumerate a two-crop grid; intended only for tiny test instances."""

    scenarios = np.asarray(profit_scenarios, dtype=float)
    costs_arr = np.asarray(list(costs), dtype=float)
    if scenarios.shape[1] != 2 or costs_arr.size != 2 or step <= 0:
        raise ValueError("oracle requires two crops and a positive step")
    best = None
    candidates = 0
    grid = np.arange(0.0, float(total_land) + step / 2.0, float(step))
    for x0 in grid:
        for x1 in grid:
            x = np.asarray([x0, x1])
            if x.sum() > total_land + 1e-12 or costs_arr @ x > budget + 1e-12:
                continue
            profits = scenarios @ x
            _, cvar = rockafellar_uryasev_cvar_oracle(-profits, alpha)
            if cvar > cvar_limit + 1e-12:
                continue
            candidates += 1
            objective = float(profits.mean())
            if best is None or objective > best[0] + 1e-12:
                best = (objective, x.copy(), cvar)
    if best is None:
        return {"status": "infeasible", "feasible_grid_points": 0}
    return {
        "status": "optimal_on_grid",
        "objective": best[0],
        "allocation": best[1],
        "cvar_loss": best[2],
        "feasible_grid_points": candidates,
    }
