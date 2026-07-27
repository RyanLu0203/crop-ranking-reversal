"""Regression checks for the GOAL-14 theory-strengthening contract."""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "theory/stage_ii"


def _rows(name: str):
    with (BASE / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_stage_ii_results_are_classified_and_assumption_linked():
    assumptions = {row["assumption_id"] for row in _rows("assumption_registry.csv")}
    results = _rows("proposition_audit.csv")
    assert assumptions == {f"S2-A{i:02d}" for i in range(1, 23)}
    assert len(results) >= 17
    assert all(set(row["assumption_ids"].split(";")).issubset(assumptions) for row in results)
    assert {"S2-P02", "S2-T01", "S2-P07", "S2-T02", "S2-T03"}.issubset(
        {row["result_id"] for row in results}
    )


def test_every_historical_gap_has_a_stage_ii_disposition():
    rows = _rows("proof_gap_reconciliation.csv")
    assert {row["gap_id"] for row in rows} == {f"G{i:02d}" for i in range(1, 21)}
    assert all(row["stage_ii_disposition"] for row in rows)
    assert any(row["stage_ii_disposition"] == "OPEN_STAGE_II" for row in rows)


def test_theory_maps_preserve_falsification_and_empirical_boundaries():
    simulation = _rows("theory_to_simulation_mapping.csv")
    empirical = _rows("theory_to_empirical_mapping.csv")
    assert len(simulation) == len(empirical) == 15
    assert all(row["falsification_pattern"] and row["convergence_requirement"] for row in simulation)
    assert all(row["admissible_claim"] and row["inadmissible_claim"] for row in empirical)
    assert all(row["timing"] and row["aggregation_risk"] for row in empirical)


def test_goal_14_validator_passes_as_subprocess():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_stage_ii_theory.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "failures=0" in result.stdout
