"""Frozen-design and calibrated scenario-engine regression tests."""

from __future__ import annotations

import json
import csv
from pathlib import Path

import numpy as np

from crop_simulation.copula_models import validate_correlation_matrix
from crop_simulation.experiment_design import expand_design, load_experiment_design
from crop_simulation.panel_calibration import panel_calibration
from crop_simulation.scenario_generation import generate_profit_scenarios

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_design_expands_to_exact_preregistered_cells():
    design = load_experiment_design()
    first = expand_design(design)
    second = expand_design(design)
    assert len(first) == 90
    assert first["cell_id"].is_unique
    assert first.equals(second)
    assert (first["cell_type"] == "lhs").sum() == 72
    assert (first["cell_type"] == "anchor").sum() == 18


def test_all_lhs_factors_remain_inside_frozen_ranges():
    design = load_experiment_design()
    lhs = expand_design(design).query("cell_type == 'lhs'")
    for name, factor in design["factors"].items():
        if factor["type"] == "continuous_lhs":
            low, high = factor["range"]
            assert lhs[name].between(low, high, inclusive="both").all()
    assert set(lhs["copula_family"]) == {"gaussian", "student_t_df4", "clayton"}
    assert set(lhs["marginal_family"]) == {"gaussian", "student_t_df5", "empirical_resample"}


def test_panel_calibration_is_complete_and_traceable():
    calibration = panel_calibration()
    assert calibration["n_years"] == 27
    assert calibration["years"] == [1998, 2024]
    assert calibration["crop_names"] == ["Corn", "Soybean", "Winter Wheat"]
    assert calibration["source_path"] == "data/processed/canonical_crop_year_panel.csv"
    assert all(value > 0 for value in calibration["stds"].values())


def test_empirical_marginal_and_all_copulas_generate_finite_scenarios():
    samples = np.array([[1.0, 2.0], [2.0, 3.0], [4.0, 5.0]])
    families = [
        ("Gaussian", np.eye(2)),
        ("Student-t", {"df": 4, "corr": np.eye(2)}),
        ("Clayton", 1.5),
    ]
    for family, parameter in families:
        scenarios, metadata = generate_profit_scenarios(
            [2.0, 3.0], [1.0, 1.0], 30, family, parameter, 123,
            marginal_model={"type": "empirical_resample", "samples": samples.tolist()},
        )
        assert scenarios.shape == (30, 2)
        assert np.isfinite(scenarios).all()
        assert "WITHIN_NAMED_FAMILY_ONLY" in metadata["ordering_scope"]


def test_invalid_correlation_matrix_is_rejected_without_repair():
    invalid = np.array([[1.0, 1.2], [1.2, 1.0]])
    with np.testing.assert_raises_regex(ValueError, "positive semidefinite"):
        validate_correlation_matrix(invalid, 2)


def test_dry_run_summary_matches_frozen_design_and_is_not_admissible():
    design = load_experiment_design()
    summary = json.loads((ROOT / "simulation/dry_run/summary.json").read_text())
    assert summary["design_sha256"] == design["design_sha256"]
    assert summary["status"] == "DRY_RUN_ONLY_NOT_A_FORMAL_EXPERIMENT"
    assert summary["cells"] == 3
    assert summary["all_exact_repeat"] is True
    assert summary["all_solvers_optimal"] is True
    with (ROOT / "simulation/dry_run/design_cells.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["copula_family"] for row in rows} == {"gaussian", "student_t_df4", "clayton"}
    assert {row["marginal_family"] for row in rows} == {"gaussian", "student_t_df5", "empirical_resample"}


def test_large_fixed_seed_normal_sample_meets_preregistered_moment_smoke_tolerance():
    scenarios, _ = generate_profit_scenarios(
        [100.0, 50.0], [20.0, 10.0], 25000, "Gaussian", np.eye(2), 2026071950,
        marginal_model={"type": "normal"},
    )
    assert np.all(np.abs(scenarios.mean(axis=0) - [100.0, 50.0]) < [0.6, 0.3])
    assert np.all(np.abs(scenarios.std(axis=0, ddof=1) - [20.0, 10.0]) < [0.6, 0.3])
