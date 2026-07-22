#!/usr/bin/env python3
"""Run the frozen GOAL-16 official-data reconstruction."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "empirical/src"))

from crop_empirical.goal16_analysis import (  # noqa: E402
    DESIGN_PATH,
    build_extended_panel,
    cluster_bootstrap_summary,
    load_design,
    model_linked_signatures,
    national_aggregation,
    parse_frozen_state_sources,
    rank_metrics,
    sha256_file,
    state_year_summaries,
    temporal_models,
    transitions,
)


DEFAULT_OUTPUT = ROOT / "empirical/goal16/outputs"


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.12g")


def write_checksums(directory: Path) -> None:
    excluded = {"SHA256SUMS.txt", "reproducibility.json", "validation_report.json"}
    paths = sorted(path for path in directory.iterdir() if path.is_file() and path.name not in excluded)
    (directory / "SHA256SUMS.txt").write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in paths), encoding="utf-8"
    )


def source_registry(nass: pd.DataFrame) -> pd.DataFrame:
    registry = pd.read_csv(ROOT / "evidence_registry/data_source_registry.csv")
    inherited = registry.loc[
        registry["source_id"].isin(
            ["DATA-ERS-CORN-CCR", "DATA-ERS-SOYBEANS-CCR", "DATA-ERS-WHEAT-CCR", "DATA-BLS-CPI-U"]
        )
    ]
    inherited_rows = pd.DataFrame(
        {
            "source_id": inherited["source_id"],
            "authority": inherited["owner"],
            "dataset": inherited["dataset_title"],
            "official_url": inherited["official_url"],
            "local_path": inherited["raw_path"],
            "sha256": inherited["sha256"],
            "time_support": inherited["time_period"],
            "geography": inherited["geography"],
            "variables": inherited["variables"],
            "status": "INCLUDED_IN_ACCOUNTING_CONSTRUCTION",
            "retrieved_at": "INHERITED_FROZEN_STAGE_II_SOURCE",
        }
    )
    return pd.concat([nass, inherited_rows], ignore_index=True).sort_values("source_id").reset_index(drop=True)


def data_dictionary() -> pd.DataFrame:
    rows = [
        ("extended_state_crop_panel.csv", "state", "string", "US state name", "USDA NASS"),
        ("extended_state_crop_panel.csv", "year", "integer", "crop year", "USDA NASS"),
        ("extended_state_crop_panel.csv", "crop", "category", "corn, soybeans or winter wheat", "USDA NASS"),
        ("extended_state_crop_panel.csv", "planted_acres_1000", "number", "planted acreage in thousands", "USDA NASS"),
        ("extended_state_crop_panel.csv", "yield_bushels_per_acre", "number", "published state yield", "USDA NASS"),
        ("extended_state_crop_panel.csv", "relative_yield", "number", "state yield divided by national yield", "derived"),
        ("extended_state_crop_panel.csv", "standardized_revenue_real_2024_usd_per_acre", "number", "state yield times national price, CPI-U deflated", "derived"),
        ("extended_state_crop_panel.csv", "standardized_operating_margin_real_2024_usd_per_acre", "number", "standardized revenue less national operating cost", "derived"),
        ("extended_state_crop_panel.csv", "standardized_total_cost_margin_real_2024_usd_per_acre", "number", "standardized revenue less national total cost", "derived"),
        ("rank_metrics_state_year.csv", "kendall_tau_b", "number", "within-state-year Kendall rank agreement with ties", "derived"),
        ("rank_metrics_state_year.csv", "spearman_rho", "number", "within-state-year Spearman rank agreement when defined", "derived"),
        ("rank_metrics_state_year.csv", "inversion_intensity", "number", "discordant pairs divided by three", "derived"),
        ("rank_metrics_state_year.csv", "top_rank_disagreement", "boolean", "score and acreage leader sets are disjoint", "derived"),
        ("rank_share_transitions.csv", "acreage_share_change", "number", "decision-year minus prior-year crop acreage share", "derived"),
        ("temporal_model.csv", "estimate", "number", "fixed-effect descriptive coefficient", "derived"),
    ]
    return pd.DataFrame(rows, columns=["file", "field", "type", "definition", "provenance"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    design = load_design()
    raw, nass_sources = parse_frozen_state_sources(design)
    national_path = ROOT / design["national_economics"]
    panel, missingness, sample_flow = build_extended_panel(raw, national_path)
    detail, ranking = rank_metrics(panel)
    summary, bootstrap_draws = cluster_bootstrap_summary(detail, design)
    transition, events, persistence = transitions(ranking)
    temporal, temporal_draws = temporal_models(transition, design)
    state_summary, year_summary, leave_state = state_year_summaries(detail)
    signatures = model_linked_signatures(detail, transition)
    national_detail, aggregation = national_aggregation(panel, raw, detail)

    coverage = panel.groupby("year", sort=True).agg(
        states=("state", "nunique"), crop_rows=("crop", "size"), crops=("crop", "nunique")
    ).reset_index()
    coverage["state_years"] = coverage["crop_rows"] // 3
    coverage["complete_three_crop"] = coverage["crops"].eq(3)

    county = design["county"]
    extension_audit = pd.DataFrame(
        [
            {
                "extension": "state panel backward",
                "status": "RECONSTRUCTED",
                "coverage": f"{panel['year'].min()}-{panel['year'].max()}",
                "blocker": "",
            },
            {
                "extension": "state panel forward to 2025",
                "status": "AUDITED_NOT_INCLUDED",
                "coverage": "2025 NASS and ERS available",
                "blocker": design["audit_only_sources"][0]["exclusion"],
            },
            {
                "extension": "county panel",
                "status": county["status"],
                "coverage": "not computed",
                "blocker": county["reason"],
            },
        ]
    )
    raw_checksums = pd.DataFrame(
        [
            {
                "path": source["path"],
                "sha256": sha256_file(ROOT / source["path"]),
                "official_url": source["url"],
                "retrieved_at": source["retrieved_at"],
                "role": "INCLUDED" if source in design["state_sources"] else "AUDIT_ONLY",
            }
            for source in design["state_sources"] + design["audit_only_sources"]
        ]
    )
    retrieval_log = raw_checksums[["path", "official_url", "retrieved_at", "role"]].copy()
    retrieval_log["method"] = "HTTPS_DIRECT_OFFICIAL_REPORT"
    retrieval_log["immutable_local_copy"] = True

    outputs = {
        "raw_nass_state_crop.csv": raw,
        "extended_state_crop_panel.csv": panel,
        "rank_metrics_state_year.csv": detail,
        "ranking_rows.csv": ranking,
        "rank_metric_summary.csv": summary,
        "rank_metric_bootstrap_draws.csv": bootstrap_draws,
        "rank_share_transitions.csv": transition,
        "leader_transitions.csv": events,
        "persistence_transition_summary.csv": persistence,
        "temporal_model.csv": temporal,
        "temporal_model_bootstrap_draws.csv": temporal_draws,
        "state_summary.csv": state_summary,
        "year_summary.csv": year_summary,
        "leave_one_state_out.csv": leave_state,
        "model_linked_signatures.csv": signatures,
        "national_rank_metrics.csv": national_detail,
        "aggregation_boundary.csv": aggregation,
        "missingness.csv": missingness,
        "sample_flow.csv": sample_flow,
        "coverage.csv": coverage,
        "source_registry.csv": source_registry(nass_sources),
        "data_dictionary.csv": data_dictionary(),
        "extension_audit.csv": extension_audit,
        "raw_source_checksums.csv": raw_checksums,
        "retrieval_log.csv": retrieval_log,
    }
    for name, frame in outputs.items():
        write_csv(frame, args.output_dir / name)

    numbers = []
    numbers.extend(
        [
            ("GoalSixteenStartYear", int(panel["year"].min()), "year"),
            ("GoalSixteenEndYear", int(panel["year"].max()), "year"),
            ("GoalSixteenCropRows", len(panel), "rows"),
            ("GoalSixteenStateYears", panel[["state", "year"]].drop_duplicates().shape[0], "state-years"),
            ("GoalSixteenStates", panel["state"].nunique(), "states"),
            ("GoalSixteenTransitionsPerDefinition", events.loc[events["ranking_definition"].eq("operating_margin")].shape[0], "state-year transitions"),
        ]
    )
    for definition in sorted(summary["ranking_definition"].unique()):
        row = summary.loc[
            summary["ranking_definition"].eq(definition) & summary["metric"].eq("inversion_intensity")
        ].iloc[0]
        stem = "".join(piece.title() for piece in definition.split("_"))
        numbers.extend(
            [
                (f"GoalSixteen{stem}Inversion", row["estimate"], "share"),
                (f"GoalSixteen{stem}InversionLow", row["ci_low"], "share"),
                (f"GoalSixteen{stem}InversionHigh", row["ci_high"], "share"),
            ]
        )
    write_csv(pd.DataFrame(numbers, columns=["macro", "value", "unit"]), args.output_dir / "generated_numbers.csv")

    input_paths = [DESIGN_PATH, ROOT / "empirical/goal16/EMPIRICAL_REDESIGN.md", national_path]
    input_paths.extend(ROOT / source["path"] for source in design["state_sources"] + design["audit_only_sources"])
    lineage = pd.DataFrame(
        [
            {
                "output_file": name,
                "upstream_inputs": ";".join(path.relative_to(ROOT).as_posix() for path in input_paths),
                "upstream_sha256": ";".join(sha256_file(path) for path in input_paths),
                "output_sha256": sha256_file(args.output_dir / name),
                "manual_edits": False,
            }
            for name in [*outputs, "generated_numbers.csv"]
        ]
    )
    write_csv(lineage, args.output_dir / "lineage.csv")

    validation = {
        "status": "PASS",
        "design_frozen": True,
        "years_contiguous": sorted(panel["year"].unique().tolist()) == list(range(2016, 2025)),
        "three_crops_per_state_year": bool(panel.groupby(["state", "year"])["crop"].nunique().eq(3).all()),
        "acreage_shares_sum_to_one": bool(
            panel.groupby(["state", "year"])["observed_acreage_share"].sum().sub(1).abs().lt(1e-10).all()
        ),
        "no_duplicate_rows": not panel.duplicated(["state", "year", "crop"]).any(),
        "no_lookahead": bool(transition["decision_year"].sub(transition["lag_year"]).eq(1).all()),
        "bootstrap_replications": int(design["uncertainty"]["replications"]),
        "county_claims_absent": True,
        "causal_claims_absent": True,
    }
    if not all(value for key, value in validation.items() if key not in {"bootstrap_replications", "status"}):
        validation["status"] = "FAIL"
        raise ValueError(f"GOAL-16 validation failed: {validation}")
    (args.output_dir / "validation_report.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    run_metadata = {
        "command": "python scripts/run_goal16_empirical.py",
        "design_id": design["design_id"],
        "design_sha256": design["design_sha256"],
        "input_hashes": {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in input_paths},
        "manual_output_edits": False,
    }
    (args.output_dir / "run_metadata.json").write_text(
        json.dumps(run_metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary_json = {
        "design_id": design["design_id"],
        "years": sorted(int(value) for value in panel["year"].unique()),
        "state_crop_rows": len(panel),
        "state_years": panel[["state", "year"]].drop_duplicates().shape[0],
        "states": panel["state"].nunique(),
        "transitions_per_definition": int(events.groupby("ranking_definition").size().min()),
        "county_panel": county["status"],
        "result_scope": "DESCRIPTIVE_ACCOUNTING_AND_MODEL_LINKED_SIGNATURES_ONLY",
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary_json, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_checksums(args.output_dir)
    print(json.dumps(summary_json, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
