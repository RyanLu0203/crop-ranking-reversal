from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "visualization/src"))

from crop_visualization.stage_ii_figures import FIGURE_META, _geometry_data  # noqa: E402


def test_stage_ii_contract_has_six_main_and_five_supplementary_figures():
    assert len(FIGURE_META) == 11
    assert sum(section == "main" for section, _, _ in FIGURE_META.values()) == 6


def test_exact_geometry_distinguishes_possible_from_universal():
    cases = _geometry_data().set_index("case_id")
    assert cases.loc["set_valued", "optimal_xcorn_min"] < 0.5
    assert cases.loc["set_valued", "optimal_xcorn_max"] > 0.5
    assert cases.loc["operations", "optimal_xcorn_max"] < 0.5


def test_stage_ii_promotion_boundary_when_generated():
    path = ROOT / "visualization/stage_ii/source_data/supplementary_stopping_summary.csv"
    if path.exists():
        frame = pd.read_csv(path)
        assert set(frame.loc[frame["experiment_pass"].astype(bool), "experiment_id"]) == {"E2", "E6"}
