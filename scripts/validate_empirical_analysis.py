#!/usr/bin/env python3
"""Fail-closed schema, lineage, reconciliation, and claim-boundary audit for Issue 7."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "empirical/src"))

from crop_empirical.empirical_analysis import load_design  # noqa: E402

OUTPUT = ROOT / "empirical/outputs"


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    design = load_design()
    required = {
        "SHA256SUMS.txt", "claim_boundaries.csv", "definition_summary.csv",
        "discordance_detail.csv", "lagged_2024_ranking_rows.csv",
        "lagged_2024_validation.csv", "leave_one_year_out.csv", "national_check.csv",
        "permutation_benchmark.csv", "ranking_rows.csv", "reproducibility.json",
        "run_metadata.json", "sample_flow.csv", "state_crop_panel.csv",
        "state_heterogeneity.csv", "summary.json", "year_heterogeneity.csv",
    }
    require(required.issubset({path.name for path in OUTPUT.glob("*")}), "empirical output package incomplete")
    if failures:
        print("\n".join(f"FAIL: {item}" for item in failures))
        return 1

    checksum_map = {}
    for line in (OUTPUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        checksum_map[name] = digest
    for name in required - {"SHA256SUMS.txt"}:
        require(checksum_map.get(name) == hashlib.sha256((OUTPUT / name).read_bytes()).hexdigest(), f"checksum mismatch: {name}")

    parsed = pd.read_csv(ROOT / "data/processed/nass_state_crop_2022_2024.csv")
    panel = pd.read_csv(ROOT / "data/processed/empirical_state_crop_analysis_panel.csv")
    output_panel = pd.read_csv(OUTPUT / "state_crop_panel.csv")
    detail = pd.read_csv(OUTPUT / "discordance_detail.csv")
    rankings = pd.read_csv(OUTPUT / "ranking_rows.csv")
    definitions = pd.read_csv(OUTPUT / "definition_summary.csv")
    state = pd.read_csv(OUTPUT / "state_heterogeneity.csv")
    year = pd.read_csv(OUTPUT / "year_heterogeneity.csv")
    national = pd.read_csv(OUTPUT / "national_check.csv")
    lagged_rows = pd.read_csv(OUTPUT / "lagged_2024_ranking_rows.csv")
    lagged = pd.read_csv(OUTPUT / "lagged_2024_validation.csv")
    leave_out = pd.read_csv(OUTPUT / "leave_one_year_out.csv")
    permutations = pd.read_csv(OUTPUT / "permutation_benchmark.csv")
    boundaries = pd.read_csv(OUTPUT / "claim_boundaries.csv")
    flow = pd.read_csv(OUTPUT / "sample_flow.csv")
    summary = json.loads((OUTPUT / "summary.json").read_text(encoding="utf-8"))
    metadata = json.loads((OUTPUT / "run_metadata.json").read_text(encoding="utf-8"))
    replay = json.loads((OUTPUT / "reproducibility.json").read_text(encoding="utf-8"))

    require(len(parsed) == 345 and parsed["crop"].nunique() == 3, "parsed NASS cardinality mismatch")
    require(not parsed.duplicated(["state", "year", "crop"]).any(), "duplicate parsed NASS key")
    known = {
        "corn": (90594.0, 179.3), "soybeans": (87050.0, 50.7), "winter_wheat": (33390.0, 51.7),
    }
    us_2024 = parsed.loc[parsed["state"].eq("United States") & parsed["year"].eq(2024)].set_index("crop")
    for crop, (acres, crop_yield) in known.items():
        require(float(us_2024.loc[crop, "planted_acres_1000"]) == acres, f"NASS acreage reconciliation: {crop}")
        require(float(us_2024.loc[crop, "yield_bushels_per_acre"]) == crop_yield, f"NASS yield reconciliation: {crop}")

    require(len(panel) == 231 and panel[["state", "year"]].drop_duplicates().shape[0] == 77, "complete sample mismatch")
    require(panel["state"].nunique() == 26 and set(panel["year"]) == {2022, 2023, 2024}, "sample scope mismatch")
    require(panel.groupby(["state", "year"])["crop"].nunique().eq(3).all(), "incomplete admitted state-year")
    require(not panel.isna().any().any(), "analysis panel contains missing values")
    require(panel["observed_allocation_interpretation"].eq("AGGREGATE_ACREAGE_NOT_MODEL_OPTIMUM").all(), "observed-acreage boundary missing")
    require(panel.equals(output_panel), "processed/output analysis panels differ")

    require(len(detail) == 308 and detail["ranking_definition"].nunique() == 4, "discordance detail mismatch")
    require(len(rankings) == 924, "ranking row cardinality mismatch")
    require(definitions["state_years"].eq(77).all(), "definition summaries do not cover 77 state-years")
    require(len(state) == 104 and len(year) == 12, "heterogeneity summary mismatch")
    require(np.isfinite(detail.select_dtypes(include=["number"]).to_numpy()).all(), "non-finite empirical result")
    require(detail["claim_level"].eq("DESCRIPTIVE_ACCOUNTING_NOT_CAUSAL").all(), "causal boundary missing from detail")

    operating = detail.loc[detail["ranking_definition"].eq("operating_margin")]
    require(int(operating["top_rank_reversal"].sum()) == 63, "operating-margin top reversal reconciliation")
    require(int(operating["strong_reversal"].sum()) == 41, "operating-margin strong reversal reconciliation")
    require(abs(float(operating["pairwise_inversions"].mean()) - 1.7922077922077921) < 1e-12, "mean inversion reconciliation")
    require(len(national) == 9 and not national["rank_reversal"].any(), "national null ranking check mismatch")
    require(len(lagged) == 25 and int(lagged["top_rank_reversal"].sum()) == 22, "lagged 2024 validation mismatch")
    require(len(lagged_rows) == 75 and len(leave_out) == 12, "temporal robustness output mismatch")

    require(len(permutations) == 6, "permutation enumeration incomplete")
    require(abs(permutations["pairwise_inversions"].mean() - 1.5) < 1e-12, "permutation inversion benchmark mismatch")
    require(abs(permutations["top_rank_reversal"].mean() - 2 / 3) < 1e-12, "permutation top benchmark mismatch")
    require(flow.iloc[-1]["rows"] == 231 and flow.iloc[-1]["state_years"] == 77, "sample-flow reconciliation")

    boundary_map = boundaries.set_index("claim_domain")["status"].to_dict()
    for domain in ("observed acreage optimality", "CVaR binding or causality", "copula mechanism", "state realized downside/CVaR"):
        require(boundary_map.get(domain) == "NOT_IDENTIFIED", f"identification boundary missing: {domain}")
    require(summary.get("observed_acreage_is_optimum") is False, "summary treats acreage as optimum")
    require(summary.get("cvar_mechanism_identified") is False, "summary identifies CVaR mechanism")
    require(summary.get("causal_claim_admissible") is False, "summary admits causal claim")
    require(summary.get("design_sha256") == design["design_sha256"], "summary design hash mismatch")

    raw_path = ROOT / "data/raw/usda_nass/crop_production_2024_summary.txt"
    require(metadata.get("nass_snapshot_sha256") == hashlib.sha256(raw_path.read_bytes()).hexdigest(), "raw NASS lineage mismatch")
    require(metadata.get("national_panel_sha256") == hashlib.sha256((ROOT / "data/processed/canonical_crop_year_panel.csv").read_bytes()).hexdigest(), "national panel lineage mismatch")
    require(metadata.get("manual_output_edits") is False, "manual output edit flag")
    require(replay.get("status") == "PASS" and replay.get("files_compared") == 19 and not replay.get("mismatched_files"), "independent empirical replay failure")

    with (ROOT / "evidence_registry/data_source_registry.csv").open(newline="", encoding="utf-8") as handle:
        sources = {row["source_id"]: row for row in csv.DictReader(handle)}
    require(sources["DATA-NASS-CROPAN25"]["sha256"] == hashlib.sha256(raw_path.read_bytes()).hexdigest(), "registry NASS hash mismatch")

    with (ROOT / "evidence_registry/claims.csv").open(newline="", encoding="utf-8") as handle:
        empirical_claims = [row for row in csv.DictReader(handle) if row["claim_id"].startswith("EMP-C")]
    require({row["claim_id"] for row in empirical_claims} == {f"EMP-C{i:02d}" for i in range(1, 9)}, "empirical claim registry incomplete")
    with (ROOT / "evidence_registry/parameter_provenance.csv").open(newline="", encoding="utf-8") as handle:
        empirical_parameters = [row for row in csv.DictReader(handle) if row["parameter_id"].startswith("P-EMP-")]
    require(len(empirical_parameters) == 5, "empirical parameter registry incomplete")
    require(all(row["config_path"] == "empirical/configs/empirical_design.yaml" for row in empirical_parameters), "empirical parameter config mismatch")
    with (ROOT / "evidence_registry/numbers.csv").open(newline="", encoding="utf-8") as handle:
        empirical_numbers = [row for row in csv.DictReader(handle) if row["number_id"].startswith("NUM-EMP-")]
    require({row["number_id"] for row in empirical_numbers} == {f"NUM-EMP-{i:03d}" for i in range(1, 7)}, "empirical number registry incomplete")
    for row in empirical_numbers:
        path = ROOT / row["output_file"]
        require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == row["checksum"], f"empirical number checksum: {row['number_id']}")

    for failure in failures:
        print(f"FAIL: {failure}")
    print(f"empirical_checks={60 - len(failures)}/60 failures={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
