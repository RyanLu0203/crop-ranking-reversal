"""Deterministic witnesses for the teacher-model theorem audit."""

from __future__ import annotations

import numpy as np
from scipy.optimize import linprog
from scipy.stats import norm

from crop_optimization.cvar_optimizer import solve_cvar_allocation
from crop_optimization.evaluation import empirical_var_cvar_losses


def _solve(scenarios: np.ndarray, limit: float, alpha: float = 0.5):
    return solve_cvar_allocation(
        profit_scenarios=np.asarray(scenarios, dtype=float),
        costs=np.ones(2),
        total_acres=1.0,
        budget=10.0,
        alpha=alpha,
        cvar_limit=limit,
        lower_bounds=np.zeros(2),
        upper_bounds=np.ones(2),
        crop_names=["A", "B"],
    )


def test_teacher_upper_profit_tail_is_not_loss_cvar():
    profits = np.array([-100.0, 10.0, 20.0, 30.0])
    _, correct = empirical_var_cvar_losses(-profits, alpha=0.75)
    teacher_expression = -np.mean(np.sort(profits)[-1:])
    assert correct == 100.0
    assert teacher_expression == -30.0


def test_multiple_optima_allow_both_reversal_labels():
    # max x1+x2 on the unit simplex; constrain objective to its optimum and
    # separately minimize/maximize x1 to expose the entire optimal face.
    a = np.array([[1.0, 1.0], [-1.0, -1.0]])
    b = np.array([1.0, -1.0])
    lo = linprog([1.0, 0.0], A_ub=a, b_ub=b, bounds=[(0, None)] * 2, method="highs")
    hi = linprog([-1.0, 0.0], A_ub=a, b_ub=b, bounds=[(0, None)] * 2, method="highs")
    assert lo.success and hi.success
    assert np.isclose(lo.x[0], 0.0) and np.isclose(hi.x[0], 1.0)


def test_cvar_can_be_slack_or_binding():
    slack = _solve(np.array([[10.0, 6.0], [10.0, 6.0]]), limit=-5.0)
    binding = _solve(np.array([[100.0, 5.0], [-20.0, 5.0]]), limit=-5.0)
    assert slack.status == binding.status == "optimal"
    assert slack.cvar_loss < -5.0 and not slack.diagnostics["cvar_binds"]
    assert np.isclose(binding.cvar_loss, -5.0) and binding.diagnostics["cvar_binds"]


def test_cvar_limit_can_make_lower_bounds_infeasible():
    result = solve_cvar_allocation(
        profit_scenarios=np.array([[-10.0, 0.0], [-10.0, 0.0]]),
        costs=[1.0, 1.0], total_acres=1.0, budget=10.0,
        alpha=0.5, cvar_limit=5.0,
        lower_bounds=[1.0, 0.0], upper_bounds=[1.0, 0.0],
        crop_names=["A", "B"],
    )
    assert result.status == "infeasible_or_failed"


def test_same_gaussian_tail_coefficient_different_portfolio_cvar():
    alpha = 0.95
    es_multiplier = norm.pdf(norm.ppf(alpha)) / (1.0 - alpha)
    cvar_rho_zero = np.sqrt(2.0) * es_multiplier
    cvar_rho_high = np.sqrt(2.0 + 2.0 * 0.9) * es_multiplier
    # Both nonsingular Gaussian copulas have lambda_L=0.
    assert cvar_rho_high > cvar_rho_zero


def test_parametric_lp_can_change_ranking_more_than_once():
    rankings = []
    for t in np.linspace(0.0, 1.0, 41):
        risk_a = 2.0 + 1.5 * np.sin(4.0 * np.pi * t)
        result = linprog(
            [-2.0, -1.0],
            A_ub=[[1.0, 1.0], [risk_a, 1.0]],
            b_ub=[1.0, 1.0], bounds=[(0, 1), (0, 1)], method="highs",
        )
        assert result.success
        rankings.append(int(result.x[0] > result.x[1] + 1e-8))
    changes = sum(a != b for a, b in zip(rankings, rankings[1:]))
    assert changes >= 3


def test_low_correlation_does_not_force_inclusion():
    scenarios = np.array([[10, -100], [11, -101], [9, -99], [10, -100]], dtype=float)
    assert np.isclose(np.corrcoef(scenarios.T)[0, 1], -1.0)
    result = _solve(scenarios, limit=1_000.0, alpha=0.75)
    assert result.status == "optimal" and result.allocation[1] < 1e-8


def test_high_comovement_does_not_force_exclusion():
    scenarios = np.array([[1, 10], [2, 11], [3, 12], [4, 13]], dtype=float)
    assert np.isclose(np.corrcoef(scenarios.T)[0, 1], 1.0)
    result = _solve(scenarios, limit=1_000.0, alpha=0.75)
    assert result.status == "optimal" and result.allocation[1] > 1.0 - 1e-8


def test_common_posterior_optimal_action_has_zero_information_value():
    # Rows are posterior states; columns are actions. A is always best.
    posterior_payoffs = np.array([[4.0, 1.0], [2.0, 0.0]])
    probabilities = np.array([0.4, 0.6])
    informed = probabilities @ posterior_payoffs.max(axis=1)
    uninformed = (probabilities @ posterior_payoffs).max()
    assert np.isclose(informed - uninformed, 0.0)
