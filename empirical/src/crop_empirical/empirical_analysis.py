"""Frozen descriptive empirical analysis for Issue 7."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import numpy as np
import pandas as pd
import yaml

from .nass_summary import complete_state_year_sample, parse_nass_state_crop_summary

ROOT = Path(__file__).resolve().parents[3]
DESIGN_PATH = ROOT / "empirical/configs/empirical_design.yaml"
CROPS = ["corn", "soybeans", "winter_wheat"]
NATIONAL_CROP_MAP = {"corn": "corn", "soybeans": "soybeans", "winter_wheat": "wheat"}
SCORE_COLUMNS = {
    "relative_yield": "relative_yield",
    "standardized_revenue": "standardized_revenue_real_2024_usd_per_acre",
    "operating_margin": "standardized_operating_margin_real_2024_usd_per_acre",
    "total_cost_margin": "standardized_total_cost_margin_real_2024_usd_per_acre",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_design(path: Path = DESIGN_PATH) -> Dict[str, Any]:
    design = yaml.safe_load(path.read_text(encoding="utf-8"))
    if design.get("status") != "FROZEN_BEFORE_EMPIRICAL_RESULTS":
        raise ValueError("empirical design is not frozen")
    design["design_sha256"] = sha256_file(path)
    return design


def build_analysis_panel(national_panel_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    parsed = parse_nass_state_crop_summary()
    complete = complete_state_year_sample(parsed, CROPS)
    national_nass = parsed.loc[parsed["state"].eq("United States")].copy()
    national_nass = national_nass.rename(columns={
        "yield_bushels_per_acre": "national_nass_yield_bushels_per_acre",
        "planted_acres_1000": "national_planted_acres_1000",
    })
    complete = complete.merge(
        national_nass[["year", "crop", "national_nass_yield_bushels_per_acre", "national_planted_acres_1000"]],
        on=["year", "crop"], how="left", validate="many_to_one",
    )

    national = pd.read_csv(national_panel_path)
    national = national.loc[national["year"].between(2022, 2024)].copy()
    national["crop"] = national["crop"].map({value: key for key, value in NATIONAL_CROP_MAP.items()})
    fields = [
        "year", "crop", "harvest_price_usd_per_bushel",
        "operating_cost_usd_per_planted_acre", "total_cost_usd_per_planted_acre",
        "cpi_u_deflator_to_2024", "primary_margin_real_2024_usd_per_planted_acre",
    ]
    complete = complete.merge(national[fields], on=["year", "crop"], how="left", validate="many_to_one")
    if complete[fields[2:]].isna().any().any():
        raise ValueError("national price/cost join is incomplete")
    complete["relative_yield"] = (
        complete["yield_bushels_per_acre"] / complete["national_nass_yield_bushels_per_acre"]
    )
    deflator = complete["cpi_u_deflator_to_2024"]
    revenue_nominal = complete["yield_bushels_per_acre"] * complete["harvest_price_usd_per_bushel"]
    complete["standardized_revenue_real_2024_usd_per_acre"] = revenue_nominal * deflator
    complete["standardized_operating_margin_real_2024_usd_per_acre"] = (
        revenue_nominal - complete["operating_cost_usd_per_planted_acre"]
    ) * deflator
    complete["standardized_total_cost_margin_real_2024_usd_per_acre"] = (
        revenue_nominal - complete["total_cost_usd_per_planted_acre"]
    ) * deflator
    complete["observed_acreage_share"] = complete["planted_acres_1000"] / complete.groupby(
        ["state", "year"]
    )["planted_acres_1000"].transform("sum")
    complete["geographic_price_cost_scope"] = "STATE_YIELD_WITH_NATIONAL_PRICE_AND_COST"
    complete["observed_allocation_interpretation"] = "AGGREGATE_ACREAGE_NOT_MODEL_OPTIMUM"
    return parsed, complete.sort_values(["state", "year", "crop"]).reset_index(drop=True)


def _pairwise_inversions(part: pd.DataFrame, score_col: str) -> Tuple[int, int]:
    inversions = 0
    ties = 0
    indexed = part.set_index("crop")
    for crop_a, crop_b in itertools.combinations(CROPS, 2):
        score_difference = float(indexed.loc[crop_a, score_col] - indexed.loc[crop_b, score_col])
        acreage_difference = float(indexed.loc[crop_a, "planted_acres_1000"] - indexed.loc[crop_b, "planted_acres_1000"])
        product = score_difference * acreage_difference
        if product < 0:
            inversions += 1
        elif product == 0:
            ties += 1
    return inversions, ties


def discordance_analysis(panel: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    ranking_rows = []
    detail_rows = []
    for definition, score_col in SCORE_COLUMNS.items():
        for (state, year), part in panel.groupby(["state", "year"], sort=True):
            part = part.copy()
            part["score_rank"] = part[score_col].rank(method="min", ascending=False)
            part["acreage_rank"] = part["planted_acres_1000"].rank(method="min", ascending=False)
            score_max = part[score_col].max()
            acreage_max = part["planted_acres_1000"].max()
            acreage_min = part["planted_acres_1000"].min()
            top_score = sorted(part.loc[part[score_col].eq(score_max), "crop"])
            top_acreage = sorted(part.loc[part["planted_acres_1000"].eq(acreage_max), "crop"])
            bottom_acreage = set(part.loc[part["planted_acres_1000"].eq(acreage_min), "crop"])
            inversions, ties = _pairwise_inversions(part, score_col)
            observed_value = float(
                (part["observed_acreage_share"] * part["standardized_operating_margin_real_2024_usd_per_acre"]).sum()
            )
            equal_value = float(part["standardized_operating_margin_real_2024_usd_per_acre"].mean())
            top_value = float(
                part.loc[part["crop"].isin(top_score), "standardized_operating_margin_real_2024_usd_per_acre"].mean()
            )
            detail_rows.append({
                "state": state, "year": int(year), "ranking_definition": definition,
                "pairwise_inversions": inversions, "pairwise_ties": ties,
                "inversion_distance": inversions / 3.0,
                "top_rank_reversal": bool(set(top_score).isdisjoint(top_acreage)),
                "strong_reversal": bool(set(top_score).issubset(bottom_acreage)),
                "top_score_crops": ";".join(top_score),
                "top_acreage_crops": ";".join(top_acreage),
                "observed_share_operating_margin_value": observed_value,
                "equal_share_operating_margin_value": equal_value,
                "score_top_operating_margin_value": top_value,
                "observed_minus_equal_value": observed_value - equal_value,
                "observed_minus_score_top_value": observed_value - top_value,
                "permutation_expected_inversions": 1.5,
                "permutation_expected_top_reversal": 2.0 / 3.0,
                "claim_level": "DESCRIPTIVE_ACCOUNTING_NOT_CAUSAL",
            })
            for _, row in part.iterrows():
                ranking_rows.append({
                    "state": state, "year": int(year), "crop": row["crop"],
                    "ranking_definition": definition, "score": float(row[score_col]),
                    "score_rank": float(row["score_rank"]),
                    "planted_acres_1000": float(row["planted_acres_1000"]),
                    "observed_acreage_share": float(row["observed_acreage_share"]),
                    "acreage_rank": float(row["acreage_rank"]),
                })
    return pd.DataFrame(detail_rows), pd.DataFrame(ranking_rows)


def definition_summary(detail: pd.DataFrame) -> pd.DataFrame:
    return (
        detail.groupby("ranking_definition", sort=True)
        .agg(
            state_years=("state", "size"),
            states=("state", "nunique"),
            mean_pairwise_inversions=("pairwise_inversions", "mean"),
            median_pairwise_inversions=("pairwise_inversions", "median"),
            top_rank_reversal_rate=("top_rank_reversal", "mean"),
            strong_reversal_rate=("strong_reversal", "mean"),
            mean_observed_minus_equal_value=("observed_minus_equal_value", "mean"),
            mean_observed_minus_score_top_value=("observed_minus_score_top_value", "mean"),
        ).reset_index()
    )


def heterogeneity_summaries(detail: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    state = (
        detail.groupby(["ranking_definition", "state"], sort=True)
        .agg(years=("year", "nunique"), mean_inversions=("pairwise_inversions", "mean"),
             top_reversal_rate=("top_rank_reversal", "mean"), strong_reversal_rate=("strong_reversal", "mean"))
        .reset_index()
    )
    year = (
        detail.groupby(["ranking_definition", "year"], sort=True)
        .agg(states=("state", "nunique"), mean_inversions=("pairwise_inversions", "mean"),
             top_reversal_rate=("top_rank_reversal", "mean"), strong_reversal_rate=("strong_reversal", "mean"))
        .reset_index()
    )
    return state, year


def national_check(parsed: pd.DataFrame, national_panel_path: Path) -> pd.DataFrame:
    acreage = parsed.loc[parsed["state"].eq("United States")].copy()
    national = pd.read_csv(national_panel_path)
    national = national.loc[national["year"].between(2022, 2024)].copy()
    national["crop"] = national["crop"].map({value: key for key, value in NATIONAL_CROP_MAP.items()})
    merged = acreage.merge(
        national[["year", "crop", "primary_margin_real_2024_usd_per_planted_acre"]],
        on=["year", "crop"], how="left", validate="one_to_one",
    )
    merged["margin_rank"] = merged.groupby("year")["primary_margin_real_2024_usd_per_planted_acre"].rank(method="min", ascending=False)
    merged["acreage_rank"] = merged.groupby("year")["planted_acres_1000"].rank(method="min", ascending=False)
    merged["rank_reversal"] = merged["margin_rank"].ne(merged["acreage_rank"])
    merged["claim_level"] = "NATIONAL_DESCRIPTIVE_CHECK"
    return merged[[
        "year", "crop", "planted_acres_1000", "primary_margin_real_2024_usd_per_planted_acre",
        "margin_rank", "acreage_rank", "rank_reversal", "claim_level",
    ]].sort_values(["year", "crop"])


def lagged_2024_validation(panel: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    training = panel.loc[panel["year"].isin([2022, 2023])]
    scores = training.groupby(["state", "crop"])["relative_yield"].mean().rename("lagged_relative_yield")
    test = panel.loc[panel["year"].eq(2024)].join(scores, on=["state", "crop"], how="inner")
    complete_states = test.groupby("state")["crop"].nunique()
    test = test.loc[test["state"].isin(complete_states.loc[complete_states.eq(3)].index)].copy()
    test["score_rank"] = test.groupby("state")["lagged_relative_yield"].rank(method="min", ascending=False)
    test["acreage_rank"] = test.groupby("state")["planted_acres_1000"].rank(method="min", ascending=False)
    rows = []
    for state, part in test.groupby("state"):
        inversions, ties = _pairwise_inversions(part.rename(columns={"lagged_relative_yield": "lagged_score"}), "lagged_score")
        top_score = set(part.loc[part["lagged_relative_yield"].eq(part["lagged_relative_yield"].max()), "crop"])
        top_acreage = set(part.loc[part["planted_acres_1000"].eq(part["planted_acres_1000"].max()), "crop"])
        rows.append({
            "state": state, "decision_year": 2024, "training_years": "2022;2023",
            "pairwise_inversions": inversions, "pairwise_ties": ties,
            "top_rank_reversal": bool(top_score.isdisjoint(top_acreage)),
            "claim_level": "LOW_POWER_LEAKAGE_FREE_DESCRIPTIVE_VALIDATION",
        })
    return test.sort_values(["state", "crop"]), pd.DataFrame(rows)


def leave_one_year_out(detail: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for definition, part in detail.groupby("ranking_definition"):
        for omitted in (2022, 2023, 2024):
            kept = part.loc[part["year"].ne(omitted)]
            rows.append({
                "ranking_definition": definition, "omitted_year": omitted,
                "state_years": len(kept),
                "mean_pairwise_inversions": float(kept["pairwise_inversions"].mean()),
                "top_rank_reversal_rate": float(kept["top_rank_reversal"].mean()),
                "strong_reversal_rate": float(kept["strong_reversal"].mean()),
            })
    return pd.DataFrame(rows)


def sample_flow(parsed: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    state_rows = parsed.loc[parsed["state"].ne("United States")]
    return pd.DataFrame([
        {"stage": "parsed NASS table rows including U.S. totals", "rows": len(parsed), "state_years": parsed[["state", "year"]].drop_duplicates().shape[0]},
        {"stage": "state rows before complete-case restriction", "rows": len(state_rows), "state_years": state_rows[["state", "year"]].drop_duplicates().shape[0]},
        {"stage": "complete three-crop state-year sample", "rows": len(panel), "state_years": panel[["state", "year"]].drop_duplicates().shape[0]},
    ])


def exact_permutation_benchmark() -> pd.DataFrame:
    rows = []
    reference = (0, 1, 2)
    for permutation in itertools.permutations(reference):
        inversions = sum(
            (reference[i] - reference[j]) * (permutation[i] - permutation[j]) < 0
            for i, j in itertools.combinations(range(3), 2)
        )
        rows.append({
            "permutation": "".join(map(str, permutation)),
            "pairwise_inversions": int(inversions),
            "top_rank_reversal": bool(permutation[0] != 0),
            "interpretation": "COMBINATORIAL_REFERENCE_NOT_SAMPLING_NULL",
        })
    return pd.DataFrame(rows)


def boundary_table() -> pd.DataFrame:
    return pd.DataFrame([
        {"claim_domain": "ranking discordance", "status": "DESCRIPTIVE_IDENTIFIED", "reason": "official state acreage and yield in the same NASS snapshot"},
        {"claim_domain": "economic consequences", "status": "ACCOUNTING_ONLY", "reason": "state yield combined with national price and cost"},
        {"claim_domain": "geographic heterogeneity", "status": "ASSOCIATIVE_DESCRIPTION", "reason": "three years and no causal design"},
        {"claim_domain": "observed acreage optimality", "status": "NOT_IDENTIFIED", "reason": "private feasible sets and objectives are absent"},
        {"claim_domain": "CVaR binding or causality", "status": "NOT_IDENTIFIED", "reason": "no farmer risk limit or decision-level loss distribution"},
        {"claim_domain": "copula mechanism", "status": "NOT_IDENTIFIED", "reason": "aggregate observed acreage cannot identify dependence causality"},
        {"claim_domain": "state realized downside/CVaR", "status": "NOT_IDENTIFIED", "reason": "only three annual observations"},
        {"claim_domain": "data revision robustness", "status": "NOT_IDENTIFIED", "reason": "one fixed NASS vintage only"},
        {"claim_domain": "optimizer selection robustness", "status": "NOT_APPLICABLE", "reason": "observed acreage is not treated as an optimizer output"},
    ])


def summarize(
    design: Dict[str, Any], parsed: pd.DataFrame, panel: pd.DataFrame,
    detail: pd.DataFrame, lagged_summary: pd.DataFrame,
) -> Dict[str, Any]:
    operating = detail.loc[detail["ranking_definition"].eq("operating_margin")]
    return {
        "design_id": design["design_id"], "design_sha256": design["design_sha256"],
        "parsed_rows": int(len(parsed)), "complete_panel_rows": int(len(panel)),
        "complete_state_years": int(panel[["state", "year"]].drop_duplicates().shape[0]),
        "states": int(panel["state"].nunique()), "years": sorted(map(int, panel["year"].unique())),
        "operating_margin_mean_pairwise_inversions": float(operating["pairwise_inversions"].mean()),
        "operating_margin_top_reversal_rate": float(operating["top_rank_reversal"].mean()),
        "operating_margin_strong_reversal_rate": float(operating["strong_reversal"].mean()),
        "lagged_2024_states": int(len(lagged_summary)),
        "lagged_2024_top_reversal_rate": float(lagged_summary["top_rank_reversal"].mean()),
        "observed_acreage_is_optimum": False,
        "cvar_mechanism_identified": False,
        "causal_claim_admissible": False,
        "result_scope": "DESCRIPTIVE_AND_ACCOUNTING_ONLY",
    }
