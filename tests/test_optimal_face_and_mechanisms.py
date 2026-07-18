"""Solution-set, crossing, pseudo-diversification, and information tests."""

from __future__ import annotations

import numpy as np

from crop_optimization.crossing_sets import crossing_set_audit
from crop_optimization.evaluation import pseudo_diversification_diagnostic
from crop_optimization.information_flexibility import (
    finite_state_information_value,
    nested_action_set_values,
)
from crop_optimization.optimal_face_audit import audit_pairwise_optimal_face


def test_multiple_optima_are_classified_as_possible_not_universal_reversal():
    scenarios = np.array([[10.0, 10.0], [10.0, 10.0]])
    audit = audit_pairwise_optimal_face(
        scenarios, [1.0, 1.0], 1.0, 1.0, 0.5, 0.0,
        [0.0, 0.0], [1.0, 1.0], ["High", "Low"], "High", "Low",
        allocation_tolerance=1e-6,
    )
    assert audit["classification"] == "Possible reversal"
    assert audit["min_difference"] < -0.99
    assert audit["max_difference"] > 0.99
    assert audit["universal_reversal"] is False


def test_contract_and_cap_force_universal_reversal_over_optimal_face():
    scenarios = np.array([[20.0, 10.0], [20.0, 10.0]])
    audit = audit_pairwise_optimal_face(
        scenarios, [1.0, 1.0], 1.0, 10.0, 0.5, 0.0,
        [0.0, 0.0], [1.0, 1.0], ["High", "Low"], "High", "Low",
        rotation_caps={"High": 0.2}, contract_minimums={"Low": 0.8},
        allocation_tolerance=1e-6,
    )
    assert audit["classification"] == "Universal reversal"
    assert audit["max_difference"] < -0.59


def test_multiple_crossing_regions_prohibit_unique_threshold_claim():
    audit = crossing_set_audit([0, 1, 2, 3, 4, 5], [False, True, True, False, True, False])
    assert audit["crossing_count"] == 4
    assert audit["reversal_region_count"] == 2
    assert audit["unique_threshold_admissible"] is False
    assert audit["reversal_regions_on_grid"] == [[1.0, 2.0], [4.0, 4.0]]


def test_pseudo_diversification_is_explicitly_descriptive_only():
    diagnostic = pseudo_diversification_diagnostic(
        [0.45, 0.35, 0.20], [3.0, 2.0, 1.0],
        np.array([[1.0, 0.1, 0.0], [0.1, 1.0, 0.05], [0.0, 0.05, 1.0]]),
        0.0,
    )
    assert diagnostic["pseudo_diversification_flag"] is True
    assert diagnostic["interpretation"] == "DESCRIPTIVE_ONLY_NOT_WELFARE_OR_EXCLUSION"


def test_information_value_is_nonnegative_and_actionability_is_observed():
    payoff = np.array([[5.0, 5.0], [10.0, 0.0], [0.0, 10.0]])
    result = finite_state_information_value(payoff, [0.5, 0.5], np.eye(2))
    assert result["no_information_value"] == 5.0
    assert result["signal_value"] == 10.0
    assert result["value_of_information"] == 5.0
    assert result["policy_actionable"] is True


def test_nested_flexibility_values_cannot_decrease():
    payoff = np.array([[2.0, 2.0], [5.0, 0.0], [0.0, 8.0]])
    values = nested_action_set_values(payoff, [0.5, 0.5], [[0], [0, 1], [0, 1, 2]])
    assert values == sorted(values)
