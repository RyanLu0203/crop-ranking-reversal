"""Deterministic witnesses for the GOAL-14 Stage II theory extension."""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pytest

from crop_optimization.cvar_optimizer import (
    solve_cvar_allocation,
    solve_expected_profit_allocation,
)
from crop_optimization.evaluation import empirical_var_cvar_losses
from crop_optimization.information_flexibility import finite_state_information_value
from stage_ii_mechanism_checks import (
    interaction_cross_difference,
    pairwise_pressure_decomposition,
    shapley_vector_attribution,
)


def _subsets(blocks):
    return [
        frozenset(subset)
        for size in range(len(blocks) + 1)
        for subset in combinations(blocks, size)
    ]


def test_restricted_top_rank_preservation_anchor():
    result = solve_expected_profit_allocation(
        means=[3.0, 2.0, 1.0],
        costs=[1.0, 1.0, 1.0],
        total_acres=1.0,
        budget=10.0,
        lower_bounds=[0.0, 0.0, 0.0],
        upper_bounds=[1.0, 1.0, 1.0],
        rotation_caps={},
        crop_names=["Top", "Middle", "Low"],
    )
    assert result.status == "optimal"
    assert np.allclose(result.allocation, [1.0, 0.0, 0.0])


def test_pairwise_pressure_terms_close_exactly_without_land_term():
    ledger = pairwise_pressure_decomposition(
        mean_profit=[8.0, 5.0],
        tail_subgradient=[3.0, 1.0],
        risk_dual=0.5,
        costs=[4.0, 2.0],
        budget_dual=0.25,
        shared_matrix=np.eye(2),
        shared_duals=[1.0, 0.5],
        lower_bound_duals=[0.0, 0.0],
        upper_bound_duals=[1.0, 0.0],
        i=0,
        j=1,
    )
    assert ledger == {
        "margin_pressure": 3.0,
        "tail_risk_pressure": 1.0,
        "budget_pressure": 0.5,
        "shared_pressure": 0.5,
        "boundary_pressure": 1.0,
        "stationarity_residual": 0.0,
    }


def test_shapley_vector_attribution_is_efficient_and_order_invariant():
    blocks = ("margin", "operations", "risk", "dependence")
    main = {
        "margin": np.array([1.0, -1.0]),
        "operations": np.array([-0.5, 0.5]),
        "risk": np.array([-0.25, 0.25]),
        "dependence": np.array([-0.1, 0.1]),
    }
    interaction = np.array([0.2, -0.2])
    values = {}
    for subset in _subsets(blocks):
        value = sum((main[block] for block in subset), np.zeros(2))
        if {"risk", "dependence"}.issubset(subset):
            value = value + interaction
        values[subset] = value
    forward = shapley_vector_attribution(values, blocks)
    reverse = shapley_vector_attribution(values, tuple(reversed(blocks)))
    total = sum(forward.values(), np.zeros(2))
    assert np.allclose(total, values[frozenset(blocks)] - values[frozenset()])
    assert all(np.allclose(forward[block], reverse[block]) for block in blocks)


def test_shapley_fails_closed_when_a_subset_is_missing():
    blocks = ("a", "b")
    values = {subset: np.array([float(len(subset))]) for subset in _subsets(blocks)}
    values.pop(frozenset({"a"}))
    with pytest.raises(ValueError, match="subset lattice mismatch"):
        shapley_vector_attribution(values, blocks)


def test_tighter_risk_limit_weakly_lowers_value_without_coordinate_theorem():
    scenarios = np.array(
        [[100.0, 10.0], [-40.0, 10.0], [100.0, 10.0], [-40.0, 10.0]]
    )
    common = dict(
        profit_scenarios=scenarios,
        costs=[1.0, 1.0],
        total_acres=1.0,
        budget=10.0,
        alpha=0.5,
        lower_bounds=[0.0, 0.0],
        upper_bounds=[1.0, 1.0],
        rotation_caps={},
        crop_names=["A", "B"],
    )
    tight = solve_cvar_allocation(cvar_limit=0.0, **common)
    loose = solve_cvar_allocation(cvar_limit=100.0, **common)
    assert tight.status == loose.status == "optimal"
    assert tight.expected_profit <= loose.expected_profit + 1e-10
    assert tight.cvar_loss <= 1e-8


def test_lower_concentration_can_have_higher_variance_and_cvar():
    scenarios = np.array([[0.0, -100.0], [0.0, 100.0]])
    concentrated = scenarios @ np.array([1.0, 0.0])
    diversified = scenarios @ np.array([0.5, 0.5])
    _, cvar_concentrated = empirical_var_cvar_losses(-concentrated, 0.5)
    _, cvar_diversified = empirical_var_cvar_losses(-diversified, 0.5)
    assert 0.5 < 1.0  # HHI([0.5, 0.5]) < HHI([1, 0])
    assert np.var(diversified) > np.var(concentrated)
    assert cvar_diversified > cvar_concentrated


def test_more_informative_signal_weakly_improves_value():
    payoff = np.array([[10.0, 0.0], [0.0, 10.0]])
    prior = [0.5, 0.5]
    uninformative = finite_state_information_value(
        payoff, prior, np.array([[0.5, 0.5], [0.5, 0.5]])
    )
    perfect = finite_state_information_value(payoff, prior, np.eye(2))
    assert uninformative["value_of_information"] == 0.0
    assert perfect["value_of_information"] == 5.0
    assert perfect["signal_value"] >= uninformative["signal_value"]


def test_nested_flexibility_can_substitute_for_information():
    # Low flexibility: specialized actions; high flexibility adds a robust action.
    low_info_low_flex = 5.0
    high_info_low_flex = 10.0
    low_info_high_flex = 9.0
    high_info_high_flex = 10.0
    cross = interaction_cross_difference(
        low_info_low_flex,
        high_info_low_flex,
        low_info_high_flex,
        high_info_high_flex,
    )
    assert cross == -4.0


def test_fixed_land_simplex_is_not_a_componentwise_lattice():
    x = np.array([1.0, 0.0])
    y = np.array([0.0, 1.0])
    join = np.maximum(x, y)
    assert x.sum() <= 1.0 and y.sum() <= 1.0
    assert join.sum() > 1.0
