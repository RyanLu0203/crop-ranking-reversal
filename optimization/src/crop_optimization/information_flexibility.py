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


def finite_state_information_value(
    payoff_by_action_state: np.ndarray,
    prior_state_probabilities: Iterable[float],
    signal_given_state: np.ndarray,
) -> Dict[str, object]:
    """Exact finite-state VOI with the ignore-signal policy included."""

    payoff = np.asarray(payoff_by_action_state, dtype=float)
    prior = np.asarray(list(prior_state_probabilities), dtype=float)
    signal = np.asarray(signal_given_state, dtype=float)
    if payoff.ndim != 2 or prior.shape != (payoff.shape[1],):
        raise ValueError("payoff columns and prior states must agree")
    if signal.shape[0] != payoff.shape[1] or np.any(signal < 0):
        raise ValueError("signal probabilities must have one row per state")
    if not np.isclose(prior.sum(), 1.0) or not np.allclose(signal.sum(axis=1), 1.0):
        raise ValueError("prior and each conditional signal row must sum to one")
    no_info_by_action = payoff @ prior
    no_info_action = int(np.argmax(no_info_by_action))
    no_info_value = float(no_info_by_action[no_info_action])
    signal_value = 0.0
    signal_actions: list[int] = []
    for signal_index in range(signal.shape[1]):
        joint = prior * signal[:, signal_index]
        signal_probability = float(joint.sum())
        if signal_probability <= 0:
            signal_actions.append(no_info_action)
            continue
        conditional_values = payoff @ joint
        action = int(np.argmax(conditional_values))
        signal_actions.append(action)
        signal_value += float(conditional_values[action])
    # The no-information action for every signal is always feasible, so this
    # independent calculation must dominate no_info_value up to rounding.
    if signal_value < no_info_value - 1e-12:
        raise AssertionError("negative VOI despite admissible ignore-signal policy")
    return {
        "no_information_action": no_info_action,
        "signal_actions": signal_actions,
        "no_information_value": no_info_value,
        "signal_value": signal_value,
        "value_of_information": signal_value - no_info_value,
        "policy_actionable": bool(any(action != no_info_action for action in signal_actions)),
    }


def nested_action_set_values(
    payoff_by_action_state: np.ndarray,
    prior_state_probabilities: Iterable[float],
    nested_action_sets: Iterable[Iterable[int]],
) -> List[float]:
    """Return optimal values for verified nested finite action sets."""

    payoff = np.asarray(payoff_by_action_state, dtype=float)
    prior = np.asarray(list(prior_state_probabilities), dtype=float)
    sets = [set(map(int, actions)) for actions in nested_action_sets]
    if any(not actions for actions in sets):
        raise ValueError("action sets must be non-empty")
    if any(not left.issubset(right) for left, right in zip(sets[:-1], sets[1:])):
        raise ValueError("action sets must be nested")
    expected = payoff @ prior
    values = [float(max(expected[list(actions)])) for actions in sets]
    if any(right < left - 1e-12 for left, right in zip(values[:-1], values[1:])):
        raise AssertionError("value decreased under a nested action-set expansion")
    return values


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
        dict(config.get("contract_minimums") or {}),
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
