import json
from pathlib import Path

import pandas as pd

from crop_empirical.nass_summary import complete_state_year_sample, parse_nass_state_crop_summary

ROOT = Path(__file__).resolve().parents[1]


def test_nass_parser_reconciles_published_us_totals():
    parsed = parse_nass_state_crop_summary()
    us = parsed.loc[parsed["state"].eq("United States") & parsed["year"].eq(2024)].set_index("crop")
    assert us.loc["corn", "planted_acres_1000"] == 90594
    assert us.loc["soybeans", "planted_acres_1000"] == 87050
    assert us.loc["winter_wheat", "yield_bushels_per_acre"] == 51.7


def test_complete_case_sample_is_three_crop_state_year_panel():
    sample = complete_state_year_sample(parse_nass_state_crop_summary(), ["corn", "soybeans", "winter_wheat"])
    assert len(sample) == 231
    assert sample[["state", "year"]].drop_duplicates().shape[0] == 77
    assert sample.groupby(["state", "year"])["crop"].nunique().eq(3).all()


def test_empirical_results_preserve_null_and_boundaries():
    output = ROOT / "empirical/outputs"
    national = pd.read_csv(output / "national_check.csv")
    boundaries = pd.read_csv(output / "claim_boundaries.csv").set_index("claim_domain")
    summary = json.loads((output / "summary.json").read_text())
    assert not national["rank_reversal"].any()
    assert boundaries.loc["CVaR binding or causality", "status"] == "NOT_IDENTIFIED"
    assert summary["observed_acreage_is_optimum"] is False
    assert summary["causal_claim_admissible"] is False


def test_empirical_outputs_are_exactly_reproducible():
    replay = json.loads((ROOT / "empirical/outputs/reproducibility.json").read_text())
    assert replay["status"] == "PASS"
    assert replay["files_compared"] == 19
    assert replay["mismatched_files"] == []
