"""Frozen GOAL-15 analyses using only the admitted Stage I official panel."""

from __future__ import annotations

import hashlib
import itertools
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import yaml

from .empirical_analysis import CROPS, SCORE_COLUMNS, _pairwise_inversions


ROOT = Path(__file__).resolve().parents[3]
DESIGN_PATH = ROOT / "empirical/configs/stage_ii_empirical_design.yaml"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_stage_ii_design(path: Path = DESIGN_PATH) -> dict:
    design = yaml.safe_load(path.read_text(encoding="utf-8"))
    if design.get("status") != "FROZEN_BEFORE_STAGEII_ESTIMATION":
        raise ValueError("Stage II empirical design is not frozen")
    design["design_sha256"] = sha256_file(path)
    return design


def _bootstrap_by_state(
    frame: pd.DataFrame,
    statistic: Callable[[pd.DataFrame], float],
    replications: int,
    seed: int,
) -> tuple[float, float, float]:
    states = np.array(sorted(frame["state"].unique()))
    estimate = float(statistic(frame))
    rng = np.random.default_rng(seed)
    values = np.empty(replications, dtype=float)
    groups = {state: frame.loc[frame["state"].eq(state)] for state in states}
    for index in range(replications):
        sampled = rng.choice(states, size=len(states), replace=True)
        draw = pd.concat([groups[state] for state in sampled], ignore_index=True)
        values[index] = statistic(draw)
    low, high = np.quantile(values, [0.025, 0.975])
    return estimate, float(low), float(high)


def _score_rank_and_z(panel: pd.DataFrame, score_col: str) -> pd.DataFrame:
    frame = panel[["state", "year", "crop", "observed_acreage_share", "planted_acres_1000", score_col]].copy()
    frame = frame.rename(columns={score_col: "score"})
    grouped = frame.groupby(["state", "year"])["score"]
    frame["score_rank"] = grouped.rank(method="min", ascending=False)
    frame["score_mean"] = grouped.transform("mean")
    frame["score_sd"] = grouped.transform("std")
    frame["score_z"] = (frame["score"] - frame["score_mean"]) / frame["score_sd"]
    frame["score_top"] = frame["score"].eq(grouped.transform("max"))
    frame["acreage_rank"] = frame.groupby(["state", "year"])["planted_acres_1000"].rank(
        method="min", ascending=False
    )
    frame["acreage_top"] = frame["planted_acres_1000"].eq(
        frame.groupby(["state", "year"])["planted_acres_1000"].transform("max")
    )
    return frame


def build_transition_panel(panel: pd.DataFrame) -> pd.DataFrame:
    outputs: list[pd.DataFrame] = []
    for definition, score_col in SCORE_COLUMNS.items():
        current = _score_rank_and_z(panel, score_col)
        lag = current.rename(columns={
            "year": "lag_year", "observed_acreage_share": "lag_acreage_share",
            "planted_acres_1000": "lag_planted_acres_1000", "score": "lag_score",
            "score_rank": "lag_score_rank", "score_mean": "lag_score_mean",
            "score_sd": "lag_score_sd", "score_z": "lag_score_z",
            "score_top": "lag_score_top", "acreage_rank": "lag_acreage_rank",
            "acreage_top": "lag_acreage_top",
        })
        lag["decision_year"] = lag["lag_year"] + 1
        merged = current.merge(
            lag[["state", "crop", "decision_year", "lag_year", "lag_acreage_share",
                 "lag_planted_acres_1000", "lag_score", "lag_score_rank", "lag_score_z",
                 "lag_score_top", "lag_acreage_rank", "lag_acreage_top"]],
            left_on=["state", "crop", "year"], right_on=["state", "crop", "decision_year"],
            how="inner", validate="one_to_one",
        )
        merged["ranking_definition"] = definition
        merged["acreage_share_change"] = merged["observed_acreage_share"] - merged["lag_acreage_share"]
        merged["score_rank_change"] = merged["score_rank"] - merged["lag_score_rank"]
        merged["acreage_rank_change"] = merged["acreage_rank"] - merged["lag_acreage_rank"]
        merged["timing_status"] = "LAGGED_SCORE_PRECEDES_DECISION_YEAR_ACREAGE"
        merged["claim_level"] = "DESCRIPTIVE_TRANSITION_NOT_CAUSAL"
        outputs.append(merged)
    result = pd.concat(outputs, ignore_index=True)
    columns = [
        "state", "decision_year", "lag_year", "crop", "ranking_definition",
        "lag_score", "lag_score_rank", "lag_score_z", "lag_score_top",
        "lag_acreage_share", "observed_acreage_share", "acreage_share_change",
        "lag_acreage_rank", "acreage_rank", "acreage_rank_change",
        "score_rank", "score_rank_change", "lag_acreage_top", "acreage_top",
        "timing_status", "claim_level",
    ]
    return result[columns].sort_values(["ranking_definition", "state", "decision_year", "crop"]).reset_index(drop=True)


def rank_transition_events(transition: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for (definition, state, year), part in transition.groupby(
        ["ranking_definition", "state", "decision_year"], sort=True
    ):
        indexed = part.set_index("crop")
        inversions = 0
        ties = 0
        for crop_a, crop_b in itertools.combinations(CROPS, 2):
            score_diff = float(indexed.loc[crop_a, "lag_score"] - indexed.loc[crop_b, "lag_score"])
            acreage_diff = float(indexed.loc[crop_a, "observed_acreage_share"] - indexed.loc[crop_b, "observed_acreage_share"])
            product = score_diff * acreage_diff
            inversions += int(product < 0)
            ties += int(product == 0)
        lag_score_top = sorted(part.loc[part["lag_score_top"], "crop"])
        current_score_top = sorted(part.loc[part["score_rank"].eq(1), "crop"])
        lag_acreage_top = sorted(part.loc[part["lag_acreage_top"], "crop"])
        current_acreage_top = sorted(part.loc[part["acreage_top"], "crop"])
        lag_top_change = part.loc[part["lag_score_top"], "acreage_share_change"].mean()
        other_change = part.loc[~part["lag_score_top"], "acreage_share_change"].mean()
        rows.append({
            "ranking_definition": definition, "state": state, "decision_year": int(year),
            "lag_score_top_crops": ";".join(lag_score_top),
            "current_score_top_crops": ";".join(current_score_top),
            "lag_acreage_top_crops": ";".join(lag_acreage_top),
            "current_acreage_top_crops": ";".join(current_acreage_top),
            "score_top_changed": lag_score_top != current_score_top,
            "acreage_top_changed": lag_acreage_top != current_acreage_top,
            "lag_score_top_matches_current_acreage_top": bool(set(lag_score_top) & set(current_acreage_top)),
            "lagged_pairwise_inversions": inversions, "lagged_pairwise_ties": ties,
            "lagged_inversion_intensity": inversions / 3.0,
            "lagged_top_minus_other_share_change": float(lag_top_change - other_change),
            "claim_level": "DESCRIPTIVE_RANK_TRANSITION_NOT_CAUSAL",
        })
    return pd.DataFrame(rows)


def _cluster_bootstrap_mean(
    frame: pd.DataFrame, column: str, replications: int, seed: int,
) -> tuple[float, float, float]:
    grouped = frame.groupby("state", sort=True)[column].agg(["sum", "count"])
    sums = grouped["sum"].to_numpy(float)
    counts = grouped["count"].to_numpy(float)
    rng = np.random.default_rng(seed)
    weights = rng.multinomial(len(grouped), np.full(len(grouped), 1 / len(grouped)), size=replications)
    draws = (weights @ sums) / (weights @ counts)
    low, high = np.quantile(draws, [0.025, 0.975])
    return float(frame[column].mean()), float(low), float(high)


def _summary_with_bootstrap(
    frame: pd.DataFrame, group_col: str, metrics: dict[str, str],
    design: dict, seed_offset: int,
) -> pd.DataFrame:
    rows: list[dict] = []
    reps = int(design["uncertainty"]["replications"])
    base_seed = int(design["uncertainty"]["seed"]) + seed_offset
    for group_index, (group, part) in enumerate(frame.groupby(group_col, sort=True)):
        for metric_index, (metric, column) in enumerate(metrics.items()):
            estimate, low, high = _cluster_bootstrap_mean(
                part, column, reps, base_seed + 100 * group_index + metric_index
            )
            rows.append({
                group_col: group, "metric": metric, "estimate": estimate,
                "ci_low": low, "ci_high": high, "states": part["state"].nunique(),
                "observations": len(part), "uncertainty_unit": "STATE_CLUSTER",
                "bootstrap_replications": reps,
            })
    return pd.DataFrame(rows)


def concurrent_inversion_summary(detail: pd.DataFrame, design: dict) -> pd.DataFrame:
    metrics = {
        "inversion_intensity": "inversion_distance",
        "top_rank_reversal_rate": "top_rank_reversal",
        "strong_reversal_rate": "strong_reversal",
    }
    summary = _summary_with_bootstrap(detail, "ranking_definition", metrics, design, 1000)
    summary["timing"] = "CONCURRENT_REALIZED_SCORE"
    summary["claim_level"] = "DESCRIPTIVE_IDENTIFIED_OR_ACCOUNTING_IDENTIFIED"
    return summary


def transition_summary(events: pd.DataFrame, design: dict) -> pd.DataFrame:
    metrics = {
        "lagged_inversion_intensity": "lagged_inversion_intensity",
        "lagged_top_match_rate": "lag_score_top_matches_current_acreage_top",
        "lagged_top_minus_other_share_change": "lagged_top_minus_other_share_change",
        "score_top_change_rate": "score_top_changed",
        "acreage_top_change_rate": "acreage_top_changed",
    }
    summary = _summary_with_bootstrap(events, "ranking_definition", metrics, design, 2000)
    summary["timing"] = "LAGGED_ROLLING_ORIGIN"
    summary["claim_level"] = "DESCRIPTIVE_TRANSITION_NOT_CAUSAL"
    return summary


def definition_agreement(detail: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for left, right in itertools.combinations(sorted(detail["ranking_definition"].unique()), 2):
        lpart = detail.loc[detail["ranking_definition"].eq(left),
                           ["state", "year", "inversion_distance", "top_rank_reversal"]]
        rpart = detail.loc[detail["ranking_definition"].eq(right),
                           ["state", "year", "inversion_distance", "top_rank_reversal"]]
        merged = lpart.merge(rpart, on=["state", "year"], suffixes=("_left", "_right"), validate="one_to_one")
        rows.append({
            "definition_left": left, "definition_right": right,
            "state_years": len(merged),
            "inversion_intensity_correlation": merged["inversion_distance_left"].corr(merged["inversion_distance_right"]),
            "top_reversal_agreement": (merged["top_rank_reversal_left"] == merged["top_rank_reversal_right"]).mean(),
            "top_reversal_both": (merged["top_rank_reversal_left"] & merged["top_rank_reversal_right"]).mean(),
            "claim_level": "DESCRIPTIVE_DEFINITION_SENSITIVITY",
        })
    return pd.DataFrame(rows)


def state_year_heterogeneity(detail: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    state = detail.groupby(["ranking_definition", "state"], sort=True).agg(
        years=("year", "nunique"), mean_inversion_intensity=("inversion_distance", "mean"),
        minimum_inversion_intensity=("inversion_distance", "min"),
        maximum_inversion_intensity=("inversion_distance", "max"),
        top_reversal_rate=("top_rank_reversal", "mean"),
    ).reset_index()
    state["claim_level"] = "DESCRIPTIVE_STATE_HETEROGENEITY_NO_STATE_RANKING"
    year = detail.groupby(["ranking_definition", "year"], sort=True).agg(
        states=("state", "nunique"), mean_inversion_intensity=("inversion_distance", "mean"),
        top_reversal_rate=("top_rank_reversal", "mean"),
        strong_reversal_rate=("strong_reversal", "mean"),
    ).reset_index()
    year["claim_level"] = "DESCRIPTIVE_YEAR_HETEROGENEITY"
    return state, year


def leave_one_state_out(detail: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for definition, part in detail.groupby("ranking_definition", sort=True):
        for omitted in sorted(part["state"].unique()):
            kept = part.loc[part["state"].ne(omitted)]
            rows.append({
                "ranking_definition": definition, "omitted_state": omitted,
                "state_years": len(kept),
                "mean_inversion_intensity": kept["inversion_distance"].mean(),
                "top_reversal_rate": kept["top_rank_reversal"].mean(),
                "strong_reversal_rate": kept["strong_reversal"].mean(),
            })
    return pd.DataFrame(rows)


def _fit_inertia(frame: pd.DataFrame) -> dict[str, float]:
    year_2024 = frame["decision_year"].eq(2024).astype(float).to_numpy()
    score = frame["lag_score_z"].to_numpy(float)
    lag_share = frame["lag_acreage_share"].to_numpy(float)
    design = np.column_stack([np.ones(len(frame)), score, lag_share, score * lag_share, year_2024])
    outcome = frame["acreage_share_change"].to_numpy(float)
    coefficient = np.linalg.lstsq(design, outcome, rcond=None)[0]
    return dict(zip(["intercept", "lag_score_z", "lag_acreage_share", "score_x_lag_share", "year_2024"], coefficient))


def inertia_association(transition: pd.DataFrame, design: dict) -> pd.DataFrame:
    rows: list[dict] = []
    reps = int(design["uncertainty"]["replications"])
    seed = int(design["uncertainty"]["seed"]) + 3000
    for group_index, (definition, part) in enumerate(transition.groupby("ranking_definition", sort=True)):
        states = np.array(sorted(part["state"].unique()))
        observed = _fit_inertia(part)
        names = list(observed)
        xtx = np.empty((len(states), len(names), len(names)))
        xty = np.empty((len(states), len(names)))
        for state_index, state in enumerate(states):
            state_frame = part.loc[part["state"].eq(state)]
            score = state_frame["lag_score_z"].to_numpy(float)
            lag_share = state_frame["lag_acreage_share"].to_numpy(float)
            matrix = np.column_stack([
                np.ones(len(state_frame)), score, lag_share, score * lag_share,
                state_frame["decision_year"].eq(2024).astype(float).to_numpy(),
            ])
            outcome = state_frame["acreage_share_change"].to_numpy(float)
            xtx[state_index] = matrix.T @ matrix
            xty[state_index] = matrix.T @ outcome
        rng = np.random.default_rng(seed + group_index)
        weights = rng.multinomial(len(states), np.full(len(states), 1 / len(states)), size=reps)
        boot_xtx = np.einsum("rs,sij->rij", weights, xtx)
        boot_xty = np.einsum("rs,sj->rj", weights, xty)
        coefficients = np.empty((reps, len(names)))
        for index in range(reps):
            coefficients[index] = np.linalg.lstsq(boot_xtx[index], boot_xty[index], rcond=None)[0]
        for term_index, (name, value) in enumerate(observed.items()):
            low, high = np.quantile(coefficients[:, term_index], [0.025, 0.975])
            rows.append({
                "ranking_definition": definition, "term": name, "estimate": value,
                "ci_low": low, "ci_high": high, "states": len(states),
                "crop_transitions": len(part), "bootstrap_replications": reps,
                "proxy_status": "PRIOR_ACREAGE_INERTIA_PROXY_NOT_OPERATIONAL_CONSTRAINT",
                "claim_level": "DESCRIPTIVE_ASSOCIATION_NOT_CAUSAL",
            })
    return pd.DataFrame(rows)


def national_definition_analysis(panel: pd.DataFrame, national: pd.DataFrame, parsed: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    national_yield = parsed.loc[parsed["state"].eq("United States"),
                                ["year", "crop", "yield_bushels_per_acre", "planted_acres_1000"]].copy()
    economics = national.copy()
    economics["crop"] = economics["crop"].map({"corn": "corn", "soybeans": "soybeans", "wheat": "winter_wheat"})
    economics = economics.loc[economics["year"].between(2022, 2024)]
    merged = national_yield.merge(economics, on=["year", "crop"], how="left", validate="one_to_one")
    merged["relative_yield"] = 1.0
    deflator = merged["cpi_u_deflator_to_2024"]
    revenue = merged["yield_bushels_per_acre"] * merged["harvest_price_usd_per_bushel"]
    merged["standardized_revenue_real_2024_usd_per_acre"] = revenue * deflator
    merged["standardized_operating_margin_real_2024_usd_per_acre"] = (
        revenue - merged["operating_cost_usd_per_planted_acre"]
    ) * deflator
    merged["standardized_total_cost_margin_real_2024_usd_per_acre"] = (
        revenue - merged["total_cost_usd_per_planted_acre"]
    ) * deflator
    detail_rows: list[dict] = []
    for definition, score_col in SCORE_COLUMNS.items():
        for year, part in merged.groupby("year", sort=True):
            inversions, ties = _pairwise_inversions(part, score_col)
            score_top = set(part.loc[part[score_col].eq(part[score_col].max()), "crop"])
            acreage_top = set(part.loc[part["planted_acres_1000"].eq(part["planted_acres_1000"].max()), "crop"])
            informative = len(score_top) < len(CROPS)
            detail_rows.append({
                "ranking_definition": definition, "year": int(year),
                "pairwise_inversions": inversions, "pairwise_ties": ties,
                "inversion_intensity": inversions / 3.0,
                "top_rank_reversal": bool(score_top.isdisjoint(acreage_top)) if informative else False,
                "score_informative": informative,
                "score_top_crops": ";".join(sorted(score_top)),
                "acreage_top_crops": ";".join(sorted(acreage_top)),
                "claim_level": "NATIONAL_DESCRIPTIVE_AGGREGATION_CHECK",
            })
    detail = pd.DataFrame(detail_rows)
    state_summary = panel[["state", "year"]].drop_duplicates().groupby("year").size()
    summary = detail.groupby("ranking_definition", sort=True).agg(
        national_years=("year", "size"), informative_years=("score_informative", "sum"),
        national_mean_inversion_intensity=("inversion_intensity", "mean"),
        national_top_reversal_rate=("top_rank_reversal", "mean"),
        national_pairwise_ties=("pairwise_ties", "sum"),
    ).reset_index()
    summary["claim_level"] = "DESCRIPTIVE_AGGREGATION_BOUNDARY"
    return detail, summary


def model_observed_boundary() -> pd.DataFrame:
    rows = [
        ("state planted acreage", "DIRECTLY_OBSERVED", "yes", "no", "aggregate outcome; not an optimizer"),
        ("state realized yield", "DIRECTLY_OBSERVED", "yes", "no", "concurrent outcome; lagged use is pre-decision proxy"),
        ("standardized revenue and margins", "ACCOUNTING_CONSTRUCTED", "yes", "no", "national price/cost mismatch"),
        ("rank transitions and inversion intensity", "DESCRIPTIVE_DERIVED", "yes", "no", "ordering summaries only"),
        ("E2 allocations and KKT pressures", "MODEL_GENERATED", "no", "yes", "controlled synthetic evidence"),
        ("E6 information value", "MODEL_GENERATED", "no", "yes", "controlled finite/synthetic evidence"),
        ("private budgets, rotations and contracts", "UNIDENTIFIED", "no", "no", "not in admitted data"),
        ("farmer objective, CVaR limit and beliefs", "UNIDENTIFIED", "no", "no", "not recoverable from aggregate acreage"),
        ("copula causality and welfare", "UNIDENTIFIED", "no", "no", "no causal design or farm law"),
    ]
    return pd.DataFrame(rows, columns=["construct", "evidence_layer", "observed_output", "model_output", "boundary"])


def claim_boundaries() -> pd.DataFrame:
    rows = [
        ("rank transitions", "DESCRIPTIVE_IDENTIFIED", "official acreage and yield with explicit timing"),
        ("inversion intensity", "DESCRIPTIVE_IDENTIFIED", "complete three-crop state-years"),
        ("accounting definition comparison", "ACCOUNTING_IDENTIFIED", "national price/cost mismatch remains explicit"),
        ("lagged score-share association", "MODEL_CONSISTENT_ASSOCIATION_WITH_EXPLICIT_ALTERNATIVES", "prior scores precede acreage but do not isolate a mechanism"),
        ("prior-acreage inertia proxy", "DESCRIPTIVE_INERTIA_PROXY_NOT_CONSTRAINT", "lagged share is observed but is not a rotation/budget/contract measure"),
        ("county heterogeneity", "NOT_IDENTIFIED", "no admitted county snapshot"),
        ("private operational constraints", "NOT_IDENTIFIED", "budgets, rotation limits and contracts absent"),
        ("observed acreage optimality", "NOT_IDENTIFIED", "private feasible sets and objectives absent"),
        ("CVaR preference or binding", "NOT_IDENTIFIED", "farmer risk limit and decision loss law absent"),
        ("copula mechanism or causality", "NOT_IDENTIFIED", "three aggregate years cannot identify farmer beliefs"),
        ("welfare effect", "NOT_IDENTIFIED", "no causal design or identified objective"),
    ]
    return pd.DataFrame(rows, columns=["claim_domain", "status", "reason"])
