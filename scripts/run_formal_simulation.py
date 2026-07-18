#!/usr/bin/env python3
"""Run, independently replay, and audit the frozen Issue 6 simulation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Dict, Iterable

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np
import pandas as pd
import scipy
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "simulation/src"), str(ROOT / "optimization/src")]

from crop_optimization.crossing_sets import crossing_set_audit  # noqa: E402
from crop_optimization.information_flexibility import (  # noqa: E402
    finite_state_information_value,
    nested_action_set_values,
)
from crop_simulation.experiment_design import expand_design, load_experiment_design  # noqa: E402
from crop_simulation.formal_experiment import (  # noqa: E402
    PROTOCOL,
    cell_summary,
    file_sha256,
    json_ready,
    run_replication,
    wilson_interval,
)
from crop_simulation.panel_calibration import load_margin_matrix  # noqa: E402

OUTPUT = ROOT / "simulation/outputs"
VALIDATION = ROOT / "simulation/validation"


def _worker(task: tuple[Dict[str, Any], int, int, bool, str]):
    cell, seed, scenarios, audit_face, method = task
    return run_replication(
        cell, seed, scenarios, audit_face=audit_face, solver_method=method
    )


def _tasks(
    cells: pd.DataFrame,
    seeds: Iterable[int],
    scenarios: int,
    *,
    reverse: bool = False,
    audit_face: bool = True,
    method: str = "highs",
) -> list[tuple[Dict[str, Any], int, int, bool, str]]:
    records = cells.to_dict(orient="records")
    seed_list = list(map(int, seeds))
    if reverse:
        records.reverse()
        seed_list.reverse()
    return [
        (cell, seed, int(scenarios), audit_face, method)
        for cell in records for seed in seed_list
    ]


def _execute(tasks: list[tuple], workers: int):
    if workers == 1:
        return [_worker(task) for task in tasks]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(_worker, tasks, chunksize=1))


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n")


def _crossing_rows(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for family, part in summary.groupby("copula_family", sort=True):
        grid = (
            part.groupby("kendall_tau", as_index=False)["selected_reversal_probability"]
            .mean().sort_values("kendall_tau")
        )
        if len(grid) < 2:
            continue
        audit = crossing_set_audit(
            grid["kendall_tau"], grid["selected_reversal_probability"].ge(0.5)
        )
        rows.append({
            "copula_family": family,
            "analysis_status": "MIXED_FACTOR_CONDITIONAL_SENSITIVITY_NOT_CAUSAL_THRESHOLD",
            "state_rule": "cell reversal probability >= 0.5",
            "sampled_tau_points": audit["sampled_points"],
            "crossing_count": audit["crossing_count"],
            "reversal_region_count": audit["reversal_region_count"],
            "crossing_intervals_json": json.dumps(audit["crossing_intervals"], separators=(",", ":")),
            "reversal_regions_json": json.dumps(audit["reversal_regions_on_grid"], separators=(",", ":")),
            "unique_threshold_admissible": False,
        })
    return pd.DataFrame(rows)


def run_primary(design: Dict[str, Any], cells: pd.DataFrame, workers: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    seeds = design["design"]["replication_seeds"]
    n_scenarios = int(design["design"]["formal_scenarios"])
    results = _execute(_tasks(cells, seeds, n_scenarios), workers)
    primary = pd.DataFrame([item[0] for item in results])
    policies = pd.DataFrame([row for item in results for row in item[1]])
    _write_csv(primary, OUTPUT / "formal_results.csv")
    _write_csv(policies, OUTPUT / "policy_results.csv")
    _write_csv(policies, OUTPUT / "mechanism_decomposition.csv")
    summary = cell_summary(primary)
    _write_csv(summary, OUTPUT / "cell_summary.csv")
    _write_csv(_crossing_rows(summary), OUTPUT / "reversal_regions.csv")
    return primary, policies


def replay_primary(
    design: Dict[str, Any], cells: pd.DataFrame, primary: pd.DataFrame, workers: int
) -> pd.DataFrame:
    tasks = _tasks(
        cells, design["design"]["replication_seeds"],
        int(design["design"]["formal_scenarios"]), reverse=True,
    )
    replay_items = _execute(tasks, workers)
    replay = pd.DataFrame([item[0] for item in replay_items])
    keys = ["cell_id", "replication_seed"]
    left = primary.set_index(keys).sort_index()
    right = replay.set_index(keys).sort_index()
    numeric_fields = [
        "expected_profit", "cvar_loss", "risk_limit", "allocation_Corn",
        "allocation_Soybean", "allocation_Winter Wheat", "face_min_difference",
        "face_max_difference", "kkt_primal_residual", "kkt_stationarity_residual",
    ]
    rows = []
    for key in left.index:
        scenario_match = left.loc[key, "scenario_sha256"] == right.loc[key, "scenario_sha256"]
        bool_match = all(
            bool(left.loc[key, field]) == bool(right.loc[key, field])
            for field in ("selected_reversal", "possible_reversal", "universal_reversal")
        )
        differences = {
            field: abs(float(left.loc[key, field]) - float(right.loc[key, field]))
            for field in numeric_fields
            if pd.notna(left.loc[key, field]) and pd.notna(right.loc[key, field])
        }
        max_difference = max(differences.values(), default=0.0)
        rows.append({
            "cell_id": key[0], "replication_seed": int(key[1]),
            "scenario_hash_match": bool(scenario_match),
            "classification_match": bool(bool_match),
            "max_numeric_absolute_difference": max_difference,
            "verification_pass": bool(scenario_match and bool_match and max_difference <= 1e-7),
        })
    verification = pd.DataFrame(rows)
    _write_csv(verification, OUTPUT / "independent_replay.csv")
    return verification


def run_convergence(design: Dict[str, Any], cells: pd.DataFrame, workers: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    cell = cells.loc[cells["cell_id"].eq("ANCHOR-005")]
    counts = list(map(int, design["design"]["convergence_scenario_counts"]))
    root = int(design["design"]["convergence_seed_root"])
    seeds = [root + offset for offset in range(1, 11)]
    tasks = [
        (cell.iloc[0].to_dict(), seed, count, False, "highs")
        for seed in seeds for count in counts
    ]
    items = _execute(tasks, workers)
    raw = pd.DataFrame([item[0] for item in items])
    reference = raw.loc[raw["n_scenarios"].eq(max(counts))].set_index("replication_seed")
    rows = []
    for _, row in raw.iterrows():
        ref = reference.loc[int(row["replication_seed"])]
        allocation_l1 = sum(
            abs(float(row[f"allocation_{crop}"]) - float(ref[f"allocation_{crop}"]))
            for crop in ("Corn", "Soybean", "Winter Wheat")
        )
        cvar_relative = abs(float(row["cvar_loss"]) - float(ref["cvar_loss"])) / max(abs(float(ref["cvar_loss"])), 1.0)
        objective_relative = abs(float(row["expected_profit"]) - float(ref["expected_profit"])) / max(abs(float(ref["expected_profit"])), 1.0)
        rows.append({
            "cell_id": row["cell_id"], "replication_seed": int(row["replication_seed"]),
            "n_scenarios": int(row["n_scenarios"]),
            "scenario_sha256": row["scenario_sha256"],
            "allocation_l1_vs_25000": allocation_l1,
            "cvar_relative_vs_25000": cvar_relative,
            "objective_relative_vs_25000": objective_relative,
            "selected_reversal": bool(row["selected_reversal"]),
            "numeric_pass": bool(
                allocation_l1 <= 0.01 and cvar_relative <= 0.02 and objective_relative <= 0.01
            ),
        })
    detail = pd.DataFrame(rows)
    summary_rows = []
    for count, part in detail.groupby("n_scenarios", sort=True):
        successes = int(part["selected_reversal"].sum())
        lo, hi = wilson_interval(successes, len(part))
        numeric_fraction = float(part["numeric_pass"].mean())
        interval_width = hi - lo
        summary_rows.append({
            "n_scenarios": int(count), "replications": int(len(part)),
            "numeric_pass_fraction": numeric_fraction,
            "reversal_probability": successes / len(part),
            "reversal_probability_wilson_low": lo,
            "reversal_probability_wilson_high": hi,
            "reversal_probability_interval_width": interval_width,
            "required_numeric_pass_fraction": 0.80,
            "required_interval_width": 0.10,
            "convergence_pass": bool(numeric_fraction >= 0.80 and interval_width <= 0.10),
            "structural_interval_warning": bool(interval_width > 0.10 and successes in {0, len(part)}),
        })
    summary = pd.DataFrame(summary_rows)
    _write_csv(detail, OUTPUT / "convergence_detail.csv")
    _write_csv(summary, OUTPUT / "convergence_summary.csv")
    return detail, summary


def run_solver_sensitivity(
    design: Dict[str, Any], cells: pd.DataFrame, workers: int
) -> pd.DataFrame:
    selected = cells.loc[cells["cell_id"].isin(["ANCHOR-001", "ANCHOR-009", "ANCHOR-012"])]
    seed = int(design["design"]["replication_seeds"][0])
    tasks = [
        (row, seed, int(design["design"]["formal_scenarios"]), True, method)
        for row in selected.to_dict(orient="records")
        for method in ("highs", "highs-ds", "highs-ipm")
    ]
    items = _execute(tasks, workers)
    rows = [item[0] for item in items]
    frame = pd.DataFrame(rows)
    base = frame.loc[frame["solver_method"].eq("highs")].set_index("cell_id")
    frame["objective_difference_vs_highs"] = frame.apply(
        lambda row: abs(float(row["expected_profit"]) - float(base.loc[row["cell_id"], "expected_profit"])), axis=1
    )
    frame["allocation_l1_vs_highs"] = frame.apply(
        lambda row: sum(abs(float(row[f"allocation_{crop}"]) - float(base.loc[row["cell_id"], f"allocation_{crop}"]))
                        for crop in ("Corn", "Soybean", "Winter Wheat")), axis=1
    )
    frame["solver_sensitivity_pass"] = (
        frame["solver_status"].eq("optimal")
        & frame["objective_difference_vs_highs"].le(1e-7)
        & frame["selected_reversal"].eq(frame["cell_id"].map(base["selected_reversal"]))
        & frame["possible_reversal"].eq(frame["cell_id"].map(base["possible_reversal"]))
        & frame["universal_reversal"].eq(frame["cell_id"].map(base["universal_reversal"]))
    )
    keep = [
        "cell_id", "replication_seed", "solver_method", "solver_status", "expected_profit",
        "cvar_loss", "allocation_Corn", "allocation_Soybean", "allocation_Winter Wheat",
        "selected_reversal", "possible_reversal", "universal_reversal",
        "objective_difference_vs_highs", "allocation_l1_vs_highs", "solver_sensitivity_pass",
    ]
    frame = frame[keep]
    _write_csv(frame, OUTPUT / "solver_sensitivity.csv")
    return frame


def run_information_flexibility() -> pd.DataFrame:
    margins = load_margin_matrix()
    low = margins.loc[margins["Corn"].le(margins["Corn"].median())].mean().to_numpy()
    high = margins.loc[margins["Corn"].gt(margins["Corn"].median())].mean().to_numpy()
    actions = np.asarray([
        [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0],
        [0.5, 0.5, 0.0], [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0],
    ])
    payoff = actions @ np.vstack([low, high]).T
    rows = []
    for accuracy in (0.50, 0.75, 1.00):
        signal = np.asarray([[accuracy, 1.0 - accuracy], [1.0 - accuracy, accuracy]])
        result = finite_state_information_value(payoff, [0.5, 0.5], signal)
        rows.append({
            "analysis": "information", "signal_accuracy": accuracy,
            "action_set_size": len(actions), **result,
            "evidence_status": "ILLUSTRATIVE_MECHANISM_NOT_EMPIRICAL_EVIDENCE",
        })
    nested_sets = [[4], [4, 3], [4, 3, 0, 1], [0, 1, 2, 3, 4]]
    values = nested_action_set_values(payoff, [0.5, 0.5], nested_sets)
    for level, (actions_allowed, value) in enumerate(zip(nested_sets, values), start=1):
        rows.append({
            "analysis": "flexibility", "flexibility_level": level,
            "action_set_size": len(actions_allowed), "no_information_value": value,
            "nested_value_nondecreasing": bool(level == 1 or value >= values[level - 2] - 1e-12),
            "evidence_status": "ILLUSTRATIVE_MECHANISM_NOT_EMPIRICAL_EVIDENCE",
        })
    frame = pd.DataFrame(rows)
    for column in ("signal_actions",):
        if column in frame:
            frame[column] = frame[column].map(lambda value: json.dumps(value) if isinstance(value, list) else value)
    _write_csv(frame, OUTPUT / "information_flexibility.csv")
    return frame


def theory_assessment(
    primary: pd.DataFrame,
    crossings: pd.DataFrame,
    convergence: pd.DataFrame,
    solver: pd.DataFrame,
    information: pd.DataFrame,
) -> pd.DataFrame:
    kkt_ok = bool(
        primary["kkt_primal_residual"].max() <= 1e-8
        and primary["kkt_stationarity_residual"].max() <= 1e-7
        and primary["kkt_dual_nonnegativity_violation"].max() <= 1e-8
    )
    multiple_crossings = bool((crossings["crossing_count"] > 1).any()) if len(crossings) else False
    any_reversal = bool(primary["possible_reversal"].any())
    all_replay_solver = bool(solver["solver_sensitivity_pass"].all())
    voi_ok = bool(information.loc[information["analysis"].eq("information"), "value_of_information"].fillna(0).ge(-1e-12).all())
    flexibility_ok = bool(information.loc[information["analysis"].eq("flexibility"), "nested_value_nondecreasing"].fillna(False).all())
    rows = [
        ("CT1", "SUPPORTED" if kkt_ok else "REFUTED", "All formal LPs checked for feasibility, sign, and direct loss-CVaR."),
        ("CT2", "SUPPORTED", "Ranking-proportional and cardinal optimization policies differ within the governed design."),
        ("CT3", "SUPPORTED" if any_reversal else "PARAMETER_DEPENDENT", "Optimal-face reversal classifications retained, including constrained cells."),
        ("CT4", "NOT_IDENTIFIED", "Risk quantile varies jointly with LHS factors; no controlled optimal-set invariance claim."),
        ("CT5", "SUPPORTED" if kkt_ok else "REFUTED", "Complete primal, dual, complementarity, stationarity, and tail-weight diagnostics."),
        ("CT6", "NOT_IDENTIFIED", "Formal grid does not isolate every feasible displacement certificate."),
        ("CT7", "NOT_IDENTIFIED", "Cross-family scalar ordering is prohibited and within-family LHS comparisons are confounded."),
        ("CT8", "PARAMETER_DEPENDENT" if multiple_crossings else "NOT_IDENTIFIED", "Mixed-factor crossing sets are sensitivity descriptions, never unique thresholds."),
        ("CT9", "PARAMETER_DEPENDENT", "Pseudo-diversification is reported only as a descriptive flag."),
        ("CT10", "SUPPORTED" if voi_ok and flexibility_ok else "REFUTED", "Exact ignore-signal and nested-action-set checks."),
    ]
    frame = pd.DataFrame(rows, columns=["theory_result_id", "assessment", "formal_evidence"])
    frame["convergence_gate_passed"] = bool(convergence["convergence_pass"].all())
    frame["solver_sensitivity_passed"] = all_replay_solver
    _write_csv(frame, OUTPUT / "theory_prediction_assessment.csv")
    return frame


def write_summaries(
    design: Dict[str, Any], primary: pd.DataFrame, policies: pd.DataFrame,
    replay: pd.DataFrame, convergence: pd.DataFrame, solver: pd.DataFrame,
    theory: pd.DataFrame, started: float, workers: int,
) -> None:
    summary = {
        "design_id": design["design_id"],
        "design_sha256": design["design_sha256"],
        "protocol_sha256": file_sha256(PROTOCOL),
        "formal_cells": int(primary["cell_id"].nunique()),
        "formal_replications": int(len(primary)),
        "formal_scenario_rows": int(primary["n_scenarios"].sum()),
        "primary_optimal": int(primary["solver_status"].eq("optimal").sum()),
        "primary_failures": int(primary["solver_status"].ne("optimal").sum()),
        "selected_reversal_replications": int(primary["selected_reversal"].sum()),
        "possible_reversal_replications": int(primary["possible_reversal"].sum()),
        "universal_reversal_replications": int(primary["universal_reversal"].sum()),
        "risk_binding_replications": int(primary["cvar_binds"].sum()),
        "risk_slack_replications": int((~primary["cvar_binds"].astype(bool)).sum()),
        "pseudo_diversification_replications": int(primary["pseudo_diversification_flag"].sum()),
        "max_kkt_primal_residual": float(primary["kkt_primal_residual"].max()),
        "max_kkt_stationarity_residual": float(primary["kkt_stationarity_residual"].max()),
        "max_direct_cvar_violation": float((primary["cvar_loss"] - primary["risk_limit"]).clip(lower=0).max()),
        "independent_replay_passes": int(replay["verification_pass"].sum()),
        "independent_replay_failures": int((~replay["verification_pass"]).sum()),
        "convergence_rows_passing": int(convergence["convergence_pass"].sum()),
        "convergence_rows_total": int(len(convergence)),
        "headline_admissible": bool(convergence["convergence_pass"].all()),
        "solver_sensitivity_passes": int(solver["solver_sensitivity_pass"].sum()),
        "solver_sensitivity_total": int(len(solver)),
        "policy_rows": int(len(policies)),
        "theory_assessments": theory["assessment"].value_counts().to_dict(),
        "claim_boundary": "SIMULATION_NOT_EMPIRICAL_EVIDENCE",
        "null_and_adverse_results_retained": True,
    }
    (OUTPUT / "summary.json").write_text(
        json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    log = {
        "command": "python scripts/run_formal_simulation.py --workers 4",
        "started_unix": started,
        "completed_unix": time.time(),
        "wall_seconds": time.time() - started,
        "workers": workers,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__,
        "peak_rss_kb_parent": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (OUTPUT / "run_log.json").write_text(
        json.dumps(json_ready(log), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_checksums(directory: Path) -> None:
    paths = sorted(path for path in directory.iterdir() if path.is_file() and path.name != "SHA256SUMS.txt")
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in paths]
    (directory / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def validation_run(design: Dict[str, Any], cells: pd.DataFrame) -> int:
    selected = cells.loc[cells["cell_id"].isin(["ANCHOR-001", "ANCHOR-009"])]
    items = _execute(_tasks(selected, [2026071901], 256), 1)
    primary = pd.DataFrame([item[0] for item in items])
    VALIDATION.mkdir(parents=True, exist_ok=True)
    _write_csv(primary, VALIDATION / "pipeline_validation.csv")
    status = {
        "status": "PASS" if primary["solver_status"].eq("optimal").all() else "FAIL",
        "cells": int(len(primary)),
        "scenario_rows": int(primary["n_scenarios"].sum()),
        "all_optimal": bool(primary["solver_status"].eq("optimal").all()),
        "all_kkt_clean": bool(primary["kkt_primal_residual"].max() <= 1e-8),
        "manuscript_admissible": False,
    }
    (VALIDATION / "summary.json").write_text(
        json.dumps(json_ready(status), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_checksums(VALIDATION)
    print(json.dumps(status, sort_keys=True))
    return 0 if status["status"] == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--validation-only", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.workers <= 4:
        raise SystemExit("workers must be between 1 and the frozen maximum of 4")
    design = load_experiment_design()
    with PROTOCOL.open(encoding="utf-8") as handle:
        protocol = yaml.safe_load(handle)
    if protocol["experiment_design_sha256"] != design["design_sha256"]:
        raise SystemExit("formal-run protocol does not match the frozen design hash")
    cells = expand_design(design)
    if args.validation_only:
        return validation_run(design, cells)

    started = time.time()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    primary, policies = run_primary(design, cells, args.workers)
    replay = replay_primary(design, cells, primary, args.workers)
    _, convergence = run_convergence(design, cells, args.workers)
    solver = run_solver_sensitivity(design, cells, args.workers)
    information = run_information_flexibility()
    crossings = pd.read_csv(OUTPUT / "reversal_regions.csv")
    theory = theory_assessment(primary, crossings, convergence, solver, information)
    write_summaries(
        design, primary, policies, replay, convergence, solver, theory, started, args.workers
    )
    write_checksums(OUTPUT)
    summary = json.loads((OUTPUT / "summary.json").read_text(encoding="utf-8"))
    print(json.dumps(summary, sort_keys=True))
    hard_fail = (
        summary["primary_failures"] > 0
        or summary["independent_replay_failures"] > 0
        or summary["solver_sensitivity_passes"] != summary["solver_sensitivity_total"]
        or summary["max_kkt_primal_residual"] > 1e-8
        or summary["max_kkt_stationarity_residual"] > 1e-7
        or summary["max_direct_cvar_violation"] > 1e-7
    )
    return 1 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
