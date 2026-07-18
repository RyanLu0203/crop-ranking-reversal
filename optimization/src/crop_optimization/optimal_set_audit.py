"""Alternative-optimum audit for v7.1 ranking-allocation reversals."""

from __future__ import annotations

import bisect
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import linprog

from .numerical_tolerances import primary_tolerances

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CROPS = ["Corn", "Soybean", "Winter Wheat"]


def _latest_costs(panel: pd.DataFrame, county_fips: str, year: int) -> Dict[str, float]:
    costs: Dict[str, float] = {}
    subset = panel.loc[panel["county_fips"].astype(str).eq(str(county_fips))]
    for crop, part in subset.loc[subset["crop"].isin(CROPS)].sort_values("year").groupby("crop"):
        prior = part.loc[(part["year"].astype(int) < int(year)) & part["cost_per_acre"].notna()]
        if not prior.empty:
            costs[crop] = float(prior["cost_per_acre"].iloc[-1])
    return costs


def _profit_scores(suitability: pd.DataFrame, county_fips: str, year: int) -> Dict[str, float]:
    rows = suitability.loc[
        suitability["county_fips"].astype(str).eq(str(county_fips))
        & suitability["year"].astype(int).eq(int(year))
        & suitability["suitability_definition"].eq("lagged_expected_profit")
        & suitability["crop"].isin(CROPS)
    ]
    return rows.set_index("crop")["lagged_profit_mean"].astype(float).to_dict()


def _solve_lp(
    objective: np.ndarray,
    means: np.ndarray,
    costs: np.ndarray,
    total_acres: float,
    budget: float,
    objective_floor: float | None = None,
) -> linprog:
    a_ub = [
        np.ones(len(CROPS)),
        costs,
        np.asarray([1.0 if crop == "Corn" else 0.0 for crop in CROPS], dtype=float),
    ]
    b_ub = [float(total_acres), float(budget), 0.60 * float(total_acres)]
    if objective_floor is not None:
        a_ub.append(-means)
        b_ub.append(-float(objective_floor))
    bounds = [(0.0, float(total_acres)) for _ in CROPS]
    return linprog(objective, A_ub=np.vstack(a_ub), b_ub=np.asarray(b_ub), bounds=bounds, method="highs")


def objective_equivalent_range(
    means_by_crop: Dict[str, float],
    costs_by_crop: Dict[str, float],
    total_acres: float,
    budget: float,
    high_crop: str,
    low_crop: str,
    objective_tolerance: float,
) -> Dict[str, float | str]:
    """Min/max x_high - x_low over the objective-equivalent feasible set."""

    means = np.asarray([means_by_crop[crop] for crop in CROPS], dtype=float)
    costs = np.asarray([costs_by_crop[crop] for crop in CROPS], dtype=float)
    opt = _solve_lp(-means, means, costs, total_acres, budget)
    if not opt.success:
        return {"status": "indeterminate", "z_star": np.nan, "min_difference": np.nan, "max_difference": np.nan}
    z_star = float(means @ opt.x)
    floor = z_star - float(objective_tolerance)
    direction = np.zeros(len(CROPS))
    direction[CROPS.index(high_crop)] = 1.0
    direction[CROPS.index(low_crop)] = -1.0
    min_result = _solve_lp(direction, means, costs, total_acres, budget, floor)
    max_result = _solve_lp(-direction, means, costs, total_acres, budget, floor)
    if not min_result.success or not max_result.success:
        return {"status": "indeterminate", "z_star": z_star, "min_difference": np.nan, "max_difference": np.nan}
    return {
        "status": "solved",
        "z_star": z_star,
        "min_difference": float(direction @ min_result.x),
        "max_difference": float(direction @ max_result.x),
    }


def classify_range(min_difference: float, max_difference: float, acreage_tolerance: float) -> str:
    """Classify whether all, some, or no equivalent optima reverse a crop pair."""

    if not np.isfinite(min_difference) or not np.isfinite(max_difference):
        return "Indeterminate"
    tol = float(acreage_tolerance)
    if max_difference < -tol:
        return "Universal reversal"
    if min_difference < -tol and max_difference >= -tol:
        return "Possible reversal"
    return "No reversal"


def audit_optimal_sets(
    events: pd.DataFrame,
    panel: pd.DataFrame,
    suitability: pd.DataFrame,
    ranking_rule: str = "N2_suitability",
    max_events: int | None = None,
) -> pd.DataFrame:
    """Audit reversed crop pairs for the selected headline ranking rule."""

    tolerances = primary_tolerances()
    acreage_tol = tolerances["acreage_tie_tolerance_acres"]
    objective_tol = tolerances["objective_equivalence_tolerance_dollars"]
    rows: List[Dict[str, object]] = []
    candidates = events.loc[events["ranking_rule"].eq(ranking_rule) & events["pairwise_reversal"].astype(bool)].copy()
    if max_events is not None:
        candidates = candidates.head(max_events)
    for _, row in candidates.iterrows():
        ranking = [part.strip() for part in str(row["ranking_order"]).split(">") if part.strip()]
        acres = {crop: float(row[f"acres_{crop}"]) for crop in CROPS}
        profits = _profit_scores(suitability, str(row["county_fips"]), int(row["decision_year"]))
        costs = _latest_costs(panel, str(row["county_fips"]), int(row["decision_year"]))
        if len(profits) != len(CROPS) or len(costs) != len(CROPS):
            continue
        for high_idx, high_crop in enumerate(ranking):
            for low_crop in ranking[high_idx + 1 :]:
                if acres[low_crop] <= acres[high_crop] + acreage_tol:
                    continue
                rng = objective_equivalent_range(
                    profits,
                    costs,
                    float(row["total_acres"]),
                    float(row.get("budget", np.nan)) if "budget" in row else float(row["total_acres"]) * max(costs.values()),
                    high_crop,
                    low_crop,
                    objective_tol,
                )
                classification = classify_range(
                    float(rng["min_difference"]),
                    float(rng["max_difference"]),
                    acreage_tol,
                )
                rows.append(
                    {
                        "event_id": row["event_id"],
                        "county_fips": row["county_fips"],
                        "county": row["county"],
                        "decision_year": int(row["decision_year"]),
                        "policy": row["policy"],
                        "ranking_rule": ranking_rule,
                        "high_rank_crop": high_crop,
                        "low_rank_crop": low_crop,
                        "selected_solution_difference": acres[high_crop] - acres[low_crop],
                        "z_star": rng["z_star"],
                        "objective_equivalence_tolerance_dollars": objective_tol,
                        "min_difference": rng["min_difference"],
                        "max_difference": rng["max_difference"],
                        "classification": classification,
                        "solver_status": rng["status"],
                    }
                )
    return pd.DataFrame(rows)
