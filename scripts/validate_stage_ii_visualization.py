#!/usr/bin/env python3
"""Validate GOAL-13 exports, source lineage, evidence boundaries and QA assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

import pandas as pd
from PIL import Image
import yaml


ROOT = Path(__file__).resolve().parents[1]
FIGURES = [f"Figure{i}" for i in range(1, 7)] + [f"FigureS{i}" for i in range(1, 5)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_checksum_file(base: Path, checksum_file: Path) -> list[str]:
    errors: list[str] = []
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = base / relative
        if not path.exists() or sha(path) != expected:
            errors.append(f"checksum mismatch: {path}")
    return errors


def main() -> int:
    errors: list[str] = []
    config = yaml.safe_load((ROOT / "visualization/configs/stage_ii_nature_style.yaml").read_text())
    for figure_id in FIGURES:
        section = "main" if not figure_id.startswith("FigureS") else "supplementary"
        width_mm, height_mm = config["dimensions_mm"][figure_id]
        for extension in ["svg", "pdf", "png", "tiff"]:
            path = ROOT / f"figures/stage_ii/{section}/{figure_id}.{extension}"
            if not path.exists() or path.stat().st_size == 0:
                errors.append(f"missing export: {path}")
        png = Image.open(ROOT / f"figures/stage_ii/{section}/{figure_id}.png")
        tiff = Image.open(ROOT / f"figures/stage_ii/{section}/{figure_id}.tiff")
        expected_png = (int(width_mm / 25.4 * 300), int(height_mm / 25.4 * 300))
        expected_tiff = (int(width_mm / 25.4 * 600), int(height_mm / 25.4 * 600))
        if png.size != expected_png:
            errors.append(f"{figure_id} PNG size {png.size} != {expected_png}")
        if tiff.size != expected_tiff:
            errors.append(f"{figure_id} TIFF size {tiff.size} != {expected_tiff}")
        svg_text = (ROOT / f"figures/stage_ii/{section}/{figure_id}.svg").read_text(encoding="utf-8")
        if "<text" not in svg_text or re.search(r"<image(?:\s|>)", svg_text):
            errors.append(f"{figure_id} SVG is not editable vector text")
        for mode in ["grayscale", "deuteranopia"]:
            if not (ROOT / f"visualization/stage_ii/qa/{figure_id}_{mode}.png").exists():
                errors.append(f"missing {mode} QA for {figure_id}")

    captions = pd.read_csv(ROOT / "visualization/stage_ii/captions.csv")
    if set(captions["figure_id"]) != set(FIGURES):
        errors.append("caption inventory is incomplete")
    lineage = pd.read_csv(ROOT / "visualization/stage_ii/source_data/lineage.csv")
    for _, row in lineage.iterrows():
        source = ROOT / row.source_data
        if sha(source) != row.source_sha256:
            errors.append(f"source lineage hash mismatch: {source}")
        for upstream, expected in zip(str(row.upstream_inputs).split(";"), str(row.upstream_sha256).split(";")):
            if sha(ROOT / upstream) != expected:
                errors.append(f"upstream lineage hash mismatch: {upstream}")

    e3 = pd.read_csv(ROOT / "visualization/stage_ii/source_data/figure4_e3_adverse.csv")
    dep = pd.read_csv(ROOT / "visualization/stage_ii/source_data/figure5_dependence_boundary.csv")
    adverse = pd.read_csv(ROOT / "visualization/stage_ii/source_data/supplementary_adverse_inventory.csv")
    if set(e3["promotion_status"]) != {"EXPERIMENT_PRECISION_FAILED_NON_PROMOTED"}:
        errors.append("E3 promotion boundary is missing")
    if set(dep["promotion_status"]) != {"EXPERIMENT_PRECISION_FAILED_NON_PROMOTED"}:
        errors.append("E5 promotion boundary is missing")
    if set(adverse["experiment_id"]) != {"E1", "E3", "E4", "E5"}:
        errors.append("adverse experiment inventory is incomplete")
    stopping = pd.read_csv(ROOT / "visualization/stage_ii/source_data/supplementary_stopping_summary.csv")
    promoted = set(stopping.loc[stopping["experiment_pass"].astype(bool), "experiment_id"])
    if promoted != {"E2", "E6"}:
        errors.append(f"unexpected promoted experiment set: {promoted}")
    infeasible = pd.read_csv(ROOT / "visualization/stage_ii/source_data/supplementary_infeasible_summary.csv")
    if int(infeasible["registered_infeasible"].sum()) != 206:
        errors.append("registered infeasible total is not 206")

    registry = pd.read_csv(ROOT / "evidence_registry/figures.csv")
    registered = set(registry.loc[registry["figure_id"].str.startswith("S2-Figure"), "figure_id"])
    if registered != {f"S2-{x}" for x in FIGURES}:
        errors.append("Stage II figure registry is incomplete")
    for _, row in registry.loc[registry["figure_id"].str.startswith("S2-Figure")].iterrows():
        fid = row.figure_id.removeprefix("S2-")
        section = "main" if not fid.startswith("FigureS") else "supplementary"
        if sha(ROOT / f"figures/stage_ii/{section}/{fid}.svg") != row.checksum:
            errors.append(f"registry checksum mismatch: {fid}")

    errors += check_checksum_file(ROOT / "figures/stage_ii", ROOT / "figures/stage_ii/SHA256SUMS.txt")
    errors += check_checksum_file(ROOT / "visualization/stage_ii/source_data",
                                  ROOT / "visualization/stage_ii/source_data/SHA256SUMS.txt")
    errors += check_checksum_file(ROOT / "visualization/stage_ii/qa",
                                  ROOT / "visualization/stage_ii/qa/SHA256SUMS.txt")
    status = {"validator": "stage_ii_visualization", "passed": not errors,
              "figures": len(FIGURES), "errors": errors}
    report = ROOT / "visualization/stage_ii/validation_report.json"
    report.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
