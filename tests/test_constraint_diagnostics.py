from conftest import ACTIVE_TOL
from crop_optimization.cvar_optimizer import solve_cvar_allocation


def test_budget_binding_detection():
    result = solve_cvar_allocation(
        profit_scenarios=[[5.0], [5.0]],
        costs=[10.0],
        total_acres=10.0,
        budget=50.0,
        alpha=0.5,
        cvar_limit=100.0,
        lower_bounds=[0.0],
        upper_bounds=[10.0],
        crop_names=["Corn"],
    )

    assert result.status == "optimal"
    assert abs(result.diagnostics["budget_slack"]) <= ACTIVE_TOL
    assert result.diagnostics["budget_binds"] is True


def test_cvar_binding_detection(deterministic_two_crop_scenarios, two_crop_config):
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

    assert result.status == "optimal"
    assert abs(result.diagnostics["optimizer_cvar_slack"]) <= ACTIVE_TOL
    assert result.diagnostics["cvar_binds"] is True


def test_slack_cvar_not_marked_active():
    result = solve_cvar_allocation(
        profit_scenarios=[[5.0], [5.0]],
        costs=[1.0],
        total_acres=1.0,
        budget=10.0,
        alpha=0.5,
        cvar_limit=100.0,
        lower_bounds=[0.0],
        upper_bounds=[1.0],
        crop_names=["Corn"],
    )

    assert result.status == "optimal"
    assert result.diagnostics["cvar_slack"] > ACTIVE_TOL
    assert result.diagnostics["cvar_binds"] is False


def test_rotation_binding_detection():
    result = solve_cvar_allocation(
        profit_scenarios=[[20.0, 5.0], [20.0, 5.0]],
        costs=[1.0, 1.0],
        total_acres=10.0,
        budget=100.0,
        alpha=0.5,
        cvar_limit=100.0,
        lower_bounds=[0.0, 0.0],
        upper_bounds=[10.0, 10.0],
        rotation_caps={"Corn": 4.0},
        crop_names=["Corn", "Soybean"],
    )

    assert result.status == "optimal"
    assert abs(result.diagnostics["rotation_slack_Corn"]) <= ACTIVE_TOL
    assert result.diagnostics["rotation_binds_Corn"] is True
    assert result.diagnostics["rotation_binds"] is True
