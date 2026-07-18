import numpy as np

from conftest import ACREAGE_TOL, BUDGET_TOL, CVAR_TOL
from crop_optimization.cvar_optimizer import solve_cvar_allocation
from crop_optimization.evaluation import allocation_metrics


def _solve_two_crop(deterministic_two_crop_scenarios, two_crop_config):
    return solve_cvar_allocation(
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


def test_solution_respects_total_acreage(deterministic_two_crop_scenarios, two_crop_config):
    result = _solve_two_crop(deterministic_two_crop_scenarios, two_crop_config)

    assert result.status == "optimal"
    assert result.allocation.sum() <= two_crop_config["total_acres"] + ACREAGE_TOL


def test_solution_respects_budget(deterministic_two_crop_scenarios, two_crop_config):
    result = _solve_two_crop(deterministic_two_crop_scenarios, two_crop_config)

    assert result.status == "optimal"
    assert np.dot([1.0, 1.0], result.allocation) <= two_crop_config["budget"] + BUDGET_TOL


def test_solution_respects_bounds(deterministic_two_crop_scenarios, two_crop_config):
    result = _solve_two_crop(deterministic_two_crop_scenarios, two_crop_config)

    assert result.status == "optimal"
    assert np.all(result.allocation >= np.array([0.0, 0.0]) - ACREAGE_TOL)
    assert np.all(result.allocation <= np.array([1.0, 1.0]) + ACREAGE_TOL)


def test_solution_respects_rotation_cap(deterministic_two_crop_scenarios, two_crop_config):
    cfg = dict(two_crop_config)
    cfg["rotation_caps"] = {"Corn": 0.15}
    result = solve_cvar_allocation(
        deterministic_two_crop_scenarios,
        costs=[1.0, 1.0],
        total_acres=cfg["total_acres"],
        budget=cfg["budget"],
        alpha=cfg["alpha"],
        cvar_limit=cfg["cvar_limit"],
        lower_bounds=[0.0, 0.0],
        upper_bounds=[1.0, 1.0],
        rotation_caps=cfg["rotation_caps"],
        crop_names=cfg["crop_names"],
    )

    assert result.status == "optimal"
    assert result.allocation[0] <= 0.15 + ACREAGE_TOL


def test_feasible_solution_respects_cvar_limit(deterministic_two_crop_scenarios, two_crop_config):
    result = _solve_two_crop(deterministic_two_crop_scenarios, two_crop_config)
    metrics = allocation_metrics(
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
    assert metrics["cvar_loss"] <= two_crop_config["cvar_limit"] + CVAR_TOL
