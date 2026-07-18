import sys
import re
from pathlib import Path

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
for source in ["empirical/src", "simulation/src", "optimization/src", "visualization/src"]:
    sys.path.insert(0, str(ROOT / source))

ACREAGE_TOL = 1e-6
BUDGET_TOL = 1e-5
CVAR_TOL = 1e-5
ACTIVE_TOL = 1e-4
SYNC_COLLISION = re.compile(r" \d+$")


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool:
    """Keep Finder/iCloud collision copies outside the canonical test suite."""
    return bool(SYNC_COLLISION.search(collection_path.stem))


@pytest.fixture
def deterministic_two_crop_scenarios():
    return np.array([[100.0, 10.0], [-40.0, 10.0], [100.0, 10.0], [-40.0, 10.0]])


@pytest.fixture
def two_crop_config():
    return {
        "random_seed": 20260703, "n_scenarios": 4, "crop_names": ["Corn", "Soybean"],
        "total_acres": 1.0, "budget": 10.0, "alpha": 0.5, "cvar_limit": 0.0,
        "costs": {"Corn": 1.0, "Soybean": 1.0}, "means": {"Corn": 30.0, "Soybean": 10.0},
        "stds": {"Corn": 70.0, "Soybean": 0.0}, "suitability_scores": {"Corn": 2.0, "Soybean": 1.0},
        "lower_bounds": {"Corn": 0.0, "Soybean": 0.0}, "upper_bounds": {"Corn": 1.0, "Soybean": 1.0},
        "rotation_caps": {"Corn": 1.0}, "mean_variance_gamma": 1e-5,
    }


@pytest.fixture
def baseline_config():
    with (ROOT / "simulation/configs/base_config.yaml").open() as handle:
        cfg = yaml.safe_load(handle)
    cfg["n_scenarios"] = 40
    cfg["theta_grid"] = [0.5, 1.0]
    cfg["robustness"] = {**(cfg.get("robustness") or {}), "n_scenarios": 30}
    return cfg
