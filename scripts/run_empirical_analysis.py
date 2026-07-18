#!/usr/bin/env python3
"""Rebuild and run the frozen Issue 7 empirical analysis in one command."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "empirical/src"))

from crop_empirical.empirical_analysis import (  # noqa: E402
    boundary_table,
    build_analysis_panel,
    definition_summary,
    discordance_analysis,
    exact_permutation_benchmark,
    heterogeneity_summaries,
    lagged_2024_validation,
    leave_one_year_out,
    load_design,
    national_check,
    sample_flow,
    sha256_file,
    summarize,
)

DEFAULT_OUTPUT = ROOT / "empirical/outputs"
DEFAULT_NASS_PROCESSED = ROOT / "data/processed/nass_state_crop_2022_2024.csv"
DEFAULT_ANALYSIS_PANEL = ROOT / "data/processed/empirical_state_crop_analysis_panel.csv"
DEFAULT_NATIONAL_PANEL = ROOT / "data/processed/canonical_crop_year_panel.csv"


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n")


def write_checksums(directory: Path) -> None:
    paths = sorted(path for path in directory.iterdir() if path.is_file() and path.name != "SHA256SUMS.txt")
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in paths]
    (directory / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--nass-processed", type=Path, default=DEFAULT_NASS_PROCESSED)
    parser.add_argument("--analysis-panel", type=Path, default=DEFAULT_ANALYSIS_PANEL)
    parser.add_argument("--national-panel", type=Path, default=DEFAULT_NATIONAL_PANEL)
    parser.add_argument("--skip-official-validation", action="store_true")
    args = parser.parse_args()

    design = load_design()
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/process_official_data.py"), "--output", str(args.national_panel)],
        check=True,
    )
    if not args.skip_official_validation and args.national_panel.resolve() == DEFAULT_NATIONAL_PANEL.resolve():
        subprocess.run([sys.executable, str(ROOT / "scripts/validate_official_data.py")], check=True)

    parsed, panel = build_analysis_panel(args.national_panel)
    args.nass_processed.parent.mkdir(parents=True, exist_ok=True)
    args.analysis_panel.parent.mkdir(parents=True, exist_ok=True)
    write_csv(parsed, args.nass_processed)
    write_csv(panel, args.analysis_panel)

    detail, rankings = discordance_analysis(panel)
    definitions = definition_summary(detail)
    state_summary, year_summary = heterogeneity_summaries(detail)
    national = national_check(parsed, args.national_panel)
    lagged_rows, lagged_summary = lagged_2024_validation(panel)
    leave_out = leave_one_year_out(detail)
    flow = sample_flow(parsed, panel)
    permutations = exact_permutation_benchmark()
    boundaries = boundary_table()
    summary = summarize(design, parsed, panel, detail, lagged_summary)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "state_crop_panel.csv": panel,
        "discordance_detail.csv": detail,
        "ranking_rows.csv": rankings,
        "definition_summary.csv": definitions,
        "state_heterogeneity.csv": state_summary,
        "year_heterogeneity.csv": year_summary,
        "national_check.csv": national,
        "lagged_2024_ranking_rows.csv": lagged_rows,
        "lagged_2024_validation.csv": lagged_summary,
        "leave_one_year_out.csv": leave_out,
        "sample_flow.csv": flow,
        "permutation_benchmark.csv": permutations,
        "claim_boundaries.csv": boundaries,
    }
    for name, frame in outputs.items():
        write_csv(frame, args.output_dir / name)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    metadata = {
        "command": "python scripts/run_empirical_analysis.py",
        "design_id": design["design_id"],
        "design_sha256": design["design_sha256"],
        "nass_snapshot_sha256": sha256_file(ROOT / "data/raw/usda_nass/crop_production_2024_summary.txt"),
        "national_panel_sha256": sha256_file(args.national_panel),
        "nass_processed_rows": int(len(parsed)),
        "analysis_panel_rows": int(len(panel)),
        "manual_output_edits": False,
    }
    (args.output_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_checksums(args.output_dir)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
