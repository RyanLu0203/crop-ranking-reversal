#!/usr/bin/env python3
"""Fail-closed acceptance gate for GOAL-12 confirmatory simulations."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "simulation/stage_ii"
OUTPUT = BASE / "outputs"
sys.path[:0] = [str(ROOT / "simulation/src"), str(ROOT / "optimization/src")]

from crop_simulation.stage_ii_confirmatory import load_confirmatory_design  # noqa: E402

REQUIRED_OUTPUTS = {
    "raw_replications.csv", "paired_contrasts.csv", "sequential_stopping.csv",
    "mechanism_summary.csv", "nested_model_path.csv", "block_subset_values.csv",
    "block_attribution.csv", "kkt_pressures.csv", "optimal_faces.csv",
    "risk_frontier.csv", "dependence_evaluation.csv",
    "diversification_metrics.csv", "information_flexibility.csv",
    "scenario_registry.csv", "independent_replay.csv", "solver_sensitivity.csv",
    "figure_source_data.csv", "claim_assessment.csv", "summary.json",
    "resource_audit.json", "run_log.json", "SHA256SUMS.txt",
}
EXPECTED_PRECISION = {
    "E1": False, "E2": True, "E3": False,
    "E4": False, "E5": False, "E6": True,
}
EXPECTED_CLAIMS = {
    "S2-P01", "S2-P02", "S2-C01", "S2-H01", "S2-T01", "S2-P03",
    "S2-P04", "S2-P05", "S2-P06", "S2-H02", "S2-P07", "S2-P08",
    "S2-T02", "S2-T03", "S2-B01",
}
ALLOWED_ASSESSMENTS = {
    "SUPPORTED", "REFUTED", "PARAMETER_DEPENDENT", "NOT_IDENTIFIED",
    "PRECISION_FAILED",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_listing_sha256(path: Path) -> str:
    listing = "".join(
        f"{sha256_file(item)}  {item.relative_to(ROOT).as_posix()}\n"
        for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file())
    )
    return hashlib.sha256(listing.encode("utf-8")).hexdigest()


def load_csv(name: str, errors: list[str]) -> pd.DataFrame:
    path = OUTPUT / name
    try:
        frame = pd.read_csv(path)
    except Exception as exc:  # pragma: no cover - fail-closed reporting path
        errors.append(f"csv_read_failure:{name}:{exc}")
        return pd.DataFrame()
    if frame.empty:
        errors.append(f"empty_output:{name}")
    return frame


def require_columns(
    errors: list[str], name: str, frame: pd.DataFrame, columns: set[str]
) -> None:
    missing = columns - set(frame.columns)
    if missing:
        errors.append(f"missing_columns:{name}:{sorted(missing)}")


def main() -> None:
    errors: list[str] = []
    present = {path.name for path in OUTPUT.iterdir() if path.is_file()} if OUTPUT.is_dir() else set()
    if present != REQUIRED_OUTPUTS:
        errors.append(
            f"output_set_mismatch:missing={sorted(REQUIRED_OUTPUTS-present)}:"
            f"extra={sorted(present-REQUIRED_OUTPUTS)}"
        )
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)

    design = load_confirmatory_design()
    design_hash = design["design_sha256"]
    summary = json.loads((OUTPUT / "summary.json").read_text(encoding="utf-8"))
    resource = json.loads((OUTPUT / "resource_audit.json").read_text(encoding="utf-8"))
    run_log = json.loads((OUTPUT / "run_log.json").read_text(encoding="utf-8"))

    checksum_lines = (OUTPUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    checksum_names: set[str] = set()
    for line in checksum_lines:
        try:
            expected, name = line.split("  ", 1)
        except ValueError:
            errors.append(f"malformed_checksum_line:{line}")
            continue
        checksum_names.add(name)
        path = OUTPUT / name
        if not path.is_file() or sha256_file(path) != expected:
            errors.append(f"checksum_mismatch:{name}")
    expected_checksum_names = REQUIRED_OUTPUTS - {"SHA256SUMS.txt"}
    if checksum_names != expected_checksum_names:
        errors.append("checksum_coverage_mismatch")

    frames = {
        name: load_csv(name, errors)
        for name in sorted(item for item in REQUIRED_OUTPUTS if item.endswith(".csv"))
    }
    raw = frames["raw_replications.csv"]
    contrasts = frames["paired_contrasts.csv"]
    stopping = frames["sequential_stopping.csv"]
    mechanism = frames["mechanism_summary.csv"]
    subsets = frames["block_subset_values.csv"]
    attribution = frames["block_attribution.csv"]
    pressures = frames["kkt_pressures.csv"]
    faces = frames["optimal_faces.csv"]
    dependence = frames["dependence_evaluation.csv"]
    information = frames["information_flexibility.csv"]
    scenarios = frames["scenario_registry.csv"]
    replay = frames["independent_replay.csv"]
    solver = frames["solver_sensitivity.csv"]
    source = frames["figure_source_data.csv"]
    claims = frames["claim_assessment.csv"]

    require_columns(errors, "raw", raw, {
        "design_id", "design_sha256", "experiment_id", "cell_id",
        "replication_seed", "solver_status", "registered_infeasible",
        "infeasibility_certificate_status",
    })
    require_columns(errors, "contrasts", contrasts, {
        "experiment_id", "contrast_id", "metric", "replication_seed",
        "value", "binary_metric",
    })
    require_columns(errors, "stopping", stopping, {
        "experiment_id", "contrast_id", "metric", "check_n", "finite_n",
        "precision_target", "precision_pass",
    })
    require_columns(errors, "faces", faces, {
        "selected_reversal", "possible_reversal", "universal_reversal",
    })

    if summary.get("design_sha256") != design_hash or run_log.get("design_sha256") != design_hash:
        errors.append("design_hash_summary_or_run_log_mismatch")
    for name, frame in frames.items():
        if "design_sha256" in frame and set(frame["design_sha256"].dropna()) != {design_hash}:
            errors.append(f"design_hash_column_mismatch:{name}")
        if "design_id" in frame and set(frame["design_id"].dropna()) != {design["design_id"]}:
            errors.append(f"design_id_column_mismatch:{name}")

    count_fields = {
        "raw_rows": len(raw), "contrast_rows": len(contrasts),
        "scenario_registry_rows": len(scenarios), "face_rows": len(faces),
        "pressure_rows": len(pressures), "subset_rows": len(subsets),
        "attribution_rows": len(attribution),
        "dependence_rows": len(dependence),
        "information_rows": len(information), "figure_source_rows": len(source),
    }
    for field, observed in count_fields.items():
        if int(summary.get(field, -1)) != observed:
            errors.append(f"summary_count_mismatch:{field}")

    actual_n = {key: int(value) for key, value in summary["actual_replications"].items()}
    if set(actual_n) != set(EXPECTED_PRECISION):
        errors.append("experiment_set_mismatch")
    schedule = set(map(int, design["sequential_replication"]["check_schedule"]))
    for experiment, n in actual_n.items():
        expected_seeds = {
            int(design["randomness"]["seed_roots"][experiment]) + index
            for index in range(1, n + 1)
        }
        observed = set(map(int, contrasts.loc[
            contrasts["experiment_id"].eq(experiment), "replication_seed"
        ]))
        if observed != expected_seeds:
            errors.append(f"seed_set_mismatch:{experiment}")
        final_n = set(map(int, mechanism.loc[
            mechanism["experiment_id"].eq(experiment), "check_n"
        ]))
        if final_n != {n} or not set(map(int, stopping.loc[
            stopping["experiment_id"].eq(experiment), "check_n"
        ])).issubset(schedule):
            errors.append(f"stopping_schedule_mismatch:{experiment}")

    precision = {
        experiment: bool(group["precision_pass"].astype(bool).all())
        for experiment, group in mechanism.groupby("experiment_id")
    }
    if precision != EXPECTED_PRECISION or summary.get("experiment_precision") != EXPECTED_PRECISION:
        errors.append(f"precision_outcome_mismatch:{precision}")
    for experiment, passed in EXPECTED_PRECISION.items():
        n = actual_n[experiment]
        if passed and n != min(schedule):
            errors.append(f"unexpected_precision_stop:{experiment}:{n}")
        if not passed and n != max(schedule):
            errors.append(f"failed_precision_did_not_reach_ceiling:{experiment}:{n}")

    registered = raw["registered_infeasible"].fillna(False).astype(bool)
    unexplained = raw.loc[~registered, "solver_status"].ne("optimal")
    if unexplained.any() or int(summary["primary_solver_failures_excluding_registered_infeasible"]):
        errors.append("unexplained_primary_solver_failure")
    if not raw.loc[registered, "solver_status"].eq("infeasible_or_failed").all():
        errors.append("registered_infeasible_status_mismatch")
    allowed_certificates = {
        "DESIGNED_BELOW_MINIMUM_CVAR", "CERTIFIED_MINIMUM_CVAR_EXCEEDS_LIMIT",
    }
    if set(raw.loc[registered, "infeasibility_certificate_status"]) - allowed_certificates:
        errors.append("invalid_infeasibility_certificate")
    certified = raw.loc[
        raw["infeasibility_certificate_status"].eq("CERTIFIED_MINIMUM_CVAR_EXCEEDS_LIMIT")
    ]
    if not certified["infeasibility_margin"].gt(1e-7).all():
        errors.append("nonpositive_infeasibility_margin")
    if int(summary["registered_infeasible_rows"]) != int(registered.sum()):
        errors.append("registered_infeasible_count_mismatch")

    pressure_tolerance = float(design["optimization"]["stationarity_tolerance"])
    max_pressure = float(pressures["stationarity_residual"].abs().max())
    if max_pressure > pressure_tolerance or not np.isclose(
        max_pressure, float(summary["maximum_pressure_stationarity_residual"])
    ):
        errors.append("pressure_ledger_failure")
    if set(pressures.loc[pressures["experiment_id"].eq("E2"), "mechanism_class"]) != {
        "DIRECT_FORCING", "INACTIVE_IN_CELL", "MARGINAL_PRESSURE"
    }:
        errors.append("forcing_pressure_trichotomy_missing")

    selected = faces["selected_reversal"].astype(bool)
    possible = faces["possible_reversal"].astype(bool)
    universal = faces["universal_reversal"].astype(bool)
    if (selected & ~possible).any() or (universal & ~possible).any():
        errors.append("optimal_face_logical_inconsistency")

    subset_counts = subsets.groupby("replication_seed")["subset_id"].nunique()
    if len(subset_counts) != int(design["attribution"]["replications"]) or not subset_counts.eq(16).all():
        errors.append("subset_lattice_incomplete")
    order_rows = attribution.loc[attribution["attribution_type"].eq("ORDER_PATH")]
    order_counts = order_rows.groupby("replication_seed")["order_id"].nunique()
    if not order_counts.eq(24).all():
        errors.append("order_attribution_incomplete")
    shapley = attribution.loc[attribution["attribution_type"].eq("SHAPLEY_ALL_SUBSETS")]
    max_efficiency = float(shapley["efficiency_residual"].abs().max())
    if max_efficiency > 1e-8 or not np.isclose(
        max_efficiency, float(summary["maximum_shapley_efficiency_residual"])
    ):
        errors.append("shapley_efficiency_failure")

    if len(replay) != 12 or not replay["verification_pass"].astype(bool).all():
        errors.append("independent_replay_failure")
    if len(solver) != 9 or not solver["solver_sensitivity_pass"].astype(bool).all():
        errors.append("solver_sensitivity_failure")
    if scenarios.duplicated(
        ["experiment_id", "replication_seed", "stream_id", "scenario_sha256"]
    ).any() or not scenarios["scenario_sha256"].str.fullmatch(r"[0-9a-f]{64}").all():
        errors.append("scenario_registry_failure")

    finite_regret = dependence["feasible_regret"].dropna()
    if not finite_regret.ge(-1e-8).all():
        errors.append("negative_feasible_regret")
    if not set(dependence["reason_code"]).issubset({
        "FEASIBLE", "TRUE_LAW_RISK_VIOLATION", "ASSUMED_POLICY_FAILED"
    }):
        errors.append("invalid_true_law_reason_code")
    if not information["value_of_information"].ge(-1e-10).all():
        errors.append("negative_information_value")
    if not information["action_set_nested"].astype(bool).all():
        errors.append("non_nested_information_action_set")

    if set(claims["theory_result_id"]) != EXPECTED_CLAIMS:
        errors.append("claim_assessment_set_mismatch")
    if set(claims["assessment"]) - ALLOWED_ASSESSMENTS:
        errors.append("invalid_claim_assessment")
    expected_failed_claims = {"S2-H01", "S2-P04", "S2-H02", "S2-P08"}
    observed_failed_claims = set(claims.loc[
        claims["assessment"].eq("PRECISION_FAILED"), "theory_result_id"
    ])
    if observed_failed_claims != expected_failed_claims:
        errors.append("precision_failed_claims_not_retained")
    if not claims["manuscript_promotion_requires_supervisor"].astype(bool).all():
        errors.append("claim_promotion_gate_missing")
    if set(source["evidence_boundary"]) != {"SIMULATION_NOT_EMPIRICAL_EVIDENCE"}:
        errors.append("figure_source_evidence_boundary_failure")

    if resource.get("status") != "PASS" or int(resource["peak_parent_rss_bytes"]) > int(
        resource["peak_parent_rss_limit_bytes"]
    ):
        errors.append("resource_budget_failure")
    if int(resource.get("parallel_workers", -1)) != 1:
        errors.append("parallel_worker_contract_failure")
    if summary.get("historical_numeric_claims_restored") is not False:
        errors.append("historical_claim_restore_flag_failure")
    if summary.get("manuscript_rewritten") is not False or summary.get("figures_generated") is not False:
        errors.append("scope_boundary_failure")

    integrity = {
        "teacher_tex": sha256_file(ROOT / "baselines/teacher_draft/Crop_ranking_reversal_total.tex"),
        "teacher_pdf": sha256_file(ROOT / "baselines/teacher_draft/Crop_ranking_reversal_total.pdf"),
        "manuscript_tree": tree_listing_sha256(ROOT / "manuscript"),
        "panel": sha256_file(ROOT / design["dependencies"]["panel"]),
    }
    expected_integrity = {
        "teacher_tex": "e8885aa89be6a6010f0d3e6f8e40b4b8192a91fc90f6ca4fb16ae9b0aa9dd26c",
        "teacher_pdf": "52ac1b4ef21c8d406fd6d722c877935a24d2cc6ea68520a6f35470ba8b334b44",
        "manuscript_tree": "0068bf01eeb3976c4df7ad0639c920c05c0ca60ce11dc323642e9b26a57cd02e",
        "panel": design["dependencies"]["panel_sha256"],
    }
    if integrity != expected_integrity:
        errors.append(f"baseline_integrity_failure:{integrity}")

    contract_rows = list(csv.DictReader(
        (BASE / "output_contract.csv").open(newline="", encoding="utf-8")
    ))
    if {row["output_file"] for row in contract_rows} - present:
        errors.append("output_contract_missing_artifact")
    acceptance_rows = list(csv.DictReader(
        (BASE / "acceptance_matrix.csv").open(newline="", encoding="utf-8")
    ))
    if len(acceptance_rows) != 18 or any(
        row["status"] not in {"COMPLETE", "ADVERSE_RETAINED"}
        for row in acceptance_rows
    ):
        errors.append("acceptance_matrix_failure")
    if sum(row["status"] == "ADVERSE_RETAINED" for row in acceptance_rows) != 4:
        errors.append("adverse_acceptance_count_mismatch")
    deviation_path = BASE / "execution_deviation_log.md"
    if not deviation_path.is_file():
        errors.append("missing_execution_deviation_log")
    else:
        deviation = deviation_path.read_text(encoding="utf-8")
        for token in (
            "16625.404638975073", "1.8189894035458565e-11",
            "14 certified E4/E5", "No result", "identical frozen design",
        ):
            if token not in deviation:
                errors.append(f"execution_deviation_token_missing:{token}")

    print(
        f"design={design['design_id']} raw={len(raw)} contrasts={len(contrasts)} "
        f"scenarios={len(scenarios)} registered_infeasible={int(registered.sum())} "
        f"precision_pass={sum(precision.values())}/6 replay={int(replay['verification_pass'].sum())}/12 "
        f"solver={int(solver['solver_sensitivity_pass'].sum())}/9 failures={len(errors)}"
    )
    for error in errors:
        print(error)
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
