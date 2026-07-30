"""Frozen GOAL-16 extended official-data empirical analysis."""

from __future__ import annotations

import hashlib
import itertools
import math
import re
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from pypdf import PdfReader
from scipy import stats
import yaml


ROOT = Path(__file__).resolve().parents[3]
DESIGN_PATH = ROOT / "empirical/configs/goal16_empirical_design.yaml"
CROPS = ["corn", "soybeans", "winter_wheat"]
NATIONAL_CROP_MAP = {"corn": "corn", "soybeans": "soybeans", "winter_wheat": "wheat"}
SCORE_COLUMNS = {
    "relative_yield": "relative_yield",
    "standardized_revenue": "standardized_revenue_real_2024_usd_per_acre",
    "operating_margin": "standardized_operating_margin_real_2024_usd_per_acre",
    "total_cost_margin": "standardized_total_cost_margin_real_2024_usd_per_acre",
}
TABLE_TITLES = {
    "corn": "Corn Area Planted for All Purposes and Harvested for Grain, Yield, and Production",
    "soybeans": "Soybeans for Beans Area Planted and Harvested, Yield, and Production",
    "winter_wheat": "Winter Wheat Area Planted and Harvested, Yield, and Production",
}
MISSING = {"(NA)", "(D)", "(Z)"}
VALUE_RE = re.compile(r"\(NA\)|\(D\)|\(Z\)|-?\d[\d,]*(?:\.\d+)?")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_design(path: Path = DESIGN_PATH) -> dict:
    design = yaml.safe_load(path.read_text(encoding="utf-8"))
    if design.get("status") != "FROZEN_BEFORE_EXTENDED_RESULTS":
        raise ValueError("GOAL-16 empirical design is not frozen")
    design["design_sha256"] = sha256_file(path)
    return design


def _value(token: str) -> float:
    return math.nan if token in MISSING else float(token.replace(",", ""))


def _parse_table_page(text: str, years: list[int], value_kind: str) -> dict[str, list[float]]:
    rows: dict[str, list[float]] = {}
    for line in text.splitlines():
        parts = re.split(r"\.{2,}", line, maxsplit=1)
        if len(parts) != 2:
            continue
        state = re.sub(r"\s+\d+$", "", parts[0].strip())
        state = re.sub(r"\s+", " ", state)
        if not state or state in {"State", "States"}:
            continue
        values = VALUE_RE.findall(parts[1])
        if len(values) < 2 * len(years):
            continue
        selected = values[: len(years)]
        rows[state] = [_value(token) for token in selected]
        if state == "United States":
            break
    if "United States" not in rows:
        raise ValueError(f"{value_kind} table lacks United States total")
    return rows


def parse_annual_summary_pdf(path: Path, source_url: str) -> pd.DataFrame:
    path = path.resolve()
    reader = PdfReader(path)
    page_text = []
    for page in reader.pages:
        try:
            page_text.append(page.extract_text(extraction_mode="layout") or "")
        except KeyError:
            # Some older annual summaries contain intentionally blank pages
            # without a /Contents object.
            page_text.append("")
    rows: list[dict[str, object]] = []
    for crop, title in TABLE_TITLES.items():
        candidates = [(index, text) for index, text in enumerate(page_text) if title in text]
        area = next(
            (
                item
                for item in candidates
                if "(continued)" not in item[1][:500]
                and "Area planted" in item[1][:1200]
                and "(1,000 acres)" in item[1][:1800]
            ),
            None,
        )
        crop_yield = next(
            (
                item
                for item in candidates
                if "(continued)" in item[1][:500]
                and "Yield per acre" in item[1][:1200]
                and "(bushels)" in item[1][:1800]
            ),
            None,
        )
        if area is None or crop_yield is None:
            raise ValueError(f"could not find both {crop} table panels in {path}")
        match = re.search(r"United States:\s*(\d{4})-(\d{4})", area[1])
        if not match:
            raise ValueError(f"could not find year range for {crop} in {path}")
        first, last = (int(value) for value in match.groups())
        years = list(range(first, last + 1))
        if len(years) != 3:
            raise ValueError(f"expected three annual columns in {path}, got {years}")
        areas = _parse_table_page(area[1], years, "area")
        yields = _parse_table_page(crop_yield[1], years, "yield")
        if set(areas) != set(yields):
            raise ValueError(f"area/yield geography mismatch for {crop} in {path}")
        for state in sorted(areas):
            for index, year in enumerate(years):
                rows.append(
                    {
                        "state": state,
                        "year": year,
                        "crop": crop,
                        "planted_acres_1000": areas[state][index],
                        "yield_bushels_per_acre": yields[state][index],
                        "source_path": path.relative_to(ROOT).as_posix(),
                        "source_url": source_url,
                        "source_sha256": sha256_file(path),
                        "source_report_year": last,
                        "source_unit_acres": "1,000 acres",
                        "source_unit_yield": "bushels per acre",
                    }
                )
    frame = pd.DataFrame(rows).sort_values(["state", "year", "crop"]).reset_index(drop=True)
    if frame.duplicated(["state", "year", "crop"]).any():
        raise ValueError(f"duplicate state-year-crop in {path}")
    return frame


def parse_frozen_state_sources(design: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    source_rows = []
    for source in design["state_sources"]:
        path = ROOT / source["path"]
        frame = parse_annual_summary_pdf(path, source["url"])
        expected = set(source["included_years"])
        if set(frame["year"].unique()) != expected:
            raise ValueError(f"unexpected years in {path}: {sorted(frame['year'].unique())}")
        frames.append(frame)
        source_rows.append(
            {
                "source_id": f"DATA-NASS-CROPAN-{source['report_year']}",
                "authority": "USDA National Agricultural Statistics Service",
                "dataset": f"Crop Production {source['report_year']} Summary",
                "official_url": source["url"],
                "local_path": source["path"],
                "sha256": sha256_file(path),
                "time_support": ";".join(str(value) for value in source["included_years"]),
                "geography": "United States and states",
                "variables": "planted acreage;yield",
                "status": "INCLUDED",
                "retrieved_at": source["retrieved_at"],
            }
        )
    for source in design["audit_only_sources"]:
        path = ROOT / source["path"]
        audit_frame = parse_annual_summary_pdf(path, source["url"])
        source_rows.append(
            {
                "source_id": f"DATA-NASS-CROPAN-{source['report_year']}",
                "authority": "USDA National Agricultural Statistics Service",
                "dataset": f"Crop Production {source['report_year']} Summary",
                "official_url": source["url"],
                "local_path": source["path"],
                "sha256": sha256_file(path),
                "time_support": ";".join(str(value) for value in sorted(audit_frame["year"].unique())),
                "geography": "United States and states",
                "variables": "planted acreage;yield",
                "status": "AUDIT_ONLY_EXCLUDED_BY_FROZEN_RULE",
                "retrieved_at": source["retrieved_at"],
            }
        )
    combined = pd.concat(frames, ignore_index=True)
    if combined.duplicated(["state", "year", "crop"]).any():
        raise ValueError("frozen non-overlapping source blocks produced duplicates")
    return combined.sort_values(["state", "year", "crop"]).reset_index(drop=True), pd.DataFrame(source_rows)


def build_extended_panel(raw: pd.DataFrame, national_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    states = raw.loc[raw["state"].ne("United States")].copy()
    missing = []
    for column in ["planted_acres_1000", "yield_bushels_per_acre"]:
        for (year, crop), part in states.groupby(["year", "crop"], sort=True):
            missing.append(
                {
                    "year": year,
                    "crop": crop,
                    "variable": column,
                    "reported_rows": len(part),
                    "missing_rows": int(part[column].isna().sum()),
                    "nonmissing_rows": int(part[column].notna().sum()),
                }
            )
    usable = states.dropna(subset=["planted_acres_1000", "yield_bushels_per_acre"])
    counts = usable.groupby(["state", "year"])["crop"].nunique()
    keys = counts.loc[counts.eq(len(CROPS))].index
    complete = usable.set_index(["state", "year"]).loc[keys].reset_index()
    complete = complete.loc[complete["crop"].isin(CROPS)].copy()
    if complete.groupby(["state", "year"])["crop"].nunique().ne(3).any():
        raise ValueError("three-crop completeness restriction failed")

    national_nass = raw.loc[raw["state"].eq("United States")].rename(
        columns={
            "yield_bushels_per_acre": "national_nass_yield_bushels_per_acre",
            "planted_acres_1000": "national_planted_acres_1000",
        }
    )
    complete = complete.merge(
        national_nass[["year", "crop", "national_nass_yield_bushels_per_acre", "national_planted_acres_1000"]],
        on=["year", "crop"],
        how="left",
        validate="many_to_one",
    )
    national = pd.read_csv(national_path)
    national["crop"] = national["crop"].map({value: key for key, value in NATIONAL_CROP_MAP.items()})
    fields = [
        "year",
        "crop",
        "harvest_price_usd_per_bushel",
        "operating_cost_usd_per_planted_acre",
        "total_cost_usd_per_planted_acre",
        "cpi_u_deflator_to_2024",
    ]
    complete = complete.merge(national[fields], on=["year", "crop"], how="left", validate="many_to_one")
    if complete[fields[2:]].isna().any().any():
        raise ValueError("national economics join is incomplete")
    deflator = complete["cpi_u_deflator_to_2024"]
    revenue = complete["yield_bushels_per_acre"] * complete["harvest_price_usd_per_bushel"]
    complete["relative_yield"] = complete["yield_bushels_per_acre"] / complete["national_nass_yield_bushels_per_acre"]
    complete["standardized_revenue_real_2024_usd_per_acre"] = revenue * deflator
    complete["standardized_operating_margin_real_2024_usd_per_acre"] = (
        revenue - complete["operating_cost_usd_per_planted_acre"]
    ) * deflator
    complete["standardized_total_cost_margin_real_2024_usd_per_acre"] = (
        revenue - complete["total_cost_usd_per_planted_acre"]
    ) * deflator
    complete["observed_acreage_share"] = complete["planted_acres_1000"] / complete.groupby(
        ["state", "year"]
    )["planted_acres_1000"].transform("sum")
    complete["geographic_price_cost_scope"] = "STATE_YIELD_WITH_NATIONAL_PRICE_AND_COST"
    complete["observed_allocation_interpretation"] = "AGGREGATE_ACREAGE_NOT_MODEL_OPTIMUM"

    raw_state_rows = len(states)
    usable_rows = len(usable)
    flow = pd.DataFrame(
        [
            ("parsed state-crop-year rows", raw_state_rows, 0),
            ("nonmissing acreage and yield", usable_rows, raw_state_rows - usable_rows),
            ("complete three-crop rows", len(complete), usable_rows - len(complete)),
            ("complete state-years", complete[["state", "year"]].drop_duplicates().shape[0], math.nan),
        ],
        columns=["stage", "retained", "excluded_from_prior_stage"],
    )
    return complete.sort_values(["state", "year", "crop"]).reset_index(drop=True), pd.DataFrame(missing), flow


def rank_metrics(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    detail = []
    ranking_rows = []
    for definition, score_column in SCORE_COLUMNS.items():
        for (state, year), part in panel.groupby(["state", "year"], sort=True):
            part = part.copy()
            part["score_rank"] = part[score_column].rank(method="average", ascending=False)
            part["acreage_rank"] = part["planted_acres_1000"].rank(method="average", ascending=False)
            score = part[score_column].to_numpy(float)
            acreage = part["planted_acres_1000"].to_numpy(float)
            tau = stats.kendalltau(score, acreage, variant="b").statistic
            rho = stats.spearmanr(score, acreage).statistic if np.std(score) > 0 and np.std(acreage) > 0 else math.nan
            score_top = set(part.loc[part[score_column].eq(part[score_column].max()), "crop"])
            acreage_top = set(part.loc[part["planted_acres_1000"].eq(part["planted_acres_1000"].max()), "crop"])
            inversions = ties = 0
            for crop_a, crop_b in itertools.combinations(CROPS, 2):
                indexed = part.set_index("crop")
                product = float(indexed.loc[crop_a, score_column] - indexed.loc[crop_b, score_column]) * float(
                    indexed.loc[crop_a, "planted_acres_1000"] - indexed.loc[crop_b, "planted_acres_1000"]
                )
                inversions += int(product < 0)
                ties += int(product == 0)
            ordered = np.sort(score)[::-1]
            detail.append(
                {
                    "state": state,
                    "year": int(year),
                    "ranking_definition": definition,
                    "kendall_tau_b": tau,
                    "spearman_rho": rho,
                    "spearman_valid": not math.isnan(rho),
                    "pairwise_inversions": inversions,
                    "pairwise_ties": ties,
                    "inversion_intensity": inversions / 3.0,
                    "top_rank_disagreement": bool(score_top.isdisjoint(acreage_top)),
                    "score_leader_unique": len(score_top) == 1,
                    "acreage_leader_unique": len(acreage_top) == 1,
                    "score_leaders": ";".join(sorted(score_top)),
                    "acreage_leaders": ";".join(sorted(acreage_top)),
                    "score_top_second_gap": float(ordered[0] - ordered[1]),
                    "claim_level": "DESCRIPTIVE_RANK_AGREEMENT_NOT_CAUSAL",
                }
            )
            for _, row in part.iterrows():
                ranking_rows.append(
                    {
                        "state": state,
                        "year": int(year),
                        "crop": row["crop"],
                        "ranking_definition": definition,
                        "score": row[score_column],
                        "score_rank": row["score_rank"],
                        "planted_acres_1000": row["planted_acres_1000"],
                        "acreage_rank": row["acreage_rank"],
                        "observed_acreage_share": row["observed_acreage_share"],
                        "score_top": row["crop"] in score_top,
                        "acreage_top": row["crop"] in acreage_top,
                    }
                )
    return pd.DataFrame(detail), pd.DataFrame(ranking_rows)


def cluster_bootstrap_summary(detail: pd.DataFrame, design: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    metrics = ["kendall_tau_b", "spearman_rho", "inversion_intensity", "top_rank_disagreement"]
    reps = int(design["uncertainty"]["replications"])
    seed = int(design["uncertainty"]["seed"])
    summaries = []
    draws = []
    for definition_index, (definition, part) in enumerate(detail.groupby("ranking_definition", sort=True)):
        states = np.array(sorted(part["state"].unique()))
        groups = {state: part.loc[part["state"].eq(state)] for state in states}
        rng = np.random.default_rng(seed + definition_index)
        for replication in range(reps):
            sample = rng.choice(states, len(states), replace=True)
            draw = pd.concat([groups[state] for state in sample], ignore_index=True)
            record = {"ranking_definition": definition, "replication": replication + 1}
            for metric in metrics:
                record[metric] = float(draw[metric].astype(float).mean())
            draws.append(record)
        draw_frame = pd.DataFrame(draws[-reps:])
        for metric in metrics:
            values = part[metric].astype(float)
            low, high = np.quantile(draw_frame[metric], [0.025, 0.975])
            summaries.append(
                {
                    "ranking_definition": definition,
                    "metric": metric,
                    "estimate": values.mean(),
                    "ci_low": low,
                    "ci_high": high,
                    "states": len(states),
                    "state_years": len(part),
                    "bootstrap_replications": reps,
                    "uncertainty_unit": "STATE_CLUSTER",
                }
            )
    return pd.DataFrame(summaries), pd.DataFrame(draws)


def transitions(ranking: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    crop_rows = []
    events = []
    for definition, part in ranking.groupby("ranking_definition", sort=True):
        current = part.copy()
        lag = current.rename(
            columns={
                "year": "lag_year",
                "score": "prior_score",
                "score_rank": "prior_score_rank",
                "observed_acreage_share": "prior_acreage_share",
                "acreage_rank": "prior_acreage_rank",
                "score_top": "prior_score_top",
                "acreage_top": "prior_acreage_top",
            }
        )
        lag["decision_year"] = lag["lag_year"] + 1
        merged = current.merge(
            lag[
                [
                    "state",
                    "crop",
                    "decision_year",
                    "lag_year",
                    "prior_score",
                    "prior_score_rank",
                    "prior_acreage_share",
                    "prior_acreage_rank",
                    "prior_score_top",
                    "prior_acreage_top",
                ]
            ],
            left_on=["state", "crop", "year"],
            right_on=["state", "crop", "decision_year"],
            how="inner",
            validate="one_to_one",
        )
        merged["ranking_definition"] = definition
        merged["acreage_share_change"] = merged["observed_acreage_share"] - merged["prior_acreage_share"]
        merged["score_rank_change"] = merged["score_rank"] - merged["prior_score_rank"]
        merged["acreage_rank_change"] = merged["acreage_rank"] - merged["prior_acreage_rank"]
        merged["timing_status"] = "STRICTLY_LAGGED_NO_LOOKAHEAD"
        crop_rows.append(merged)
        for (state, year), cell in merged.groupby(["state", "decision_year"], sort=True):
            prior_score = set(cell.loc[cell["prior_score_top"], "crop"])
            score_now = set(cell.loc[cell["score_top"], "crop"])
            prior_acreage = set(cell.loc[cell["prior_acreage_top"], "crop"])
            acreage_now = set(cell.loc[cell["acreage_top"], "crop"])
            top_change = cell.loc[cell["prior_score_top"], "acreage_share_change"].mean()
            other_change = cell.loc[~cell["prior_score_top"], "acreage_share_change"].mean()
            score_changed = prior_score != score_now
            acreage_changed = prior_acreage != acreage_now
            category = "both" if score_changed and acreage_changed else (
                "score_only" if score_changed else ("acreage_only" if acreage_changed else "neither")
            )
            events.append(
                {
                    "ranking_definition": definition,
                    "state": state,
                    "decision_year": int(year),
                    "score_leader_changed": score_changed,
                    "acreage_leader_changed": acreage_changed,
                    "transition_category": category,
                    "prior_top_minus_other_share_change": float(top_change - other_change),
                    "prior_score_leaders": ";".join(sorted(prior_score)),
                    "current_score_leaders": ";".join(sorted(score_now)),
                    "prior_acreage_leaders": ";".join(sorted(prior_acreage)),
                    "current_acreage_leaders": ";".join(sorted(acreage_now)),
                }
            )
    crop_frame = pd.concat(crop_rows, ignore_index=True)
    event_frame = pd.DataFrame(events)
    transition_summary = (
        event_frame.groupby(["ranking_definition", "transition_category"], sort=True)
        .size()
        .rename("events")
        .reset_index()
    )
    transition_summary["share"] = transition_summary["events"] / transition_summary.groupby(
        "ranking_definition"
    )["events"].transform("sum")
    return crop_frame, event_frame, transition_summary


def _design_matrix(frame: pd.DataFrame, predictor: str, state_column: str = "state") -> tuple[np.ndarray, np.ndarray, list[str]]:
    base = pd.DataFrame(
        {
            predictor: frame[predictor].astype(float),
            "prior_acreage_share": frame["prior_acreage_share"].astype(float),
        }
    )
    dummies = pd.get_dummies(
        frame[["crop", "decision_year"]].astype(str),
        drop_first=True,
        dtype=float,
        prefix=["crop", "year"],
    )
    matrix = pd.concat([base.reset_index(drop=True), dummies.reset_index(drop=True)], axis=1)
    groups = frame[state_column].reset_index(drop=True)
    matrix = matrix - matrix.groupby(groups).transform("mean")
    outcome = frame["acreage_share_change"].reset_index(drop=True)
    outcome = outcome - outcome.groupby(groups).transform("mean")
    keep = matrix.columns[matrix.std(ddof=0).gt(1e-12)]
    matrix = matrix[keep]
    return matrix.to_numpy(float), outcome.to_numpy(float), matrix.columns.tolist()


def _fit_temporal(frame: pd.DataFrame, predictor: str, state_column: str = "state") -> tuple[float, int, int]:
    x, y, columns = _design_matrix(frame, predictor, state_column)
    coefficient = np.linalg.lstsq(x, y, rcond=None)[0]
    return float(coefficient[columns.index(predictor)]), int(np.linalg.matrix_rank(x)), len(columns)


def temporal_models(transition: pd.DataFrame, design: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    reps = int(design["uncertainty"]["replications"])
    seed = int(design["uncertainty"]["seed"]) + 1000
    results = []
    draw_rows = []
    for definition_index, (definition, part) in enumerate(transition.groupby("ranking_definition", sort=True)):
        states = np.array(sorted(part["state"].unique()))
        for spec_index, predictor in enumerate(["prior_score_top", "prior_score_rank"]):
            estimate, rank, columns = _fit_temporal(part, predictor)
            rng = np.random.default_rng(seed + 100 * definition_index + spec_index)
            x, y, matrix_columns = _design_matrix(part, predictor)
            state_values = part["state"].to_numpy()
            xtx = np.stack([x[state_values == state].T @ x[state_values == state] for state in states])
            xty = np.stack([x[state_values == state].T @ y[state_values == state] for state in states])
            weights = rng.multinomial(len(states), np.full(len(states), 1 / len(states)), size=reps)
            boot_xtx = np.einsum("rs,sij->rij", weights, xtx)
            boot_xty = np.einsum("rs,sj->rj", weights, xty)
            values = np.empty(reps)
            for replication in range(reps):
                coefficient = np.linalg.lstsq(boot_xtx[replication], boot_xty[replication], rcond=None)[0]
                values[replication] = coefficient[matrix_columns.index(predictor)]
                draw_rows.append(
                    {
                        "ranking_definition": definition,
                        "specification": "primary_top" if predictor == "prior_score_top" else "rank_sensitivity",
                        "replication": replication + 1,
                        "coefficient": values[replication],
                    }
                )
            low, high = np.quantile(values, [0.025, 0.975])
            results.append(
                {
                    "ranking_definition": definition,
                    "specification": "primary_top" if predictor == "prior_score_top" else "rank_sensitivity",
                    "term": predictor,
                    "estimate": estimate,
                    "ci_low": low,
                    "ci_high": high,
                    "state_clusters": len(states),
                    "crop_transitions": len(part),
                    "design_rank": rank,
                    "design_columns": columns,
                    "bootstrap_replications": reps,
                    "fixed_effects": "crop;decision_year;state",
                    "claim_level": "DESCRIPTIVE_ASSOCIATION_NOT_CAUSAL",
                }
            )
    return pd.DataFrame(results), pd.DataFrame(draw_rows)


def state_year_summaries(detail: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    state = detail.groupby(["ranking_definition", "state"], sort=True).agg(
        years=("year", "nunique"),
        mean_inversion_intensity=("inversion_intensity", "mean"),
        mean_kendall_tau_b=("kendall_tau_b", "mean"),
        top_disagreement_rate=("top_rank_disagreement", "mean"),
    ).reset_index()
    year = detail.groupby(["ranking_definition", "year"], sort=True).agg(
        states=("state", "nunique"),
        mean_inversion_intensity=("inversion_intensity", "mean"),
        mean_kendall_tau_b=("kendall_tau_b", "mean"),
        top_disagreement_rate=("top_rank_disagreement", "mean"),
    ).reset_index()
    leave_rows = []
    for definition, part in detail.groupby("ranking_definition", sort=True):
        for state_name in sorted(part["state"].unique()):
            kept = part.loc[part["state"].ne(state_name)]
            leave_rows.append(
                {
                    "ranking_definition": definition,
                    "omitted_state": state_name,
                    "state_years": len(kept),
                    "mean_inversion_intensity": kept["inversion_intensity"].mean(),
                    "mean_kendall_tau_b": kept["kendall_tau_b"].mean(),
                }
            )
    return state, year, pd.DataFrame(leave_rows)


def model_linked_signatures(detail: pd.DataFrame, transition: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for definition, part in detail.groupby("ranking_definition", sort=True):
        rows.append(
            {
                "ranking_definition": definition,
                "signature": "margin_separation",
                "estimate": stats.spearmanr(part["score_top_second_gap"], part["inversion_intensity"]).statistic,
                "observations": len(part),
                "definition": "Spearman association of top-second score gap with inversion intensity",
                "claim_level": "MODEL_LINKED_SIGNATURE_NOT_MECHANISM_TEST",
            }
        )
        trans = transition.loc[transition["ranking_definition"].eq(definition)]
        rows.append(
            {
                "ranking_definition": definition,
                "signature": "allocation_persistence",
                "estimate": stats.spearmanr(trans["prior_acreage_share"], trans["acreage_share_change"]).statistic,
                "observations": len(trans),
                "definition": "Spearman association of prior acreage share with subsequent share change",
                "claim_level": "MODEL_LINKED_SIGNATURE_NOT_MECHANISM_TEST",
            }
        )
        rows.append(
            {
                "ranking_definition": definition,
                "signature": "rank_share_inversion",
                "estimate": part["inversion_intensity"].mean(),
                "observations": len(part),
                "definition": "Mean concurrent pairwise inversion intensity",
                "claim_level": "MODEL_LINKED_SIGNATURE_NOT_MECHANISM_TEST",
            }
        )
    return pd.DataFrame(rows)


def national_aggregation(panel: pd.DataFrame, raw: pd.DataFrame, detail: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    national = raw.loc[raw["state"].eq("United States")].copy()
    economics = panel[
        [
            "year",
            "crop",
            "harvest_price_usd_per_bushel",
            "operating_cost_usd_per_planted_acre",
            "total_cost_usd_per_planted_acre",
            "cpi_u_deflator_to_2024",
        ]
    ].drop_duplicates(["year", "crop"])
    national = national.merge(economics, on=["year", "crop"], how="left", validate="one_to_one")
    national["relative_yield"] = 1.0
    revenue = national["yield_bushels_per_acre"] * national["harvest_price_usd_per_bushel"]
    deflator = national["cpi_u_deflator_to_2024"]
    national["standardized_revenue_real_2024_usd_per_acre"] = revenue * deflator
    national["standardized_operating_margin_real_2024_usd_per_acre"] = (
        revenue - national["operating_cost_usd_per_planted_acre"]
    ) * deflator
    national["standardized_total_cost_margin_real_2024_usd_per_acre"] = (
        revenue - national["total_cost_usd_per_planted_acre"]
    ) * deflator
    national["observed_acreage_share"] = national["planted_acres_1000"] / national.groupby("year")[
        "planted_acres_1000"
    ].transform("sum")
    national_detail, _ = rank_metrics(national.assign(state="United States"))
    state_summary = detail.groupby("ranking_definition", sort=True)["inversion_intensity"].mean()
    aggregation = national_detail.groupby("ranking_definition", sort=True).agg(
        national_years=("year", "size"),
        informative_years=("score_leader_unique", "sum"),
        national_mean_inversion_intensity=("inversion_intensity", "mean"),
        national_mean_kendall_tau_b=("kendall_tau_b", "mean"),
    ).reset_index()
    aggregation["state_mean_inversion_intensity"] = aggregation["ranking_definition"].map(state_summary)
    aggregation["aggregation_difference"] = (
        aggregation["national_mean_inversion_intensity"] - aggregation["state_mean_inversion_intensity"]
    )
    aggregation["relative_yield_national_status"] = np.where(
        aggregation["ranking_definition"].eq("relative_yield"), "ALL_SCORES_TIED_NONINFORMATIVE", "INFORMATIVE"
    )
    return national_detail, aggregation
