#!/usr/bin/env python3
"""Fail-closed GOAL-15 design, result, lineage and identification validator."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "empirical/src"))

from crop_empirical.stage_ii_analysis import load_stage_ii_design  # noqa: E402


OUTPUT = ROOT / "empirical/stage_ii/outputs"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    design = load_stage_ii_design()
    required = {
        "SHA256SUMS.txt", "aggregation_summary.csv", "claim_boundaries.csv",
        "definition_agreement.csv", "inertia_association.csv",
        "inversion_intensity_summary.csv", "leave_one_state_out.csv", "lineage.csv",
        "national_definition_detail.csv", "observed_model_unidentified.csv",
        "rank_transition_events.csv", "reproducibility.json", "run_metadata.json",
        "state_heterogeneity.csv", "summary.json", "transition_panel.csv",
        "transition_summary.csv", "year_heterogeneity.csv", "main_results_table.csv",
        "robustness_table.csv",
    }
    present = {path.name for path in OUTPUT.iterdir() if path.is_file()}
    require(required.issubset(present), "Stage II empirical output package incomplete")
    if errors:
        print(json.dumps({"passed": False, "errors": errors}, indent=2))
        return 1

    checksums = {}
    for line in (OUTPUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        checksums[name] = digest
    for name in required - {"SHA256SUMS.txt"}:
        require(checksums.get(name) == sha(OUTPUT / name), f"checksum mismatch: {name}")

    panel = pd.read_csv(ROOT / design["admitted_inputs"]["state_crop_panel"])
    detail = pd.read_csv(ROOT / "empirical/outputs/discordance_detail.csv")
    transition = pd.read_csv(OUTPUT / "transition_panel.csv")
    events = pd.read_csv(OUTPUT / "rank_transition_events.csv")
    inversion = pd.read_csv(OUTPUT / "inversion_intensity_summary.csv")
    transition_summary = pd.read_csv(OUTPUT / "transition_summary.csv")
    inertia = pd.read_csv(OUTPUT / "inertia_association.csv")
    agreement = pd.read_csv(OUTPUT / "definition_agreement.csv")
    state = pd.read_csv(OUTPUT / "state_heterogeneity.csv")
    year = pd.read_csv(OUTPUT / "year_heterogeneity.csv")
    holdout = pd.read_csv(OUTPUT / "leave_one_state_out.csv")
    national = pd.read_csv(OUTPUT / "national_definition_detail.csv")
    aggregation = pd.read_csv(OUTPUT / "aggregation_summary.csv")
    layers = pd.read_csv(OUTPUT / "observed_model_unidentified.csv")
    boundaries = pd.read_csv(OUTPUT / "claim_boundaries.csv")
    main_table = pd.read_csv(OUTPUT / "main_results_table.csv")
    robustness_table = pd.read_csv(OUTPUT / "robustness_table.csv")
    lineage = pd.read_csv(OUTPUT / "lineage.csv")
    summary = json.loads((OUTPUT / "summary.json").read_text(encoding="utf-8"))
    metadata = json.loads((OUTPUT / "run_metadata.json").read_text(encoding="utf-8"))
    replay = json.loads((OUTPUT / "reproducibility.json").read_text(encoding="utf-8"))

    definitions = {"relative_yield", "standardized_revenue", "operating_margin", "total_cost_margin"}
    require(len(panel) == 231 and panel[["state", "year"]].drop_duplicates().shape[0] == 77,
            "admitted panel cardinality changed")
    require(len(transition) == 612 and len(events) == 204, "transition cardinality mismatch")
    require(set(transition["ranking_definition"]) == definitions, "transition definitions incomplete")
    require(transition["decision_year"].sub(transition["lag_year"]).eq(1).all(), "lag timing mismatch")
    require(transition["timing_status"].eq("LAGGED_SCORE_PRECEDES_DECISION_YEAR_ACREAGE").all(),
            "transition timing boundary missing")
    zero_sum = transition.groupby(["ranking_definition", "state", "decision_year"])["acreage_share_change"].sum()
    require(np.allclose(zero_sum, 0, atol=1e-12), "acreage-share transitions do not sum to zero")
    require(events.groupby("ranking_definition").size().eq(51).all(), "rank-transition event counts mismatch")
    require(events["lagged_inversion_intensity"].between(0, 1).all(), "invalid inversion intensity")

    require(len(inversion) == 12 and set(inversion["metric"]) == {
        "inversion_intensity", "top_rank_reversal_rate", "strong_reversal_rate"
    }, "inversion summary family incomplete")
    require(len(transition_summary) == 20 and len(inertia) == 20, "transition result family incomplete")
    for frame, label in [(inversion, "inversion"), (transition_summary, "transition"), (inertia, "inertia")]:
        require(frame["bootstrap_replications"].eq(5000).all(), f"{label} bootstrap count mismatch")
        require((frame["ci_low"] <= frame["estimate"]).all() and (frame["estimate"] <= frame["ci_high"]).all(),
                f"{label} interval does not contain estimate")
        require(np.isfinite(frame.select_dtypes(include=["number"]).to_numpy()).all(), f"{label} non-finite output")
    lag_contrast = transition_summary.loc[transition_summary["metric"].eq("lagged_top_minus_other_share_change")]
    require(((lag_contrast["ci_low"] <= 0) & (lag_contrast["ci_high"] >= 0)).all(),
            "registered lagged transition null was not retained")
    require(inertia["proxy_status"].eq("PRIOR_ACREAGE_INERTIA_PROXY_NOT_OPERATIONAL_CONSTRAINT").all(),
            "inertia proxy mislabeled as constraint")

    require(len(agreement) == 6 and agreement["state_years"].eq(77).all(), "definition agreement incomplete")
    require(len(state) == 104 and len(year) == 12 and len(holdout) == 104,
            "geographic/temporal robustness family incomplete")
    require(state["claim_level"].eq("DESCRIPTIVE_STATE_HETEROGENEITY_NO_STATE_RANKING").all(),
            "state precision boundary missing")
    require(len(national) == 12 and len(aggregation) == 4, "national aggregation family incomplete")
    require(len(main_table) == 24 and len(robustness_table) == 12, "empirical result tables incomplete")
    relative = aggregation.loc[aggregation["ranking_definition"].eq("relative_yield")].iloc[0]
    require(relative["informative_years"] == 0 and relative["national_pairwise_ties"] == 9,
            "national relative-yield tie boundary changed")
    require(aggregation.loc[aggregation["ranking_definition"].eq("operating_margin"),
                            "national_top_reversal_rate"].iloc[0] == 0,
            "national operating-margin null changed")

    layer_map = layers.set_index("construct")["evidence_layer"].to_dict()
    require(layer_map.get("state planted acreage") == "DIRECTLY_OBSERVED", "observed layer missing")
    require(layer_map.get("E2 allocations and KKT pressures") == "MODEL_GENERATED", "model layer missing")
    require(layer_map.get("private budgets, rotations and contracts") == "UNIDENTIFIED", "latent layer missing")
    boundary_map = boundaries.set_index("claim_domain")["status"].to_dict()
    for domain in ["county heterogeneity", "private operational constraints", "observed acreage optimality",
                   "CVaR preference or binding", "copula mechanism or causality", "welfare effect"]:
        require(boundary_map.get(domain) == "NOT_IDENTIFIED", f"identification boundary missing: {domain}")

    prediction = pd.read_csv(ROOT / "empirical/stage_ii/prediction_registry.csv")
    require(set(prediction["prediction_id"]) == {
        "EMP2-P01", "EMP2-P02", "EMP2-P03", "EMP2-P04", "EMP2-N01", "EMP2-N02", "EMP2-N03", "EMP2-N04"
    }, "prediction registry incomplete")
    feasibility = pd.read_csv(ROOT / "empirical/stage_ii/data_feasibility.csv")
    require(feasibility.loc[feasibility["data_layer"].eq("county acreage and yield"), "status"].iloc[0] == "NOT_ADMITTED",
            "county data boundary missing")
    require(feasibility.loc[feasibility["data_layer"].eq("private operational constraints"), "status"].iloc[0] == "UNIDENTIFIED",
            "private constraint boundary missing")
    claim_registry = pd.read_csv(ROOT / "evidence_registry/claims.csv")
    stage2_claims = claim_registry.loc[claim_registry["claim_id"].str.startswith("S2EMP-")]
    require(set(stage2_claims["claim_id"]) == {f"S2EMP-C{i:02d}" for i in range(1, 8)},
            "Stage II empirical claim registry incomplete")
    require(stage2_claims["manuscript_admissible"].eq("YES").all(),
            "authorized empirical claims not marked admissible")
    number_registry = pd.read_csv(ROOT / "evidence_registry/numbers.csv")
    stage2_numbers = number_registry.loc[number_registry["number_id"].str.startswith("NUM-EMP-S2-")]
    require(set(stage2_numbers["number_id"]) == {f"NUM-EMP-S2-{i:03d}" for i in range(1, 6)},
            "Stage II empirical number registry incomplete")
    for _, row in stage2_numbers.iterrows():
        require(sha(ROOT / row.output_file) == row.checksum, f"number registry checksum: {row.number_id}")

    require(set(lineage["output_file"]) == {
        "transition_panel.csv", "rank_transition_events.csv", "inversion_intensity_summary.csv",
        "transition_summary.csv", "definition_agreement.csv", "state_heterogeneity.csv",
        "year_heterogeneity.csv", "leave_one_state_out.csv", "inertia_association.csv",
        "national_definition_detail.csv", "aggregation_summary.csv", "observed_model_unidentified.csv",
        "claim_boundaries.csv", "main_results_table.csv", "robustness_table.csv",
    }, "lineage inventory incomplete")
    for _, row in lineage.iterrows():
        require(sha(OUTPUT / row.output_file) == row.output_sha256, f"lineage output hash: {row.output_file}")
        for upstream, expected in zip(row.upstream_inputs.split(";"), row.upstream_sha256.split(";")):
            require(sha(ROOT / upstream) == expected, f"lineage upstream hash: {upstream}")
    require(metadata["design_sha256"] == design["design_sha256"] and metadata["manual_output_edits"] is False,
            "run metadata mismatch")
    require(replay == {"comparison": "two isolated admitted-panel-to-output executions",
                       "filename_sets_match": True, "files_compared": 19,
                       "mismatched_files": [], "status": "PASS"}, "isolated replay mismatch")
    for key in ["county_analysis_admissible", "private_constraint_identified", "observed_acreage_is_optimum",
                "cvar_identified", "copula_causality_identified", "welfare_identified"]:
        require(summary.get(key) is False, f"summary identification boundary: {key}")

    report = {"validator": "stage_ii_empirical", "passed": not errors,
              "checks": 87, "errors": errors}
    (OUTPUT / "validation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
