"""Acceptance tests for the focused Issue #36 scientific repair."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reconstruction" / "issue34" / "outputs"
SCRIPT = ROOT / "scripts" / "run_issue34_reconstruction.py"
SPEC = importlib.util.spec_from_file_location("issue36_repair", SCRIPT)
assert SPEC and SPEC.loader
REPAIR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPAIR)
DESIGN = REPAIR.load_design()


def test_restored_strong_reversal_requires_exclusion():
    scores = np.array([0.7, 0.6, 0.9])
    positive_top = REPAIR.reversal_classification(
        np.array([0.33, 0.42, 0.25]), scores, DESIGN
    )
    excluded_top = REPAIR.reversal_classification(
        np.array([0.40, 0.60, 0.0]), scores, DESIGN
    )

    assert positive_top["selected_complete_rank_reversal"]
    assert not positive_top["selected_strong_reversal"]
    assert excluded_top["selected_strong_reversal"]


def test_zero_tolerance_sensitivity_is_executable():
    scores = np.array([0.9, 0.8, 0.7])
    allocation = np.array([5e-5, 0.6, 0.39995])
    primary = REPAIR.reversal_classification(
        allocation, scores, DESIGN, acreage_tolerance=1e-4,
        near_zero_tolerance=1e-4,
    )
    machine = REPAIR.reversal_classification(
        allocation, scores, DESIGN, acreage_tolerance=1e-8,
        near_zero_tolerance=1e-8,
    )

    assert primary["selected_strong_reversal"]
    assert not machine["selected_strong_reversal"]


def test_registered_risk_path_has_true_crossing_and_order_conditions():
    frame = pd.read_csv(OUTPUT / "risk_induced_reversal.csv").sort_values(
        "risk_tolerance"
    )
    tight, loose = frame.iloc[0], frame.iloc[-1]

    assert tight["score_high"] > tight["score_low"]
    assert tight["mean_margin_high"] > tight["mean_margin_low"]
    assert abs(tight["mean_preservation_error"]) < 1e-9
    assert tight["allocation_high"] < tight["allocation_low"]
    assert loose["allocation_high"] > loose["allocation_low"]
    assert frame["registered_loose_to_tight_crossing"].all()


def test_diversification_frontier_and_non_outcome_selection_rule():
    frame = pd.read_csv(OUTPUT / "diversification_failure.csv")
    policies = frame[frame["row_type"] == "registered_policy"]
    frontier = frame[frame["row_type"] == "mean_variance_frontier"].sort_values(
        "gamma"
    )
    x0 = policies.loc[
        policies["policy"] == "x0_expected_profit_under_matched_gaussian"
    ].iloc[0]
    xmv = policies.loc[
        policies["policy"] == "xMV_variance_target_selected"
    ].iloc[0]

    assert bool(x0["declared_benchmark"])
    assert len(frontier) == 301
    assert np.isclose(frontier["gamma"].iloc[0], 0.0)
    assert np.isclose(frontier["gamma"].iloc[-1], 0.03)
    assert np.allclose(np.diff(frontier["gamma"]), 0.0001)
    assert frontier["policy_solver_generated"].all()
    assert frontier["solver_status"].eq("optimal").all()
    assert frontier["feasibility_max_violation"].max() <= 1e-7
    assert frontier["full_investment_residual"].abs().max() <= 1e-7
    assert xmv["gaussian_profit_variance"] < x0["gaussian_profit_variance"] - 1e-6
    assert np.isclose(
        xmv["benchmark_gaussian_variance"], x0["gaussian_profit_variance"]
    )
    assert xmv["gaussian_variance_reduction_fraction"] >= 0.15
    previous = frontier.loc[frontier["gamma"] < xmv["gamma"]].iloc[-1]
    assert previous["gaussian_variance_reduction_fraction"] < 0.15
    assert xmv["selection_rule"] == (
        "smallest_gamma_achieving_fixed_gaussian_variance_reduction"
    )


def test_evaluation_law_cvar_and_strong_failure_inequalities():
    frame = pd.read_csv(OUTPUT / "diversification_failure.csv")
    xmv = frame.loc[
        frame["policy"] == "xMV_variance_target_selected"
    ].iloc[0]
    xt = frame.loc[
        frame["policy"] == "xT_CVaR_under_student_t_evaluation"
    ].iloc[0]

    assert xmv["xMV_vs_xT_allocation_L1"] > 0.01
    assert xmv["evaluation_loss_CVaR"] > xt["evaluation_loss_CVaR"] + 1e-6
    assert xmv["evaluation_loss_CVaR"] > xmv["risk_ceiling"] + 1e-6
    assert bool(xmv["strong_diversification_failure"])
    assert bool(xmv["tail_and_ceiling_conditions_numerically_dependent"])
    assert np.isclose(
        xmv["xMV_evaluation_CVaR_minus_xT"],
        xmv["evaluation_loss_CVaR"] - xmv["risk_ceiling"],
        atol=1e-6,
    )


def test_diversification_sensitivity_varies_all_required_factors():
    frame = pd.read_csv(OUTPUT / "diversification_sensitivity.csv")
    assert {
        "baseline",
        "scenario_count",
        "seed",
        "kendall_tau",
        "student_t_copula_df",
        "cvar_alpha",
        "risk_ceiling_path",
        "evaluation_marginal",
        "selection_target",
    } <= set(frame["varied_factor"])
    assert frame["selected_solver_status"].eq("optimal").all()
    assert frame["selected_feasibility_max_violation"].max() <= 1e-7
    assert frame["selected_gamma_is_interior"].all()
    assert frame["weak_failure_gamma_intervals"].ne("none").all()


def test_risk_probability_magnitude_map_contains_focal_crossing():
    frame = pd.read_csv(OUTPUT / "risk_shock_sensitivity.csv")
    assert len(frame) == 49
    assert set(frame["classification"]) <= {
        "crossing", "no_crossing", "infeasible"
    }
    assert frame["mean_preservation_error"].abs().max() <= 1e-9
    focal = frame.loc[frame["focal_case"]]
    assert len(focal) == 1
    assert focal.iloc[0]["classification"] == "crossing"
    assert np.isfinite(focal.iloc[0]["first_crossing_risk_tolerance"])


def test_information_cross_difference_matches_four_solved_values():
    frame = pd.read_csv(OUTPUT / "information_flexibility.csv")
    checked = frame.dropna(subset=["discrete_cross_difference"])
    assert len(checked) > 0
    lookup = frame.set_index(
        ["flexibility_path", "signal_accuracy", "flexibility_level"]
    )["optimized_value"]
    for _, row in checked.iterrows():
        path = row["flexibility_path"]
        expected = (
            lookup.loc[(path, row["q2"], row["phi2"])]
            - lookup.loc[(path, row["q1"], row["phi2"])]
            - lookup.loc[(path, row["q2"], row["phi1"])]
            + lookup.loc[(path, row["q1"], row["phi1"])]
        )
        assert np.isclose(row["discrete_cross_difference"], expected, atol=1e-10)
    assert set(frame["cross_difference_classification"]) <= {
        "positive_cross_difference",
        "negative_cross_difference",
        "zero_or_boundary",
        "zero_information",
    }


def test_exact_clopper_pearson_interval_is_named_correctly():
    summary = pd.read_csv(OUTPUT / "uncertainty_summary.csv").set_index("metric")
    row = summary.loc["selected_pairwise_reversal_frequency"]
    expected = stats.binomtest(
        int(row["event_count"]), int(row["bootstrap_replications"])
    ).proportion_ci(confidence_level=0.95, method="exact")

    assert row["interval_method"] == "exact_Clopper_Pearson_binomial"
    assert np.isnan(row["percentile_95_low"])
    assert np.isclose(row["exact_binomial_95_low"], expected.low)
    assert np.isclose(row["exact_binomial_95_high"], expected.high)


def test_manuscript_terminology_and_official_references_are_consistent():
    manuscript = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "manuscript" / "issue34").glob("*.tex"))
    )
    bibliography = (ROOT / "references.bib").read_text(encoding="utf-8")

    assert "therefore strongly reverses" not in manuscript
    assert "red strong reversal" not in manuscript
    assert "selected complete rank reversal" in manuscript
    assert "exact Clopper--Pearson" in manuscript
    forbidden = {
        "supervisor", "repository", "registered", "preregistered", "audit",
        "repaired", "reconstruction", "true-law", "issue #",
    }
    lower = manuscript.lower()
    assert not any(term in lower for term in forbidden)
    for key in [
        "usdanass2019crop",
        "usdanass2022crop",
        "usdanass2025crop",
        "usdaers2026costs",
        "bls2026cpi",
    ]:
        assert key in bibliography
