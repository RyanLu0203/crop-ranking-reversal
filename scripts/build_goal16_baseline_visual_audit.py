#!/usr/bin/env python3
"""Render the frozen GOAL-16 pre-redesign figure audit package.

This script is intentionally independent of the figure generator: it reads the
committed Stage II exports at commit 4088e62 and creates only diagnostic views.
"""

from __future__ import annotations

import csv
import hashlib
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audits" / "goal16_visual_baseline"
FIGURES = [f"Figure{i}" for i in range(1, 7)] + [f"FigureS{i}" for i in range(1, 5)]
MM_TO_PX_300 = {183: round(183 / 25.4 * 300), 89: round(89 / 25.4 * 300)}


def source_path(figure_id: str, suffix: str) -> Path:
    section = "main" if not figure_id.startswith("FigureS") else "supplementary"
    return ROOT / "figures" / "stage_ii" / section / f"{figure_id}.{suffix}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cvd(image: Image.Image, mode: str) -> Image.Image:
    rgb = np.asarray(image.convert("RGB"), dtype=float) / 255.0
    matrices = {
        "deuteranopia": np.array(
            [[0.625, 0.375, 0.000], [0.700, 0.300, 0.000], [0.000, 0.300, 0.700]]
        ),
        "protanopia": np.array(
            [[0.567, 0.433, 0.000], [0.558, 0.442, 0.000], [0.000, 0.242, 0.758]]
        ),
    }
    transformed = np.clip(rgb @ matrices[mode].T, 0, 1)
    return Image.fromarray(np.uint8(np.rint(transformed * 255)))


def fit_width(image: Image.Image, width: int) -> Image.Image:
    height = round(image.height * width / image.width)
    return image.resize((width, height), Image.Resampling.LANCZOS)


def contact_sheet(mode: str, paths: list[tuple[str, Path]]) -> Path:
    cell_width, cell_height = 950, 720
    sheet = Image.new("RGB", (cell_width * 2, cell_height * 5), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (figure_id, path) in enumerate(paths):
        row, col = divmod(index, 2)
        image = Image.open(path).convert("RGB")
        image.thumbnail((cell_width - 60, cell_height - 80), Image.Resampling.LANCZOS)
        left = col * cell_width + (cell_width - image.width) // 2
        top = row * cell_height + 48 + (cell_height - 58 - image.height) // 2
        sheet.paste(image, (left, top))
        draw.text((col * cell_width + 18, row * cell_height + 16), figure_id, fill="#3D3539")
    path = OUT / f"contact_sheet_{mode}.png"
    sheet.save(path, dpi=(150, 150))
    return path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    modes = ["full_pdf", "183mm", "89mm", "grayscale", "deuteranopia", "protanopia"]
    for mode in modes:
        (OUT / mode).mkdir(parents=True, exist_ok=True)

    records: list[dict[str, object]] = []
    mode_paths: dict[str, list[tuple[str, Path]]] = {mode: [] for mode in modes}
    for figure_id in FIGURES:
        pdf = source_path(figure_id, "pdf")
        png = source_path(figure_id, "png")
        rendered_prefix = OUT / "full_pdf" / figure_id
        subprocess.run(
            ["pdftoppm", "-singlefile", "-r", "200", "-png", str(pdf), str(rendered_prefix)],
            check=True,
        )
        full_pdf = rendered_prefix.with_suffix(".png")
        mode_paths["full_pdf"].append((figure_id, full_pdf))

        original = Image.open(png).convert("RGB")
        generated = {
            "183mm": fit_width(original, MM_TO_PX_300[183]),
            "89mm": fit_width(original, MM_TO_PX_300[89]),
            "grayscale": ImageOps.grayscale(original).convert("RGB"),
            "deuteranopia": cvd(original, "deuteranopia"),
            "protanopia": cvd(original, "protanopia"),
        }
        for mode, image in generated.items():
            path = OUT / mode / f"{figure_id}.png"
            image.save(path, dpi=(300, 300))
            mode_paths[mode].append((figure_id, path))

        records.append(
            {
                "figure_id": figure_id,
                "source_pdf": str(pdf.relative_to(ROOT)),
                "source_pdf_sha256": sha256(pdf),
                "source_png": str(png.relative_to(ROOT)),
                "source_png_sha256": sha256(png),
                "source_width_px": original.width,
                "source_height_px": original.height,
                "audit_width_183mm_px": generated["183mm"].width,
                "audit_width_89mm_px": generated["89mm"].width,
            }
        )

    for mode, paths in mode_paths.items():
        contact_sheet(mode, paths)

    manifest = OUT / "baseline_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    hashes = []
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            hashes.append(f"{sha256(path)}  {path.relative_to(ROOT)}")
    (OUT / "SHA256SUMS.txt").write_text("\n".join(hashes) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
