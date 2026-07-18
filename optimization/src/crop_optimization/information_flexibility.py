"""Information-flexibility complementarity experiment."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd

from .cvar_optimizer import solve_cvar_allocation
from .evaluation import portfolio_profit
from .robustness import array_by_crop
from crop_simulation.scenario_generation import generate_profit_scenarios


def flexibility_config(config: Dict[str, object], phi: float) -> Dict[str, object]:
    """Relax inequality constraints as operational flexibility increases."""

    cfg = deepcopy(config)
    phi = float(phi)
    if not 0.0 <= phi <= 1.0:
        raise ValueError("phi must be in [0, 1].")
    total_acres = float(cfg["total_acres"])
    cfg["budget"] = float(cfg["budget"]) * (1.0 + 0.30 * phi)
    cfg["upper_bounds"] = {
        crop: min(total_acres, float(value) * (1.0 + 0.30 * phi))
        for crop, value in cfg["upper_bounds"].items()
    }
    if "Corn" in cfg.get("rotation_caps", {}):
        cfg["rotation_caps"]["Corn"] = min(
            total_acres,
            float(config["rotation_caps"]["Corn"]) * (1.0 + 0.30 * phi),
        )
    return cfg


def _scaled_corn_scenarios(base_scenarios: np.ndarray, crop_names: List[str], corn_factor: float) -> np.ndarray:
    scenarios = np.array(base_scenarios, copy=True)
    scenarios[:, crop_names.index("Corn")] *= float(corn_factor)
    return scenarios


def _solve_allocation_for_scenarios(config: Dict[str, object], scenarios: np.ndarray) -> np.ndarray:
    crop_names = list(config["crop_names"])
    result = solve_cvar_allocation(
        scenarios,
        array_by_crop(config["costs"], crop_names),
        float(config["total_acres"]),
        float(config["budget"]),
        float(config["alpha"]),
        float(config["cvar_limit"]),
        array_by_crop(config["lower_bounds"], crop_names),
        array_by_crop(config["upper_bounds"], crop_names),
        dict(config.get("rotation_caps") or {}),
        crop_names,
    )
    if result.allocation is None:
        return array_by_crop(config["lower_bounds"], crop_names)
    return result.allocation


def information_flexibility_experiment(config: Dict[str, object]) -> pd.DataFrame:
    crop_names = list(config["crop_names"])
    means = array_by_crop(config["means"], crop_names)
    stds = array_by_crop(config["stds"], crop_names)
    base_scenarios, _ = generate_profit_scenarios(
        means,
        stds,
        int(config["n_scenarios"]),
        "Clayton",
        float(config.get("baseline_clayton_theta", 2.0)),
        int(config["random_seed"]) + 404,
        crop_names=crop_names,
        marginal_model=config.get("marginal_model"),
    )
    high_scenarios = _scaled_corn_scenarios(base_scenarios, crop_names, 1.15)
    low_scenarios = _scaled_corn_scenarios(base_scenarios, crop_names, 0.85)
    state_scenarios = {"high": high_scenarios, "low": low_scenarios}
    signal_factor = {"high": 1.15, "low": 0.85}

    rows = []
    for phi in np.linspace(0.0, 1.0, 6):
        cfg = flexibility_config(config, float(phi))
        prior_allocation = _solve_allocation_for_scenarios(cfg, base_scenarios)
        prior_expected = 0.5 * np.mean(portfolio_profit(high_scenarios, prior_allocation))
        prior_expected += 0.5 * np.mean(portfolio_profit(low_scenarios, prior_allocation))

        rows.append(
            {
                "phi": float(phi),
                "signal_regime": "No information",
                "information_accuracy": 0.50,
                "prior_expected_profit": prior_expected,
                "signal_expected_profit": prior_expected,
                "value_of_information": 0.0,
            }
        )

        for regime, accuracy in [("75% accurate signal", 0.75), ("Perfect signal", 1.00)]:
            expected_signal_profit = 0.0
            for actual_state, actual_prob in [("high", 0.5), ("low", 0.5)]:
                for signal_state in ["high", "low"]:
                    signal_prob = accuracy if signal_state == actual_state else 1.0 - accuracy
                    signal_scenarios = _scaled_corn_scenarios(base_scenarios, crop_names, signal_factor[signal_state])
                    signal_allocation = _solve_allocation_for_scenarios(cfg, signal_scenarios)
                    expected_signal_profit += (
                        actual_prob
                        * signal_prob
                        * np.mean(portfolio_profit(state_scenarios[actual_state], signal_allocation))
                    )
            rows.append(
                {
                    "phi": float(phi),
                    "signal_regime": regime,
                    "information_accuracy": accuracy,
                    "prior_expected_profit": prior_expected,
                    "signal_expected_profit": expected_signal_profit,
                    "value_of_information": expected_signal_profit - prior_expected,
                }
            )
    return pd.DataFrame(rows)
