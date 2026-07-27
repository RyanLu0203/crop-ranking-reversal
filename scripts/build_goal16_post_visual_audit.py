#!/usr/bin/env python3
"""Build deterministic before/after visual comparison sheets."""

from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audits/goal16_visual_comparison"
PAIRS = {
    "183mm": ("audits/goal16_visual_baseline/contact_sheet_183mm.png", "visualization/stage_ii/qa/contact_sheet_full.png"),
    "89mm": ("audits/goal16_visual_baseline/contact_sheet_89mm.png", "visualization/stage_ii/qa/contact_sheet_width89mm.png"),
    "grayscale": ("audits/goal16_visual_baseline/contact_sheet_grayscale.png", "visualization/stage_ii/qa/contact_sheet_grayscale.png"),
    "deuteranopia": ("audits/goal16_visual_baseline/contact_sheet_deuteranopia.png", "visualization/stage_ii/qa/contact_sheet_deuteranopia.png"),
    "protanopia": ("audits/goal16_visual_baseline/contact_sheet_protanopia.png", "visualization/stage_ii/qa/contact_sheet_protanopia.png"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def comparison(before_path: Path, after_path: Path, target: Path) -> None:
    before = Image.open(before_path).convert("RGB")
    after = Image.open(after_path).convert("RGB")
    width = 1100
    before.thumbnail((width, 4200), Image.Resampling.LANCZOS)
    after.thumbnail((width, 4200), Image.Resampling.LANCZOS)
    header = 58
    canvas = Image.new("RGB", (2 * width + 30, max(before.height, after.height) + header), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((20, 18), "BEFORE · PR #31 baseline", fill="#3D3539")
    draw.text((width + 50, 18), "AFTER · GOAL-16 reconstruction", fill="#3D3539")
    canvas.paste(before, ((width - before.width) // 2, header))
    canvas.paste(after, (width + 30 + (width - after.width) // 2, header))
    canvas.save(target, dpi=(150, 150))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    targets = []
    for mode, (before, after) in PAIRS.items():
        target = OUT / f"before_after_{mode}.png"
        comparison(ROOT / before, ROOT / after, target)
        targets.append(target)
    checksum = OUT / "SHA256SUMS.txt"
    checksum.write_text("".join(f"{sha(path)}  {path.name}\n" for path in sorted(targets)), encoding="utf-8")
    print(f"goal16_comparison_sheets={len(targets)}")


if __name__ == "__main__":
    main()
