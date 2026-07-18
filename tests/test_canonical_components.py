from pathlib import Path

import numpy as np

from crop_optimization.cvar_optimizer import solve_cvar_allocation
from crop_optimization.evaluation import empirical_var_cvar_losses
from crop_optimization.numerical_tolerances import pairwise_reversal
from crop_simulation.scenario_generation import generate_profit_scenarios

ROOT = Path(__file__).resolve().parents[1]


def test_standard_repository_directories_exist():
    required = {
        "baselines", "manuscript", "theory", "literature", "data", "simulation",
        "optimization", "empirical", "visualization", "figures", "tables",
        "supplementary", "evidence_registry", "audits", "provenance",
    }
    assert all((ROOT / directory).is_dir() for directory in required)


def test_fixed_seed_scenarios_are_exactly_repeatable():
    kwargs = dict(
        means=[30.0, 10.0], stds=[70.0, 0.0], n_scenarios=40,
        copula_type="Gaussian", copula_param=np.eye(2), random_seed=20260703,
        marginal_model={"type": "normal"},
    )
    first, _ = generate_profit_scenarios(**kwargs)
    second, _ = generate_profit_scenarios(**kwargs)
    assert np.array_equal(first, second)


def test_optimization_cvar_and_ranking_classification():
    scenarios = np.array([[100.0, 10.0], [-40.0, 10.0], [100.0, 10.0], [-40.0, 10.0]])
    result = solve_cvar_allocation(
        scenarios, [1.0, 1.0], 1.0, 10.0, 0.5, 0.0,
        [0.0, 0.0], [1.0, 1.0], {"Corn": 1.0}, ["Corn", "Soybean"],
    )
    assert result.status == "optimal"
    _, cvar_loss = empirical_var_cvar_losses(-(scenarios @ result.allocation), 0.5)
    assert np.isfinite(cvar_loss)
    assert pairwise_reversal(0.2, 0.8, 2.0, 1.0, acreage_tolerance=1e-9)
