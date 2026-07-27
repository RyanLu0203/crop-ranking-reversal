"""Executable witnesses for the reconstructed Issue #34 theory."""

from __future__ import annotations

import numpy as np

from crop_optimization.cvar_optimizer import solve_cvar_allocation
from crop_optimization.evaluation import empirical_var_cvar_losses


def test_two_crop_exact_frontier_matches_half_share_risk_test():
    scenarios = np.array([
        [30.0, 12.0],
        [-40.0, 12.0],
        [30.0, 12.0],
        [-40.0, 12.0],
    ])
    alpha = 0.5
    half_losses = -(scenarios @ np.array([0.5, 0.5]))
    _, risk_at_half = empirical_var_cvar_losses(half_losses, alpha)
    result = solve_cvar_allocation(
        scenarios, [1.0, 1.0], 1.0, 1.0, alpha, risk_at_half - 0.5,
        [0.0, 0.0], [1.0, 1.0], {}, ["higher_score", "lower_score"],
    )
    assert result.status == "optimal"
    assert result.allocation[0] < 0.5
    assert result.allocation[0] < result.allocation[1]


def test_signal_ignorability_gives_nonnegative_information_value():
    state_payoffs = np.array([[10.0, 0.0], [0.0, 10.0]])
    prior_action = np.array([0.5, 0.5])
    prior_value = float(np.mean(state_payoffs @ prior_action))
    informed_value = 0.5 * state_payoffs[0, 0] + 0.5 * state_payoffs[1, 1]
    assert informed_value >= prior_value
    assert informed_value > prior_value


def test_shock_buffering_can_substitute_for_information():
    state_payoffs = np.array([[10.0, 0.0], [0.0, 10.0]])
    common = state_payoffs.mean(axis=0)
    values = []
    for flexibility in np.linspace(0.0, 1.0, 6):
        buffered = (1.0 - flexibility) * state_payoffs + flexibility * common
        informed = 0.5 * buffered[0].max() + 0.5 * buffered[1].max()
        uninformed = common.max()
        values.append(informed - uninformed)
    assert np.all(np.diff(values) <= 1e-12)
    assert values[0] > 0
    assert np.isclose(values[-1], 0.0)
