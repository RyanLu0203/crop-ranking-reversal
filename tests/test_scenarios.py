import numpy as np
import pytest

from crop_optimization.cvar_optimizer import solve_cvar_allocation
from crop_simulation.scenario_generation import generate_profit_scenarios


def test_scenario_matrix_shape():
    scenarios, metadata = generate_profit_scenarios(
        means=[1.0, 2.0, 3.0],
        stds=[0.1, 0.2, 0.3],
        n_scenarios=25,
        copula_type="Gaussian",
        copula_param=np.eye(3),
        random_seed=123,
        marginal_model={"type": "normal"},
    )

    assert scenarios.shape == (25, 3)
    assert metadata["n_scenarios"] == 25


def test_scenarios_are_finite():
    scenarios, _ = generate_profit_scenarios(
        means=[1.0, 2.0],
        stds=[0.1, 0.2],
        n_scenarios=30,
        copula_type="Clayton",
        copula_param=1.5,
        random_seed=456,
        marginal_model={"type": "student_t", "df": 5},
    )

    assert np.isfinite(scenarios).all()


def test_invalid_dimension_rejected():
    with pytest.raises(ValueError, match="same length"):
        generate_profit_scenarios(
            means=[1.0, 2.0],
            stds=[0.1],
            n_scenarios=10,
            copula_type="Gaussian",
            copula_param=np.eye(2),
            random_seed=1,
        )


def test_crop_parameter_alignment_validation():
    with pytest.raises(ValueError, match="must match scenario columns"):
        solve_cvar_allocation(
            profit_scenarios=np.ones((4, 2)),
            costs=[1.0],
            total_acres=1.0,
            budget=10.0,
            alpha=0.5,
            cvar_limit=100.0,
            lower_bounds=[0.0, 0.0],
            upper_bounds=[1.0, 1.0],
            crop_names=["Corn", "Soybean"],
        )


def test_unsupported_copula_type_fails_clearly():
    with pytest.raises(ValueError, match="Unsupported copula_type"):
        generate_profit_scenarios(
            means=[1.0, 2.0],
            stds=[0.1, 0.2],
            n_scenarios=10,
            copula_type="UnsupportedCopula",
            copula_param=None,
            random_seed=1,
        )
