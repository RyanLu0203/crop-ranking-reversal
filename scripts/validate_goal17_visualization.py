#!/usr/bin/env python3
"""Fail-closed validation for the GOAL-17 visual exploration and final figures."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import zlib

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "figures/goal17"
CANDIDATES = ROOT / "audits/goal17_visual_candidates"
QA = ROOT / "visualization/goal17/qa"
CARD = {
    "charcoal": "#3D3539",
    "supported": "#0F9EA8",
    "soybean": "#008B82",
    "corn": "#45728F",
    "winter_wheat": "#8CD1B2",
    "inconclusive": "#8B84A3",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def rgb(hex_value: str) -> tuple[float, float, float]:
    value = hex_value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def permitted_rgb(value: tuple[float, float, float], tolerance: float = 2e-4) -> bool:
    """Permit card colours, white, and transparent card-to-white derivatives."""
    bases = [rgb(value) for value in CARD.values()]
    white = (1.0, 1.0, 1.0)
    if all(abs(a - b) <= tolerance for a, b in zip(value, white)):
        return True
    for base in bases:
        if all(abs(a - b) <= tolerance for a, b in zip(value, base)):
            return True
        ratios = []
        for observed, channel in zip(value, base):
            if abs(1 - channel) > tolerance:
                ratios.append((1 - observed) / (1 - channel))
        # SVG serializes channels at 8-bit precision, so near-white transparent
        # derivatives require a small ratio-spread allowance after quantization.
        if ratios and -0.004 <= min(ratios) <= 1.004 and max(ratios) - min(ratios) <= 0.011:
            return True
    return False


def pdf_rgb_values(path: Path) -> set[tuple[float, float, float]]:
    values: set[tuple[float, float, float]] = set()
    data = path.read_bytes()
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        stream = match.group(1)
        try:
            stream = zlib.decompress(stream)
        except zlib.error:
            pass
        pattern = rb"(?<![\d.])([01](?:\.\d+)?)\s+([01](?:\.\d+)?)\s+([01](?:\.\d+)?)\s+(?:rg|RG)\b"
        for triple in re.findall(pattern, stream):
            values.add(tuple(float(value) for value in triple))
    return values


def main() -> int:
    errors: list[str] = []
    final_rows = rows(FINAL / "figure_manifest.csv")
    expected = {f"Figure{i}" for i in range(1, 7)} | {"FigureS6", "FigureS7"}
    if {row["figure_id"] for row in final_rows} != expected:
        errors.append("final manifest must contain Figure1--Figure6 and FigureS6--FigureS7")

    semantic_source = (ROOT / "visualization/style/nature_style.py").read_text(encoding="utf-8")
    required_pairs = {
        '"Corn": CARD["corn"]', '"Soybean": CARD["soybean"]',
        '"Winter Wheat": CARD["winter_wheat"]', '"positive_supported": CARD["promoted"]',
        '"adverse_unresolved": CARD["adverse"]',
    }
    for pair in required_pairs:
        if pair not in semantic_source:
            errors.append(f"semantic colour mapping missing: {pair}")

    for row in final_rows:
        figure_id = row["figure_id"]
        width = float(row["width_mm"])
        height = float(row["height_mm"])
        if abs(width - 183) > 0.01 or not 120 <= height <= 150:
            errors.append(f"{figure_id}: unexpected final dimensions {width} x {height} mm")
        for extension in ("svg", "pdf", "png", "tiff"):
            path = ROOT / row[f"{extension}_path"]
            if not path.exists() or not path.stat().st_size:
                errors.append(f"{figure_id}: missing {extension} export")
            elif sha(path) != row[f"{extension}_sha256"]:
                errors.append(f"{figure_id}: {extension} manifest checksum mismatch")
        for extension, dpi in (("png", 300), ("tiff", 600)):
            image = Image.open(ROOT / row[f"{extension}_path"])
            expected_size = (width / 25.4 * dpi, height / 25.4 * dpi)
            if any(abs(actual - target) > 1.1 for actual, target in zip(image.size, expected_size)):
                errors.append(f"{figure_id}: {extension} dimensions {image.size} fail {dpi}-dpi contract")

        svg_path = ROOT / row["svg_path"]
        svg = svg_path.read_text(encoding="utf-8")
        if "<text" not in svg or re.search(r"<image(?:\s|>)", svg):
            errors.append(f"{figure_id}: SVG text is not editable vector content")
        font_sizes = [float(value) for value in re.findall(r"font:\s*(?:(?:\d+|normal|bold)\s+)?([0-9.]+)px", svg)]
        if not font_sizes or min(font_sizes) < 5.5 - 1e-6:
            errors.append(f"{figure_id}: essential SVG text falls below 5.5 pt")
        for value in set(re.findall(r"#[0-9A-Fa-f]{6}", svg)):
            if not permitted_rgb(rgb(value)):
                errors.append(f"{figure_id}: off-card SVG colour {value}")
        pdf_colours = pdf_rgb_values(ROOT / row["pdf_path"])
        if not pdf_colours:
            errors.append(f"{figure_id}: no PDF RGB operators found")
        for value in pdf_colours:
            if not permitted_rgb(value):
                errors.append(f"{figure_id}: off-card PDF colour {value}")

    candidate_rows = rows(CANDIDATES / "candidate_manifest.csv")
    if len(candidate_rows) != 12:
        errors.append(f"expected 12 candidate concepts, found {len(candidate_rows)}")
    for group in range(1, 7):
        concepts = {row["concept"] for row in candidate_rows if int(row["group"]) == group}
        if concepts != {"A", "B"}:
            errors.append(f"Figure {group}: candidate concepts are not A and B")
    for row in candidate_rows:
        if float(row["width_mm"]) != 183 or row["status"] != "RENDERED_FINAL_SIZE":
            errors.append(f"Figure {row['group']}{row['concept']}: not rendered at final size")
        for extension in ("png", "pdf", "svg"):
            if not (ROOT / row[extension]).exists():
                errors.append(f"Figure {row['group']}{row['concept']}: missing candidate {extension}")

    for folder in (CANDIDATES, QA):
        for mode in ("full", "grayscale", "deuteranopia", "protanopia"):
            name = "contact_sheet.png" if folder == CANDIDATES and mode == "full" else f"contact_sheet_{mode}.png"
            if not (folder / name).exists():
                errors.append(f"missing {folder.relative_to(ROOT)} {mode} contact sheet")

    renderer = rows(QA / "renderer_qa.csv")
    if {row["figure_id"] for row in renderer} != expected:
        errors.append("renderer QA does not cover every final figure")
    if any(int(row["bounds_failure_count"]) or int(row["title_collision_count"]) for row in renderer):
        errors.append("renderer QA contains clipping or title collisions")
    report = json.loads((QA / "generation_report.json").read_text(encoding="utf-8"))
    if report.get("renderer_bounds_failures") != 0 or report.get("renderer_title_collisions") != 0:
        errors.append("generation report contains renderer failures")

    for line in (FINAL / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        expected_sha, relative = line.split("  ", 1)
        path = FINAL / relative
        if not path.exists() or sha(path) != expected_sha:
            errors.append(f"final checksum mismatch: {relative}")
    source = rows(ROOT / "data/goal17/source_registry.csv")
    if len(source) != 1:
        errors.append("fixed-vintage geometry source registry must contain exactly one source")
    else:
        geometry = ROOT / source[0]["file"]
        if not geometry.exists() or sha(geometry) != source[0]["sha256"] or int(source[0]["features"]) != 56:
            errors.append("fixed-vintage Census geometry provenance fails")

    status = {
        "validator": "goal17_visualization",
        "passed": not errors,
        "final_figures": len(final_rows),
        "candidate_concepts": len(candidate_rows),
        "minimum_font_pt": min(
            float(value)
            for row in final_rows
            for value in re.findall(
                r"font:\s*(?:(?:\d+|normal|bold)\s+)?([0-9.]+)px",
                (ROOT / row["svg_path"]).read_text(encoding="utf-8"),
            )
        ),
        "renderer_bounds_failures": sum(int(row["bounds_failure_count"]) for row in renderer),
        "renderer_title_collisions": sum(int(row["title_collision_count"]) for row in renderer),
        "svg_and_pdf_palette_validation": "PASS" if not any("colour" in error for error in errors) else "FAIL",
        "errors": errors,
    }
    (QA / "validation_report.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
