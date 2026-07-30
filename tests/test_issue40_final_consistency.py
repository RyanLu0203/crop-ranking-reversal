"""Acceptance tests for the bounded Issue #40 consistency repair."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reconstruction" / "issue34" / "outputs"
DESIGN = yaml.safe_load(
    (ROOT / "simulation" / "configs" / "issue34_full_model_design.yaml")
    .read_text(encoding="utf-8")
)


def test_issue40_uses_exact_scientific_parent_and_registered_rules():
    assert DESIGN["editorial_consistency_issue"] == 40
    assert DESIGN["editorial_consistency_baseline_commit"] == (
        "2c03e0ddd1bfa29ff8b16078d3effff592e36508"
    )
    assert DESIGN["heuristic_projection"]["principal_method"] == "euclidean_l2"
    assert DESIGN["heuristic_projection"]["total_land_equality"] is True
    assert DESIGN["heuristic_projection"]["idle_land_allowed"] is False
    assert DESIGN["heuristic_projection"]["cvar_ceiling_in_projection"] is False
    assert DESIGN["strong_reversal_sensitivity"]["primary_zero_tolerance"] == 1e-4


def test_one_canonical_selected_gaussian_mean_variance_policy():
    canonical = pd.read_csv(OUTPUT / "canonical_mean_variance_policy.csv")
    assert len(canonical) == 1
    row = canonical.iloc[0]
    assert row["policy"] == "Selected Gaussian mean-variance policy"
    assert row["source_policy_id"] == "xMV_variance_target_selected"
    assert row["selection_rule"] == (
        "smallest_gamma_achieving_fixed_gaussian_variance_reduction"
    )
    assert np.isclose(row["variance_reduction_target"], 0.15)
    assert np.isclose(row["gamma"], 0.0082)
    assert bool(row["operational_feasible"])
    assert not bool(row["risk_ceiling_feasible"])

    div = pd.read_csv(OUTPUT / "diversification_failure.csv")
    source = div.loc[div["policy"].eq(row["source_policy_id"])].iloc[0]
    comparisons = {
        "gamma": "gamma",
        "allocation_Corn": "allocation_Corn",
        "allocation_Soybean": "allocation_Soybean",
        "allocation_Winter_Wheat": "allocation_Winter_Wheat",
        "gaussian_expected_profit": "gaussian_expected_profit",
        "gaussian_profit_variance": "gaussian_profit_variance",
        "student_t_evaluation_expected_profit": "evaluation_expected_profit",
        "student_t_evaluation_loss_CVaR": "evaluation_loss_CVaR",
        "risk_ceiling": "risk_ceiling",
    }
    for canonical_column, source_column in comparisons.items():
        assert np.isclose(row[canonical_column], source[source_column])


def test_old_low_penalty_policy_is_not_a_comparison_policy():
    policies = pd.read_csv(OUTPUT / "policy_comparison.csv")
    identifiers = set(policies["policy"])
    assert "mean_variance" not in identifiers
    assert not any("low_penalty" in value for value in identifiers)
    assert identifiers == {
        "suitability_proportional_euclidean",
        "winner_take_all_euclidean",
        "equal_share_euclidean",
        "expected_profit_no_CVaR",
        "full_CVaR_operational",
        "minimum_CVaR_endpoint_not_primary",
    }


def test_principal_and_relaxed_lower_bound_phase_counts():
    summary = pd.read_csv(OUTPUT / "strong_reversal_lower_bound_summary.csv")
    primary = summary.loc[np.isclose(summary["near_zero_tolerance"], 1e-4)]
    rows = primary.set_index("lower_bound_specification")
    expected = {
        "principal_positive_lower_bounds": (143, 96, True),
        "all_zero_lower_bounds": (143, 95, False),
        "highest_ranked_crop_zero_lower_bound": (143, 96, False),
    }
    for specification, (pairwise, complete, structural) in expected.items():
        row = rows.loc[specification]
        assert int(row["cells"]) == 165
        assert int(row["feasible_cells"]) == 165
        assert int(row["infeasible_cells"]) == 0
        assert int(row["multiple_optimum_cells"]) == 2
        assert int(row["selected_pairwise_reversal_cells"]) == pairwise
        assert int(row["possible_pairwise_reversal_cells"]) == pairwise
        assert int(row["universal_pairwise_reversal_cells"]) == pairwise
        assert int(row["selected_complete_rank_reversal_cells"]) == complete
        assert int(row["possible_complete_rank_reversal_cells"]) == complete
        assert int(row["universal_complete_rank_reversal_cells"]) == complete
        assert int(row["selected_strong_reversal_cells"]) == 0
        assert int(row["possible_strong_reversal_cells"]) == 0
        assert int(row["universal_strong_reversal_cells"]) == 0
        assert bool(row["strong_reversal_structurally_inadmissible"]) is structural
        assert row["first_strong_boundary_status"] == "none_on_evaluated_grid"
        assert pd.isna(row["first_selected_strong_excluded_pair"])
        assert pd.isna(row["first_selected_strong_active_constraints"])


def test_relaxed_strong_reversal_null_holds_at_every_zero_tolerance():
    summary = pd.read_csv(OUTPUT / "strong_reversal_lower_bound_summary.csv")
    assert set(summary["near_zero_tolerance"]) == {
        1e-8, 1e-6, 1e-4, 1e-3, 1e-2
    }
    relaxed = summary.loc[
        summary["lower_bound_specification"].isin(
            ["all_zero_lower_bounds", "highest_ranked_crop_zero_lower_bound"]
        )
    ]
    for column in (
        "selected_strong_reversal_cells",
        "possible_strong_reversal_cells",
        "universal_strong_reversal_cells",
    ):
        assert relaxed[column].eq(0).all()
    assert relaxed["first_strong_boundary_status"].eq(
        "none_on_evaluated_grid"
    ).all()


def test_heuristic_projection_is_exact_and_projection_sensitive():
    frame = pd.read_csv(OUTPUT / "heuristic_projection_sensitivity.csv")
    assert len(frame) == 6
    assert frame["full_investment_required"].all()
    assert not frame["idle_land_allowed"].any()
    assert not frame["cvar_ceiling_in_projection"].any()
    assert frame["acreage_usage"].sub(1.0).abs().max() <= 1e-8
    assert frame["risk_feasible"].all()

    winner = frame.loc[frame["heuristic_policy"].eq("winner_take_all")]
    l2 = winner.loc[winner["projection_method"].eq("euclidean_l2")].iloc[0]
    l1 = winner.loc[winner["projection_method"].eq("l1_lexicographic")].iloc[0]
    assert np.allclose(
        l2[["raw_Corn", "raw_Soybean", "raw_Winter_Wheat"]].astype(float),
        [0.0, 0.0, 1.0],
    )
    assert np.allclose(
        l2[["projected_Corn", "projected_Soybean", "projected_Winter_Wheat"]]
        .astype(float),
        [0.2, 0.2, 0.6], atol=1e-7,
    )
    assert np.allclose(
        l1[["projected_Corn", "projected_Soybean", "projected_Winter_Wheat"]]
        .astype(float),
        [0.3, 0.1, 0.6], atol=1e-7,
    )
    assert np.isclose(l2["projection_distance_l2"], np.sqrt(0.24), atol=1e-7)
    assert np.isclose(l1["projection_distance_l1"], 0.8, atol=1e-7)
    assert l2["classification"] == "no_reversal"
    assert l1["classification"] == "selected_pairwise_reversal"


def test_generated_macros_match_canonical_policy():
    canonical = pd.read_csv(OUTPUT / "canonical_mean_variance_policy.csv").iloc[0]
    text = (ROOT / "manuscript" / "issue34" / "generated" / "numbers.tex")
    values = dict(
        re.findall(r"\\newcommand\{\\([^}]+)\}\{([^}]*)\}", text.read_text())
    )
    assert values["DiversificationGamma"] == f"{canonical['gamma']:.4f}"
    assert values["CanonicalMVCorn"] == f"{canonical['allocation_Corn']:.3f}"
    assert values["CanonicalMVSoy"] == f"{canonical['allocation_Soybean']:.3f}"
    assert values["CanonicalMVWheat"] == (
        f"{canonical['allocation_Winter_Wheat']:.3f}"
    )
    assert values["CanonicalMVGaussianVariance"] == (
        f"{canonical['gaussian_profit_variance']:.1f}"
    )
    assert values["CanonicalMVCVaR"] == (
        f"{canonical['student_t_evaluation_loss_CVaR']:.1f}"
    )


def test_main_and_supplement_are_independent_academic_documents():
    sources = list((ROOT / "manuscript" / "issue34").glob("*.tex")) + [
        ROOT / "main_manuscript.tex",
        ROOT / "supplementary_information.tex",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in sources).lower()
    forbidden = (
        "returns to its intended foundation",
        "return to its intended foundation",
        "restored exclusion definition",
        "restored definition",
        "the paper does not recast",
        "previous version",
        "earlier version",
        "low-penalty mean--variance diagnostic",
        "issue #40",
        "supervisor draft",
    )
    assert not any(phrase in text for phrase in forbidden)
    assert "selected gaussian mean--variance policy" in text
    assert "structurally inadmissible" in text
    assert "substantive null" in text
