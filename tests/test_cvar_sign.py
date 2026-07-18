import numpy as np

from crop_optimization.cvar_optimizer import solve_cvar_allocation
from crop_optimization.evaluation import empirical_var_cvar_losses


def test_cvar_is_computed_on_losses_not_profits():
    profits = np.array([10.0, -20.0])
    losses = -profits
    var_loss, cvar_loss = empirical_var_cvar_losses(losses, alpha=0.5)
    assert var_loss == 20.0
    assert cvar_loss == 20.0


def test_cvar_constraint_can_make_required_allocation_infeasible():
    scenarios = np.array([[10.0], [-20.0]])
    feasible = solve_cvar_allocation(
        scenarios,
        costs=[1.0],
        total_acres=1.0,
        budget=10.0,
        alpha=0.5,
        cvar_limit=25.0,
        lower_bounds=[1.0],
        upper_bounds=[1.0],
        crop_names=["Test Crop"],
    )
    infeasible = solve_cvar_allocation(
        scenarios,
        costs=[1.0],
        total_acres=1.0,
        budget=10.0,
        alpha=0.5,
        cvar_limit=0.0,
        lower_bounds=[1.0],
        upper_bounds=[1.0],
        crop_names=["Test Crop"],
    )
    assert feasible.status == "optimal"
    assert infeasible.status == "infeasible_or_failed"
