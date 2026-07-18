import numpy as np

from crop_optimization.benchmark_policies import run_policy_comparison


def _comparison(deterministic_two_crop_scenarios, two_crop_config):
    return run_policy_comparison(deterministic_two_crop_scenarios, two_crop_config)


def test_infeasible_eo_regret_is_na(deterministic_two_crop_scenarios, two_crop_config):
    df = _comparison(deterministic_two_crop_scenarios, two_crop_config)
    eo = df.loc[df["policy"] == "EO"].iloc[0]

    assert bool(eo["cvar_violation"]) is True
    assert np.isnan(eo["regret_vs_best_feasible"])


def test_feasible_policy_regret_is_defined(deterministic_two_crop_scenarios, two_crop_config):
    df = _comparison(deterministic_two_crop_scenarios, two_crop_config)
    feasible = df.loc[df["cvar_violation"] == False]  # noqa: E712

    assert not feasible.empty
    assert feasible["regret_vs_best_feasible"].notna().all()


def test_best_feasible_policy_regret_is_zero(deterministic_two_crop_scenarios, two_crop_config):
    df = _comparison(deterministic_two_crop_scenarios, two_crop_config)
    feasible = df.loc[df["cvar_violation"] == False]  # noqa: E712
    best = feasible.sort_values("expected_profit", ascending=False).iloc[0]

    assert np.isclose(best["regret_vs_best_feasible"], 0.0)


def test_infeasible_policy_not_used_as_feasible_comparator(deterministic_two_crop_scenarios, two_crop_config):
    df = _comparison(deterministic_two_crop_scenarios, two_crop_config)
    feasible = df.loc[df["regret_vs_best_feasible"].notna()]
    eo_profit = df.loc[df["policy"] == "EO", "expected_profit"].iloc[0]

    assert feasible["expected_profit"].max() < eo_profit
    assert np.isclose(feasible["regret_vs_best_feasible"].min(), 0.0)
