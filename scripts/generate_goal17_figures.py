#!/usr/bin/env python3
"""Generate the selected GOAL-17 main and supplementary figure system."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.text import Text
import numpy as np
from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import generate_goal17_visual_candidates as concepts  # noqa: E402
from visualization.style.nature_style import CARD  # noqa: E402


OUT = ROOT / "figures" / "goal17"
QA = ROOT / "visualization" / "goal17" / "qa"
BUILDERS = {
    "Figure1": ("main", concepts.fig1b, "Ordinal rankings do not identify cardinal allocations"),
    "Figure2": ("main", concepts.fig2b, "Distinct mechanisms can generate the same rank–allocation disagreement"),
    "Figure3": ("main", concepts.fig3a, "Model components jointly reshape allocation, value and local pressure"),
    "Figure4": ("main", concepts.fig4a, "Assigned operational interventions force universal reversal"),
    "Figure5": ("main", concepts.fig5a, "Information and flexibility are not universally complementary"),
    "Figure6": ("main", concepts.fig6a, "Rank–acreage discordance varies across place, time and definition"),
    "FigureS6": ("supplementary", concepts.fig6b, "Definition, transition and sample sensitivity in the official-data panel"),
    "FigureS7": ("supplementary", concepts.fig4b, "Factorial response surfaces and operational mechanism detail"),
}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(figure_id: str, builder, title: str) -> plt.Figure:
    fig = builder()
    if fig._suptitle is None:
        fig.suptitle(title)
    else:
        fig._suptitle.set_text(title)
        fig._suptitle.set_fontsize(8.4)
        fig._suptitle.set_fontweight("bold")
        fig._suptitle.set_color(CARD["charcoal"])
    fig.canvas.draw()
    return fig


def renderer_qa(fig: plt.Figure) -> dict[str, object]:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    canvas = fig.bbox
    bounds_failures: list[str] = []
    texts: list[tuple[str, object]] = []
    for item in fig.findobj(match=Text):
        value = item.get_text().strip()
        if not value or not item.get_visible():
            continue
        bbox = item.get_window_extent(renderer=renderer)
        if bbox.x0 < canvas.x0 - 2 or bbox.y0 < canvas.y0 - 2 or bbox.x1 > canvas.x1 + 2 or bbox.y1 > canvas.y1 + 2:
            bounds_failures.append(value[:80])
        if item in fig.texts or item in [ax.title for ax in fig.axes] or item in [ax._left_title for ax in fig.axes]:
            texts.append((value, bbox))
    title_collisions: list[str] = []
    for i, (left_text, left_box) in enumerate(texts):
        for right_text, right_box in texts[i + 1:]:
            overlap_w = min(left_box.x1, right_box.x1) - max(left_box.x0, right_box.x0)
            overlap_h = min(left_box.y1, right_box.y1) - max(left_box.y0, right_box.y0)
            if overlap_w > 2 and overlap_h > 2:
                title_collisions.append(f"{left_text[:40]} | {right_text[:40]}")
    return {
        "bounds_failure_count": len(bounds_failures),
        "bounds_failures": "; ".join(bounds_failures),
        "title_collision_count": len(title_collisions),
        "title_collisions": "; ".join(title_collisions),
    }


def export(fig: plt.Figure, figure_id: str, section: str) -> dict[str, object]:
    target = OUT / section
    target.mkdir(parents=True, exist_ok=True)
    paths = {ext: target / f"{figure_id}.{ext}" for ext in ["svg", "pdf", "png", "tiff"]}
    fig.savefig(paths["svg"], format="svg", metadata={"Date": "2026-07-22"})
    concepts.normalize_svg(paths["svg"])
    fig.savefig(paths["pdf"], format="pdf", metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(paths["png"], format="png", dpi=300, metadata={"Software": "crop-ranking-reversal GOAL17"})
    fig.savefig(paths["tiff"], format="tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    width_mm, height_mm = (value * 25.4 for value in fig.get_size_inches())
    return {
        "figure_id": figure_id,
        "section": section,
        "width_mm": round(width_mm, 3),
        "height_mm": round(height_mm, 3),
        **{f"{ext}_path": str(path.relative_to(ROOT)) for ext, path in paths.items()},
        **{f"{ext}_sha256": sha(path) for ext, path in paths.items()},
    }


def transform(image: Image.Image, mode: str) -> Image.Image:
    if mode == "full":
        return image.convert("RGB")
    if mode == "grayscale":
        return ImageOps.grayscale(image).convert("RGB")
    matrices = {
        "deuteranopia": np.array([[0.625, 0.375, 0.000], [0.700, 0.300, 0.000], [0.000, 0.300, 0.700]]),
        "protanopia": np.array([[0.567, 0.433, 0.000], [0.558, 0.442, 0.000], [0.000, 0.242, 0.758]]),
    }
    rgb = np.asarray(image.convert("RGB"), dtype=float) / 255.0
    return Image.fromarray(np.uint8(np.rint(np.clip(rgb @ matrices[mode].T, 0, 1) * 255)))


def contact_sheet(records: list[dict[str, object]], mode: str) -> Path:
    columns, cell_w, cell_h = 2, 1000, 760
    rows = math.ceil(len(records) / columns)
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for index, record in enumerate(records):
        image = transform(Image.open(ROOT / str(record["png_path"])), mode)
        image.thumbnail((940, 690), Image.Resampling.LANCZOS)
        row, col = divmod(index, columns)
        x = col * cell_w + (cell_w - image.width) // 2
        y = row * cell_h + 50 + (cell_h - 60 - image.height) // 2
        sheet.paste(image, (x, y))
        draw.text((col * cell_w + 18, row * cell_h + 16), str(record["figure_id"]), fill=CARD["charcoal"])
    path = QA / f"contact_sheet_{mode}.png"
    sheet.save(path, dpi=(150, 150))
    return path


def main() -> int:
    QA.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    renderer_rows: list[dict[str, object]] = []
    for figure_id, (section, builder, title) in BUILDERS.items():
        fig = prepare(figure_id, builder, title)
        renderer_rows.append({"figure_id": figure_id, **renderer_qa(fig)})
        records.append(export(fig, figure_id, section))
        plt.close(fig)

    with (OUT / "figure_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(records)
    with (QA / "renderer_qa.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(renderer_rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(renderer_rows)

    contacts = {mode: str(contact_sheet(records, mode).relative_to(ROOT)) for mode in ["full", "grayscale", "deuteranopia", "protanopia"]}
    files = sorted(path for path in OUT.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt")
    (OUT / "SHA256SUMS.txt").write_text("".join(f"{sha(path)}  {path.relative_to(OUT)}\n" for path in files), encoding="utf-8")
    result = {"figures": len(records), "manifest": str((OUT / "figure_manifest.csv").relative_to(ROOT)), "contact_sheets": contacts,
              "renderer_bounds_failures": sum(int(row["bounds_failure_count"]) for row in renderer_rows),
              "renderer_title_collisions": sum(int(row["title_collision_count"]) for row in renderer_rows)}
    (QA / "generation_report.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
