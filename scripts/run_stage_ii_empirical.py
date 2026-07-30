#!/usr/bin/env python3
"""Run the frozen GOAL-15 admitted-data empirical strengthening analysis."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "empirical/src"))

from crop_empirical.stage_ii_analysis import (  # noqa: E402
    build_transition_panel,
    claim_boundaries,
    concurrent_inversion_summary,
    definition_agreement,
    inertia_association,
    leave_one_state_out,
    load_stage_ii_design,
    model_observed_boundary,
    national_definition_analysis,
    rank_transition_events,
    sha256_file,
    state_year_heterogeneity,
    transition_summary,
)


DEFAULT_OUTPUT = ROOT / "empirical/stage_ii/outputs"


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.12g")


def write_checksums(directory: Path) -> None:
    excluded = {"SHA256SUMS.txt", "reproducibility.json", "validation_report.json"}
    paths = sorted(path for path in directory.iterdir() if path.is_file() and path.name not in excluded)
    (directory / "SHA256SUMS.txt").write_text(
        "".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in paths),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    design = load_stage_ii_design()
    panel_path = ROOT / design["admitted_inputs"]["state_crop_panel"]
    national_path = ROOT / design["admitted_inputs"]["national_panel"]
    parsed_path = ROOT / "data/processed/nass_state_crop_2022_2024.csv"
    detail_path = ROOT / "empirical/outputs/discordance_detail.csv"
    panel = pd.read_csv(panel_path)
    national = pd.read_csv(national_path)
    parsed = pd.read_csv(parsed_path)
    detail = pd.read_csv(detail_path)

    transition = build_transition_panel(panel)
    events = rank_transition_events(transition)
    inversion = concurrent_inversion_summary(detail, design)
    transitions = transition_summary(events, design)
    agreement = definition_agreement(detail)
    state, year = state_year_heterogeneity(detail)
    state_holdout = leave_one_state_out(detail)
    inertia = inertia_association(transition, design)
    national_detail, aggregation = national_definition_analysis(panel, national, parsed)
    evidence_layers = model_observed_boundary()
    boundaries = claim_boundaries()
    main_rows = []
    for source, family in [(inversion, "CONCURRENT"), (transitions, "LAGGED_TRANSITION")]:
        selected_metrics = {"inversion_intensity", "top_rank_reversal_rate"} if family == "CONCURRENT" else {
            "lagged_inversion_intensity", "lagged_top_match_rate", "lagged_top_minus_other_share_change",
            "acreage_top_change_rate",
        }
        for _, row in source.loc[source["metric"].isin(selected_metrics)].iterrows():
            main_rows.append({
                "result_family": family, "ranking_definition": row.ranking_definition,
                "estimand": row.metric, "estimate": row.estimate,
                "ci_low": row.ci_low, "ci_high": row.ci_high,
                "state_clusters": row.states, "observations": row.observations,
                "identification_status": row.claim_level,
            })
    main_table = pd.DataFrame(main_rows)
    robustness_rows = []
    for definition in sorted(detail["ranking_definition"].unique()):
        held = state_holdout.loc[state_holdout["ranking_definition"].eq(definition)]
        yearly = year.loc[year["ranking_definition"].eq(definition)]
        national_row = aggregation.loc[aggregation["ranking_definition"].eq(definition)].iloc[0]
        robustness_rows.extend([
            {"ranking_definition": definition, "robustness_check": "LEAVE_ONE_STATE_OUT_INVERSION",
             "minimum": held["mean_inversion_intensity"].min(), "maximum": held["mean_inversion_intensity"].max(),
             "cells": len(held), "claim_level": "DESCRIPTIVE_ROBUSTNESS"},
            {"ranking_definition": definition, "robustness_check": "YEAR_RANGE_INVERSION",
             "minimum": yearly["mean_inversion_intensity"].min(), "maximum": yearly["mean_inversion_intensity"].max(),
             "cells": len(yearly), "claim_level": "DESCRIPTIVE_ROBUSTNESS"},
            {"ranking_definition": definition, "robustness_check": "NATIONAL_AGGREGATION_INVERSION",
             "minimum": national_row["national_mean_inversion_intensity"],
             "maximum": national_row["national_mean_inversion_intensity"],
             "cells": int(national_row["national_years"]), "claim_level": "DESCRIPTIVE_AGGREGATION_BOUNDARY"},
        ])
    robustness_table = pd.DataFrame(robustness_rows)

    outputs = {
        "transition_panel.csv": transition,
        "rank_transition_events.csv": events,
        "inversion_intensity_summary.csv": inversion,
        "transition_summary.csv": transitions,
        "definition_agreement.csv": agreement,
        "state_heterogeneity.csv": state,
        "year_heterogeneity.csv": year,
        "leave_one_state_out.csv": state_holdout,
        "inertia_association.csv": inertia,
        "national_definition_detail.csv": national_detail,
        "aggregation_summary.csv": aggregation,
        "observed_model_unidentified.csv": evidence_layers,
        "claim_boundaries.csv": boundaries,
        "main_results_table.csv": main_table,
        "robustness_table.csv": robustness_table,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in outputs.items():
        write_csv(frame, args.output_dir / name)

    lineage = pd.DataFrame([
        {
            "output_file": name,
            "upstream_inputs": ";".join([
                str(panel_path.relative_to(ROOT)), str(national_path.relative_to(ROOT)),
                str(parsed_path.relative_to(ROOT)), str(detail_path.relative_to(ROOT)),
                str(Path("empirical/configs/stage_ii_empirical_design.yaml")),
            ]),
            "upstream_sha256": ";".join([
                sha256_file(panel_path), sha256_file(national_path), sha256_file(parsed_path),
                sha256_file(detail_path), design["design_sha256"],
            ]),
            "output_sha256": sha256_file(args.output_dir / name),
            "manual_edits": False,
        }
        for name in outputs
    ])
    write_csv(lineage, args.output_dir / "lineage.csv")

    summary = {
        "design_id": design["design_id"], "design_sha256": design["design_sha256"],
        "state_crop_rows": int(len(panel)), "state_years": int(panel[["state", "year"]].drop_duplicates().shape[0]),
        "states": int(panel["state"].nunique()), "years": sorted(int(x) for x in panel["year"].unique()),
        "crop_transition_rows": int(len(transition)), "rank_transition_events": int(len(events)),
        "ranking_definitions": int(detail["ranking_definition"].nunique()),
        "bootstrap_replications": int(design["uncertainty"]["replications"]),
        "county_analysis_admissible": False, "private_constraint_identified": False,
        "observed_acreage_is_optimum": False, "cvar_identified": False,
        "copula_causality_identified": False, "welfare_identified": False,
        "result_scope": "DESCRIPTIVE_ACCOUNTING_AND_MODEL_CONSISTENCY_ONLY",
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    metadata = {
        "command": "python scripts/run_stage_ii_empirical.py",
        "design_id": design["design_id"], "design_sha256": design["design_sha256"],
        "input_hashes": {
            str(panel_path.relative_to(ROOT)): sha256_file(panel_path),
            str(national_path.relative_to(ROOT)): sha256_file(national_path),
            str(parsed_path.relative_to(ROOT)): sha256_file(parsed_path),
            str(detail_path.relative_to(ROOT)): sha256_file(detail_path),
        },
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
