"""Lagged empirical suitability definitions without future leakage."""

from __future__ import annotations

from typing import Iterable, List, Optional

import numpy as np
import pandas as pd


def _normalize_within_group(df: pd.DataFrame, value_col: str, out_col: str) -> pd.DataFrame:
    out = df.copy()
    min_v = out.groupby(["state", "county_fips", "year"])[value_col].transform("min")
    max_v = out.groupby(["state", "county_fips", "year"])[value_col].transform("max")
    denom = (max_v - min_v).replace(0.0, np.nan)
    out[out_col] = (out[value_col] - min_v) / denom
    out[out_col] = out[out_col].fillna(1.0)
    return out


def compute_lagged_yield_suitability(
    panel: pd.DataFrame,
    min_history_years: int = 3,
    crops: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Compute decision-year suitability from prior-year yield only."""

    crops = list(crops) if crops is not None else sorted(panel["crop"].dropna().unique())
    rows: List[dict] = []
    data = panel.loc[panel["crop"].isin(crops)].copy()
    for (state, county_fips, county, crop), part in data.groupby(["state", "county_fips", "county", "crop"]):
        part = part.sort_values("year")
        for _, row in part.iterrows():
            hist = part.loc[part["year"] < row["year"], "yield_per_acre"].dropna()
            if len(hist) < min_history_years:
                continue
            rows.append(
                {
                    "state": state,
                    "county": county,
                    "county_fips": county_fips,
                    "year": int(row["year"]),
                    "crop": crop,
                    "lagged_yield_mean": float(hist.mean()),
                    "history_years": int(len(hist)),
                    "suitability_definition": "lagged_historical_yield",
                }
            )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return _normalize_within_group(result, "lagged_yield_mean", "suitability_score")


def compute_lagged_expected_profit_suitability(
    panel: pd.DataFrame,
    min_history_years: int = 3,
    crops: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Compute decision-year suitability from prior-year profit only."""

    crops = list(crops) if crops is not None else sorted(panel["crop"].dropna().unique())
    rows: List[dict] = []
    data = panel.loc[panel["crop"].isin(crops)].copy()
    for (state, county_fips, county, crop), part in data.groupby(["state", "county_fips", "county", "crop"]):
        part = part.sort_values("year")
        for _, row in part.iterrows():
            hist = part.loc[part["year"] < row["year"], "profit_per_acre"].dropna()
            if len(hist) < min_history_years:
                continue
            rows.append(
                {
                    "state": state,
                    "county": county,
                    "county_fips": county_fips,
                    "year": int(row["year"]),
                    "crop": crop,
                    "lagged_profit_mean": float(hist.mean()),
                    "history_years": int(len(hist)),
                    "suitability_definition": "lagged_expected_profit",
                }
            )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return _normalize_within_group(result, "lagged_profit_mean", "suitability_score")


def rank_crops_by_suitability(suitability: pd.DataFrame) -> pd.DataFrame:
    """Rank crops within each decision county-year, highest score first."""

    required = {"state", "county_fips", "year", "crop", "suitability_score"}
    missing = required - set(suitability.columns)
    if missing:
        raise ValueError(f"Suitability table is missing required columns: {sorted(missing)}")
    ranked = suitability.copy()
    ranked["suitability_rank"] = ranked.groupby(["state", "county_fips", "year"])["suitability_score"].rank(
        method="first", ascending=False
    )
    return ranked.sort_values(["state", "county_fips", "year", "suitability_rank"])
