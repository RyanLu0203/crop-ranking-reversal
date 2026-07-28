from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from visualization.style.nature_style import ALLOWED_HEX, CARD, CROP_COLORS, palette  # noqa: E402


def test_fixed_card_and_crop_semantics() -> None:
    assert set(CARD.values()) == {"#3D3539", "#0F9EA8", "#008B82", "#45728F", "#8CD1B2", "#8B84A3"}
    assert CROP_COLORS == {"Corn": "#45728F", "Soybean": "#008B82", "Winter Wheat": "#8CD1B2"}
    assert set(value.lower() for value in palette().values()).issubset(ALLOWED_HEX)


def test_generated_svgs_use_only_fixed_card_or_white() -> None:
    for path in sorted((ROOT / "figures/stage_ii").rglob("*.svg")):
        used = set(re.findall(r"#[0-9a-fA-F]{6}", path.read_text(encoding="utf-8").lower()))
        assert used.issubset(ALLOWED_HEX), (path, used - ALLOWED_HEX)
