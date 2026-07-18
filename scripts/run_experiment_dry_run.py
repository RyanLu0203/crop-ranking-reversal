#!/usr/bin/env python3
"""Execute three tiny engine smoke tests under the frozen Issue #5 design."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "simulation/src"), str(ROOT / "optimization/src")]

from crop_optimization.cvar_optimizer import solve_cvar_allocation  # noqa: E402
from crop_optimization.optimal_face_audit import audit_pairwise_optimal_face  # noqa: E402
from crop_simulation.experiment_design import expand_design, load_experiment_design  # noqa: E402
from crop_simulation.panel_calibration import (  # noqa: E402
    clayton_theta_from_kendall_tau,
    equicorrelation_from_kendall_tau,
    load_margin_matrix,
    panel_calibration,
)
from crop_simulation.scenario_generation import generate_profit_scenarios  # noqa: E402

OUTPUT_DIR = ROOT / "simulation/dry_run"


def _copula(cell: dict[str, object], n_crops: int):
    tau = float(cell["kendall_tau"])
    family = str(cell["copula_family"])
    if family == "gaussian":
        return "Gaussian", equicorrelation_from_kendall_tau(tau, n_crops)
    if family == "student_t_df4":
        return "Student-t", {"df": 4, "corr": equicorrelation_from_kendall_tau(tau, n_crops)}
    if family == "clayton":
        return "Clayton", clayton_theta_from_kendall_tau(tau)
    raise ValueError(f"unknown copula family: {family}")


def _marginal(cell: dict[str, object], margin_matrix: np.ndarray) -> dict[str, object]:
    family = str(cell["marginal_family"])
    if family == "gaussian":
        return {"type": "normal"}
    if family == "student_t_df5":
        return {"type": "student_t", "df": 5}
    if family == "empirical_resample":
        return {"type": "empirical_resample", "samples": margin_matrix.tolist()}
    raise ValueError(f"unknown marginal family: {family}")


def main() -> int:
    design = load_experiment_design()
    cells = expand_design(design)
    calibration = panel_calibration()
    margin_matrix = load_margin_matrix().to_numpy()
    crop_names = calibration["crop_names"]
    means = np.asarray([calibration["means"][crop] for crop in crop_names])
    stds = np.asarray([calibration["stds"][crop] for crop in crop_names])
    costs = np.asarray([calibration["costs_2024_real"][crop] for crop in crop_names])
    anchors = cells.loc[cells["cell_type"].eq("anchor")]
    dry_pairs = [
        ("gaussian", "gaussian"),
        ("student_t_df4", "student_t_df5"),
        ("clayton", "empirical_resample"),
    ]
    selected = np.concatenate([
        anchors.loc[
            anchors["copula_family"].eq(copula)
            & anchors["marginal_family"].eq(marginal)
        ].head(1).index.to_numpy()
        for copula, marginal in dry_pairs
    ])
    selected = anchors.loc[selected]
    rows: list[dict[str, object]] = []
    for dry_index, (_, cell_series) in enumerate(selected.iterrows()):
        cell = cell_series.to_dict()
        copula_type, copula_param = _copula(cell, len(crop_names))
        marginal = _marginal(cell, margin_matrix)
        seed = int(design["design"]["replication_seeds"][dry_index])
        kwargs = dict(
            means=means,
            stds=stds,
            n_scenarios=int(design["design"]["dry_run_scenarios"]),
            copula_type=copula_type,
            copula_param=copula_param,
            random_seed=seed,
            crop_names=crop_names,
            marginal_model=marginal,
        )
        scenarios, metadata = generate_profit_scenarios(**kwargs)
        repeated, _ = generate_profit_scenarios(**kwargs)
        scenario_hash = hashlib.sha256(scenarios.tobytes()).hexdigest()
        budget = float(cell["budget_to_max_cost_ratio"]) * float(costs.max())
        cap = float(cell["dominant_crop_cap_share"])
        contract = float(cell["contract_minimum_share"])
        rotation = {crop_names[0]: cap} if cap < 1.0 else {}
        contracts = {crop_names[-1]: contract} if contract > 0 else {}
        cvar_limit = 1000.0  # smoke-test feasibility only; explicitly illustrative
        result = solve_cvar_allocation(
            scenarios, costs, 1.0, budget, float(cell["alpha"]), cvar_limit,
            np.zeros(len(crop_names)), np.ones(len(crop_names)), rotation,
            crop_names, contracts,
        )
        face = audit_pairwise_optimal_face(
            scenarios, costs, 1.0, budget, float(cell["alpha"]), cvar_limit,
            np.zeros(len(crop_names)), np.ones(len(crop_names)), crop_names,
            crop_names[0], crop_names[1], rotation_caps=rotation,
            contract_minimums=contracts,
        )
        rows.append({
            "cell_id": cell["cell_id"],
            "copula_family": cell["copula_family"],
            "marginal_family": cell["marginal_family"],
            "seed": seed,
            "scenario_rows": scenarios.shape[0],
            "scenario_columns": scenarios.shape[1],
            "scenario_sha256": scenario_hash,
            "exact_repeat": bool(np.array_equal(scenarios, repeated)),
            "all_finite": bool(np.isfinite(scenarios).all()),
            "solver_status": result.status,
            "kkt_primal_residual": result.diagnostics.get("kkt_primal_residual"),
            "kkt_stationarity_residual": result.diagnostics.get("kkt_stationarity_residual"),
            "optimal_face_status": face.get("status"),
            "reversal_classification": face.get("classification"),
            "manuscript_admissible": "NO",
            "copula_ordering_scope": metadata["ordering_scope"],
        })
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / "design_cells.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    summary = {
        "design_id": design["design_id"],
        "design_sha256": design["design_sha256"],
        "status": "DRY_RUN_ONLY_NOT_A_FORMAL_EXPERIMENT",
        "cells": len(rows),
        "all_exact_repeat": all(bool(row["exact_repeat"]) for row in rows),
        "all_finite": all(bool(row["all_finite"]) for row in rows),
        "all_solvers_optimal": all(row["solver_status"] == "optimal" for row in rows),
        "panel_source": calibration["source_path"],
        "formal_resource_budget": design["resource_budget"],
    }
    (OUTPUT_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["all_exact_repeat"] and summary["all_finite"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
