#!/usr/bin/env python3
"""Fail-closed audit of the generated Issue 6 formal simulation package."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulation/src"))

from crop_simulation.experiment_design import load_experiment_design  # noqa: E402

OUTPUT = ROOT / "simulation/outputs"


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    design = load_experiment_design()
    protocol_path = ROOT / "simulation/configs/formal_run_protocol.yaml"
    protocol = yaml.safe_load(protocol_path.read_text(encoding="utf-8"))
    require(protocol.get("status") == "FROZEN_BEFORE_FORMAL_RESULTS", "run protocol is not frozen")
    require(protocol.get("experiment_design_sha256") == design["design_sha256"], "protocol/design hash mismatch")

    required_files = {
        "formal_results.csv", "policy_results.csv", "mechanism_decomposition.csv",
        "cell_summary.csv", "independent_replay.csv", "convergence_detail.csv",
        "convergence_summary.csv", "solver_sensitivity.csv", "reversal_regions.csv",
        "information_flexibility.csv", "theory_prediction_assessment.csv", "summary.json",
        "run_log.json", "resource_audit.json", "SHA256SUMS.txt",
    }
    require(required_files.issubset({path.name for path in OUTPUT.glob("*")}), "formal output package is incomplete")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    checksum_lines = (OUTPUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    checksum_map = {
        name: digest
        for digest, name in (line.split("  ", 1) for line in checksum_lines if "  " in line)
    }
    for name in required_files - {"SHA256SUMS.txt"}:
        actual = hashlib.sha256((OUTPUT / name).read_bytes()).hexdigest()
        require(checksum_map.get(name) == actual, f"checksum mismatch: {name}")

    primary = pd.read_csv(OUTPUT / "formal_results.csv")
    policies = pd.read_csv(OUTPUT / "policy_results.csv")
    mechanism = pd.read_csv(OUTPUT / "mechanism_decomposition.csv")
    cells = pd.read_csv(OUTPUT / "cell_summary.csv")
    replay = pd.read_csv(OUTPUT / "independent_replay.csv")
    convergence_detail = pd.read_csv(OUTPUT / "convergence_detail.csv")
    convergence = pd.read_csv(OUTPUT / "convergence_summary.csv")
    solver = pd.read_csv(OUTPUT / "solver_sensitivity.csv")
    crossings = pd.read_csv(OUTPUT / "reversal_regions.csv")
    information = pd.read_csv(OUTPUT / "information_flexibility.csv")
    theory = pd.read_csv(OUTPUT / "theory_prediction_assessment.csv")
    summary = json.loads((OUTPUT / "summary.json").read_text(encoding="utf-8"))
    resources = json.loads((OUTPUT / "resource_audit.json").read_text(encoding="utf-8"))
    validation = json.loads((ROOT / "simulation/validation/summary.json").read_text(encoding="utf-8"))

    seeds = set(map(int, design["design"]["replication_seeds"]))
    require(len(primary) == 450 and primary["cell_id"].nunique() == 90, "formal cardinality is not 90 x 5")
    require(not primary.duplicated(["cell_id", "replication_seed"]).any(), "duplicate formal replication")
    require(set(primary["replication_seed"].astype(int)) == seeds, "formal seeds differ from frozen seeds")
    require(primary["n_scenarios"].eq(10000).all(), "formal scenario count differs from 10,000")
    require(primary["design_sha256"].eq(design["design_sha256"]).all(), "formal design hash mismatch")
    require(primary["protocol_sha256"].eq(hashlib.sha256(protocol_path.read_bytes()).hexdigest()).all(), "formal protocol hash mismatch")
    require(primary["solver_status"].eq("optimal").all(), "non-optimal primary solve")
    require(primary["face_status"].eq("solved").all(), "indeterminate optimal-face audit")
    require(primary["kkt_primal_residual"].max() <= 1e-8, "primal residual exceeds tolerance")
    require(primary["kkt_stationarity_residual"].max() <= 1e-7, "stationarity residual exceeds tolerance")
    require(primary["kkt_dual_nonnegativity_violation"].max() <= 1e-8, "dual violation exceeds tolerance")
    require((primary["cvar_loss"] - primary["risk_limit"]).max() <= 1e-7, "direct CVaR violation exceeds tolerance")
    require(primary.loc[primary["risk_dual_eta"].gt(1e-10), "tail_weight_violation"].max() <= 1e-8, "tail weights violate cap")
    require((primary["universal_reversal"] <= primary["possible_reversal"]).all(), "universal reversal implication fails")
    require((primary["possible_reversal"] | ~primary["selected_reversal"]).all(), "selected reversal not possible on face")
    require(primary["copula_ordering_scope"].str.contains("not a cross-family order", case=False).all(), "copula claim boundary missing")

    require(len(policies) == 1800 and policies["policy"].nunique() == 4, "policy comparison is not 450 x 4")
    require(mechanism.equals(policies), "mechanism decomposition is not generated from policy rows")
    require(len(cells) == 90 and cells["replications"].eq(5).all(), "cell summary is incomplete")
    require(len(replay) == 450 and replay["verification_pass"].all(), "independent replay failure")
    require(len(convergence_detail) == 50, "convergence detail is not 5 x 10")
    require(len(convergence) == 5, "convergence summary does not cover five counts")
    require(not convergence["convergence_pass"].all(), "adverse convergence result was hidden")
    require((convergence["reversal_probability_interval_width"] > 0.10).all(), "Wilson-width failure not retained")
    require(len(solver) == 9 and solver["solver_sensitivity_pass"].all(), "solver sensitivity failure")
    require(len(crossings) == 3 and (~crossings["unique_threshold_admissible"]).all(), "unique threshold incorrectly admitted")
    require(theory["theory_result_id"].nunique() == 10, "not every theorem was assessed")
    require(set(theory["assessment"]).issubset({"SUPPORTED", "REFUTED", "PARAMETER_DEPENDENT", "NOT_IDENTIFIED"}), "invalid theory assessment")

    info = information.loc[information["analysis"].eq("information")]
    flex = information.loc[information["analysis"].eq("flexibility")]
    require(info["value_of_information"].fillna(0).ge(-1e-12).all(), "negative value of information")
    require(flex["nested_value_nondecreasing"].fillna(False).all(), "nested flexibility value decreased")
    require(summary.get("headline_admissible") is False, "failed convergence not propagated")
    require(summary.get("independent_replay_failures") == 0, "summary hides replay failures")
    require(summary.get("max_direct_cvar_violation", 1.0) <= 1e-7, "summary direct-CVaR gate fails")
    require(resources.get("status") == "PASS", "resource audit fails")
    require(resources.get("maximum_peak_rss_bytes", 10**12) <= 500_000_000, "resource cap exceeded")
    require(validation.get("status") == "PASS" and validation.get("manuscript_admissible") is False, "validation boundary fails")

    finite_columns = [
        "expected_profit", "cvar_loss", "risk_limit", "allocation_Corn",
        "allocation_Soybean", "allocation_Winter Wheat", "kkt_primal_residual",
        "kkt_stationarity_residual",
    ]
    require(np.isfinite(primary[finite_columns].to_numpy(dtype=float)).all(), "non-finite primary output")

    for failure in failures:
        print(f"FAIL: {failure}")
    print(f"formal_simulation_checks={47 - len(failures)}/47 failures={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
