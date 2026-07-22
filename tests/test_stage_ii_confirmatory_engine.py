"""Contract tests for the GOAL-12 confirmatory engine."""

from __future__ import annotations

import numpy as np
import pandas as pd

from crop_simulation.stage_ii_confirmatory import (
    allocation_evaluation,
    all_subsets,
    finite_state_information_value_subset,
    generate_family_scenarios,
    load_confirmatory_design,
    operational_spec,
    pairwise_pressure_row,
    replication_seed,
    shapley_values,
    solve_minimum_cvar,
    solve_risk,
    stopping_rows,
    symmetric_garbling,
)


def test_confirmatory_design_is_frozen_and_seed_streams_are_disjoint():
    design = load_confirmatory_design()
    assert design["status"] == "FROZEN_BEFORE_RESULTS"
    seeds = {
        replication_seed(design, experiment, index)
        for experiment in design["randomness"]["seed_roots"]
        for index in range(1, 65)
    }
    assert len(seeds) == 7 * 64


def test_empirical_copula_stream_is_exactly_reproducible():
    design = load_confirmatory_design()
    first, metadata_first = generate_family_scenarios(
        design, "empirical_copula", None, 202607224001, 128
    )
    second, metadata_second = generate_family_scenarios(
        design, "empirical_copula", None, 202607224001, 128
    )
    assert np.array_equal(first, second)
    assert metadata_first["scenario_sha256"] == metadata_second["scenario_sha256"]
    assert metadata_first["ordering_scope"].startswith("EMPIRICAL_COPULA")


def test_minimum_cvar_anchor_and_tighter_feasible_policy():
    design = load_confirmatory_design()
    scenarios = np.asarray(
        [[100.0, 10.0, 0.0], [-40.0, 10.0, 0.0]] * 40,
        dtype=float,
    )
    spec = operational_spec(design)
    minimum = solve_minimum_cvar(scenarios, spec, 0.5)
    assert minimum.status == "optimal"
    feasible = solve_risk(scenarios, spec, 0.5, float(minimum.cvar_loss) + 1e-8)
    assert feasible.status == "optimal"
    assert feasible.cvar_loss <= float(minimum.cvar_loss) + 1e-6


def test_tail_contributions_sum_to_portfolio_cvar():
    scenarios = np.asarray(
        [[100.0, 10.0, 0.0], [-40.0, 10.0, 0.0]] * 40,
        dtype=float,
    )
    evaluated = allocation_evaluation(scenarios, [0.6, 0.4, 0.0], 0.5, 1e9)
    contributions = sum(
        float(evaluated[f"tail_contribution_{crop}"])
        for crop in ("Corn", "Soybean", "Winter_Wheat")
    )
    assert np.isclose(contributions, float(evaluated["cvar_loss"]))


def test_binary_signal_garbling_is_constructive():
    garbling = symmetric_garbling(0.9, 0.7)
    high = np.asarray([[0.9, 0.1], [0.1, 0.9]])
    low = np.asarray([[0.7, 0.3], [0.3, 0.7]])
    assert np.allclose(high @ garbling, low)


def test_information_subset_retains_ignore_signal_policy():
    payoff = np.asarray([[10.0, 0.0], [0.0, 10.0], [9.0, 9.0]])
    signal = np.asarray([[0.9, 0.1], [0.1, 0.9]])
    low = finite_state_information_value_subset(payoff, [0.5, 0.5], signal, [0, 1])
    high = finite_state_information_value_subset(payoff, [0.5, 0.5], signal, [0, 1, 2])
    assert low["value_of_information"] > high["value_of_information"] >= 0.0


def test_all_subset_shapley_is_efficient():
    blocks = ["margins", "operations", "risk", "dependence"]
    vectors = {
        subset: np.asarray([float(len(subset)), float(2 * len(subset))])
        for subset in all_subsets(blocks)
    }
    values = shapley_values(vectors, blocks)
    assert len(vectors) == 16
    assert np.allclose(
        sum(values.values(), np.zeros(2)),
        vectors[frozenset(blocks)] - vectors[frozenset()],
    )


def test_stopping_rows_use_frozen_continuous_and_binary_targets():
    design = load_confirmatory_design()
    rows = []
    for seed in range(16):
        rows.extend(
            [
                {
                    "experiment_id": "E1",
                    "contrast_id": "stable",
                    "replication_seed": seed,
                    "metric": "allocation_l1",
                    "value": 0.1,
                    "binary_metric": False,
                },
                {
                    "experiment_id": "E1",
                    "contrast_id": "stable",
                    "replication_seed": seed,
                    "metric": "selected_reversal_change",
                    "value": 1.0,
                    "binary_metric": True,
                },
            ]
        )
    audit, passed = stopping_rows(design, pd.DataFrame(rows), "E1", 16)
    assert len(audit) == 2
    assert passed


def test_missing_binary_contrast_fails_precision_without_crashing():
    design = load_confirmatory_design()
    rows = [
        {
            "experiment_id": "E1",
            "contrast_id": "missing",
            "replication_seed": seed,
            "metric": "selected_reversal_change",
            "value": np.nan if seed == 15 else 1.0,
            "binary_metric": True,
        }
        for seed in range(16)
    ]
    audit, passed = stopping_rows(design, pd.DataFrame(rows), "E1", 16)
    assert not passed
    assert audit[0]["finite_n"] == 15
    assert not audit[0]["precision_pass"]


def test_pairwise_pressure_ledger_closes_with_boundary_terms():
    design = load_confirmatory_design()
    scenarios = np.asarray(
        [[100.0, 10.0, 0.0], [-40.0, 10.0, 0.0]] * 80,
        dtype=float,
    )
    spec = operational_spec(design)
    result = solve_risk(scenarios, spec, 0.5, 0.0)
    ledger = pairwise_pressure_row(result, scenarios, spec, 0.5)
    assert abs(ledger["stationarity_residual"]) <= 1e-7
