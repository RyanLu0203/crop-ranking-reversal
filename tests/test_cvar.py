import numpy as np

from conftest import CVAR_TOL
from crop_optimization.cvar_optimizer import solve_cvar_allocation
from crop_optimization.evaluation import allocation_metrics, empirical_var_cvar_losses


def test_cvar_is_computed_on_losses():
    profits = np.array([10.0, -20.0])
    losses = -profits

    var_loss, cvar_loss = empirical_var_cvar_losses(losses, alpha=0.5)

    assert var_loss == 20.0
    assert cvar_loss == 20.0


def test_higher_profit_reduces_cvar_loss():
    base_profits = np.array([-10.0, 0.0, 20.0, 30.0])
    improved_profits = base_profits + 5.0

    _, base_cvar = empirical_var_cvar_losses(-base_profits, alpha=0.75)
    _, improved_cvar = empirical_var_cvar_losses(-improved_profits, alpha=0.75)

    assert improved_cvar <= base_cvar


def test_negating_profit_scenarios_uses_loss_tail_consistently():
    profits = np.array([[10.0], [-20.0]])
    negated_profits = -profits
    allocation = [1.0]

    original = allocation_metrics(allocation, profits, [1.0], 1.0, 10.0, 0.5, 100.0, ["Crop"])
    negated = allocation_metrics(allocation, negated_profits, [1.0], 1.0, 10.0, 0.5, 100.0, ["Crop"])

    assert original["cvar_loss"] == empirical_var_cvar_losses(np.array([-10.0, 20.0]), 0.5)[1]
    assert negated["cvar_loss"] == empirical_var_cvar_losses(np.array([10.0, -20.0]), 0.5)[1]
    assert original["cvar_loss"] != negated["cvar_loss"]


def test_cvar_evaluator_matches_solver_convention(deterministic_two_crop_scenarios, two_crop_config):
    result = solve_cvar_allocation(
        deterministic_two_crop_scenarios,
        costs=[1.0, 1.0],
        total_acres=two_crop_config["total_acres"],
        budget=two_crop_config["budget"],
        alpha=two_crop_config["alpha"],
        cvar_limit=two_crop_config["cvar_limit"],
        lower_bounds=[0.0, 0.0],
        upper_bounds=[1.0, 1.0],
        rotation_caps=two_crop_config["rotation_caps"],
        crop_names=two_crop_config["crop_names"],
    )

    direct_metrics = allocation_metrics(
        result.allocation,
        deterministic_two_crop_scenarios,
        [1.0, 1.0],
        two_crop_config["total_acres"],
        two_crop_config["budget"],
        two_crop_config["alpha"],
        two_crop_config["cvar_limit"],
        two_crop_config["crop_names"],
    )

    assert result.status == "optimal"
    assert np.isclose(result.cvar_loss, direct_metrics["cvar_loss"], atol=CVAR_TOL)
