#!/usr/bin/env python3
"""Build deterministic figure-accessibility and PDF-page QA contact sheets."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audits" / "issue36_visual_qa"
FIGURES = [ROOT / "figures" / "issue34" / f"Figure{i}.png" for i in range(1, 7)]
PDFS = [ROOT / "main_manuscript.pdf", ROOT / "supplementary_information.pdf"]

CVD_MATRICES = {
    "deuteranopia": np.array(
        [[0.625, 0.375, 0.000], [0.700, 0.300, 0.000], [0.000, 0.300, 0.700]]
    ),
    "protanopia": np.array(
        [[0.567, 0.433, 0.000], [0.558, 0.442, 0.000], [0.000, 0.242, 0.758]]
    ),
}


def accessible(image: Image.Image, mode: str) -> Image.Image:
    rgb = image.convert("RGB")
    if mode == "full":
        return rgb
    if mode == "grayscale":
        return ImageOps.grayscale(rgb).convert("RGB")
    pixels = np.asarray(rgb, dtype=float) / 255.0
    transformed = np.clip(pixels @ CVD_MATRICES[mode].T, 0.0, 1.0)
    return Image.fromarray(np.uint8(np.rint(transformed * 255.0))).convert("RGB")


def contact_sheet(
    records: list[tuple[str, Image.Image]],
    *,
    columns: int,
    cell_width: int,
    cell_height: int,
) -> Image.Image:
    rows = (len(records) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, (label, source) in enumerate(records):
        image = source.copy()
        image.thumbnail((cell_width - 30, cell_height - 45), Image.Resampling.LANCZOS)
        x0 = (index % columns) * cell_width
        y0 = (index // columns) * cell_height
        x = x0 + (cell_width - image.width) // 2
        y = y0 + 28 + (cell_height - 35 - image.height) // 2
        sheet.paste(image, (x, y))
        draw.text((x0 + 12, y0 + 8), label, fill="#024E52", font=font)
    return sheet


def render_pdf(pdf: Path, temp_dir: Path) -> list[Path]:
    prefix = temp_dir / pdf.stem
    subprocess.run(
        ["pdftoppm", "-png", "-r", "120", str(pdf), str(prefix)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return sorted(temp_dir.glob(f"{pdf.stem}-*.png"))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    figure_records = [(path.stem, Image.open(path).convert("RGB")) for path in FIGURES]
    outputs: dict[str, str] = {}
    for mode in ("full", "grayscale", "deuteranopia", "protanopia"):
        transformed = [(label, accessible(image, mode)) for label, image in figure_records]
        sheet = contact_sheet(transformed, columns=2, cell_width=950, cell_height=700)
        path = OUT / f"figure_contact_{mode}.png"
        sheet.save(path, optimize=False)
        outputs[mode] = str(path.relative_to(ROOT))

    page_counts: dict[str, int] = {}
    with tempfile.TemporaryDirectory(prefix="issue36-pdf-qa-") as temp:
        temp_dir = Path(temp)
        for pdf in PDFS:
            page_paths = render_pdf(pdf, temp_dir)
            pages = [
                (f"{pdf.stem} p.{index}", Image.open(path).convert("RGB"))
                for index, path in enumerate(page_paths, start=1)
            ]
            sheet = contact_sheet(pages, columns=4, cell_width=420, cell_height=570)
            target = OUT / f"{pdf.stem}_page_contact.png"
            sheet.save(target, optimize=False)
            outputs[f"{pdf.stem}_pages"] = str(target.relative_to(ROOT))
            detail_paths: list[str] = []
            for start in range(0, len(pages), 4):
                chunk = pages[start : start + 4]
                detail = contact_sheet(
                    chunk, columns=2, cell_width=850, cell_height=1120
                )
                detail_target = OUT / (
                    f"{pdf.stem}_pages_{start + 1:02d}-{start + len(chunk):02d}.png"
                )
                detail.save(detail_target, optimize=False)
                detail_paths.append(str(detail_target.relative_to(ROOT)))
            outputs[f"{pdf.stem}_page_details"] = detail_paths
            page_counts[pdf.name] = len(pages)

    report = {
        "status": "GENERATED_FOR_MANUAL_INSPECTION",
        "figure_count": len(figure_records),
        "figure_modes": ["full", "grayscale", "deuteranopia", "protanopia"],
        "page_counts": page_counts,
        "outputs": outputs,
        "note": (
            "Colour-vision simulations are QA transforms, not diagnostic models. "
            "PASS is assigned only after manual inspection at contact-sheet and full-page scale."
        ),
    }
    (OUT / "generation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
