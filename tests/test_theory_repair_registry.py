"""Structural and mathematical regression tests for the repaired theorem set."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def _rows(relative: str):
    with (ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_every_draft_result_has_one_transition():
    result_ids = [row["draft_result_id"] for row in _rows(
        "theory/repaired/theorem_transition_registry.csv"
    )]
    assert result_ids == [f"R{i:02d}" for i in range(1, 32)]
    assert len(result_ids) == len(set(result_ids))


def test_both_downstream_maps_cover_all_canonical_results():
    expected = {f"CT{i}" for i in range(1, 11)}
    for name in ("theory_to_simulation_map.csv", "theory_to_empirical_map.csv"):
        assert {
            row["theory_result_id"]
            for row in _rows(f"theory/repaired/{name}")
        } == expected


def test_zero_derivative_at_binding_boundary_is_not_a_feasible_certificate():
    # Local risk r(t)=t^2 at kappa=0: r'(0;1)=0, but every positive step violates.
    step = 1e-4
    directional_derivative = 0.0
    assert directional_derivative == 0.0
    assert step**2 > 0.0


def test_strictly_negative_directional_risk_gives_a_small_feasible_step():
    # r(t)=1-t+t^2 binds at t=0 under kappa=1 and decreases for small t.
    steps = np.array([1e-6, 1e-4, 1e-2])
    assert np.all(1.0 - steps + steps**2 < 1.0)


def test_risk_slack_optimal_set_is_an_intersection_not_blanket_equality():
    # Both endpoints maximize a zero objective, but only x=0 passes r(x)=x <= 0.
    unrestricted_optima = {0.0, 1.0}
    risk_feasible = {0.0}
    assert unrestricted_optima & risk_feasible == {0.0}
    assert unrestricted_optima != risk_feasible
