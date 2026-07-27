from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def _goal16():
    import sys

    sys.path.insert(0, str(ROOT / "empirical/src"))
    from crop_empirical import goal16_analysis

    return goal16_analysis


def test_2024_report_parser_reproduces_frozen_stage_ii_rows() -> None:
    module = _goal16()
    parsed = module.parse_annual_summary_pdf(
        ROOT / "empirical/goal16/raw/usda_nass/crop_production_2024_summary.pdf",
        "https://www.nass.usda.gov/Publications/Todays_Reports/reports/cropan25.pdf",
    )
    frozen = pd.read_csv(ROOT / "data/processed/nass_state_crop_2022_2024.csv")
    fields = ["state", "year", "crop", "planted_acres_1000", "yield_bushels_per_acre"]
    parsed = parsed[fields].sort_values(fields[:3]).reset_index(drop=True)
    frozen = frozen[fields].sort_values(fields[:3]).reset_index(drop=True)
    pd.testing.assert_frame_equal(parsed, frozen, check_dtype=False)


def test_extended_panel_has_registered_support_and_unit_shares() -> None:
    panel = pd.read_csv(ROOT / "empirical/goal16/outputs/extended_state_crop_panel.csv")
    assert panel["year"].drop_duplicates().sort_values().tolist() == list(range(2016, 2025))
    assert panel.groupby(["state", "year"])["crop"].nunique().eq(3).all()
    assert not panel.duplicated(["state", "year", "crop"]).any()
    sums = panel.groupby(["state", "year"])["observed_acreage_share"].sum()
    assert np.allclose(sums, 1.0, atol=1e-10)


def test_rank_metric_ties_and_inversions_are_bounded() -> None:
    detail = pd.read_csv(ROOT / "empirical/goal16/outputs/rank_metrics_state_year.csv")
    assert detail["kendall_tau_b"].dropna().between(-1, 1).all()
    assert detail["spearman_rho"].dropna().between(-1, 1).all()
    assert detail["inversion_intensity"].between(0, 1).all()
    relative_national = pd.read_csv(ROOT / "empirical/goal16/outputs/aggregation_boundary.csv")
    status = relative_national.set_index("ranking_definition").loc["relative_yield", "relative_yield_national_status"]
    assert status == "ALL_SCORES_TIED_NONINFORMATIVE"


def test_temporal_rows_are_strictly_lagged_and_uncertainty_is_complete() -> None:
    transition = pd.read_csv(ROOT / "empirical/goal16/outputs/rank_share_transitions.csv")
    assert transition["decision_year"].sub(transition["lag_year"]).eq(1).all()
    assert transition["timing_status"].eq("STRICTLY_LAGGED_NO_LOOKAHEAD").all()
    models = pd.read_csv(ROOT / "empirical/goal16/outputs/temporal_model.csv")
    assert len(models) == 8
    assert models["state_clusters"].eq(31).all()
    assert models["bootstrap_replications"].eq(5000).all()
    assert models[["estimate", "ci_low", "ci_high"]].notna().all().all()
    assert models["ci_low"].le(models["estimate"]).all()
    assert models["estimate"].le(models["ci_high"]).all()
