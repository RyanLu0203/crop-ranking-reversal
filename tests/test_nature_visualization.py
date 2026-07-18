from pathlib import Path

import yaml

from crop_visualization.visualization_style import NATURE_COLORS, mm_to_inches


ROOT=Path(__file__).resolve().parents[1]


def test_fixed_nature_palette_matches_contract():
    cfg=yaml.safe_load((ROOT/"visualization/configs/nature_style.yaml").read_text())
    semantic={k:v for k,v in cfg["palette"].items() if k!="paper"}
    assert semantic==dict(NATURE_COLORS)


def test_target_dimensions_are_exact():
    assert mm_to_inches(183,150)==(183/25.4,150/25.4)


def test_visual_system_has_no_legacy_inputs():
    code=(ROOT/"visualization/src/crop_visualization/nature_figures.py").read_text()
    assert "plotting.py" not in code


def test_simulation_outputs_are_supplementary_only():
    registry=(ROOT/"evidence_registry/figures.csv").read_text()
    assert "FigureS1,supplementary" in registry
    assert "FigureS2,supplementary" in registry
    assert registry.count("NONHEADLINE")>=2
