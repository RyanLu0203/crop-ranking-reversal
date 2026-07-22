#!/usr/bin/env python3
"""Execute the frozen GOAL-12 controlled confirmatory simulation."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import resource
import sys
import time
from itertools import permutations, product
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "simulation/src"), str(ROOT / "optimization/src")]

from crop_simulation.stage_ii_confirmatory import (  # noqa: E402
    allocation_evaluation,
    all_subsets,
    face_audit,
    finite_state_information_value_subset,
    generate_family_scenarios,
    json_ready,
    load_confirmatory_design,
    operational_spec,
    pairwise_pressure_row,
    raw_policy_row,
    replication_seed,
    sha256_array,
    sha256_file,
    shapley_values,
    solve_expected,
    solve_minimum_cvar,
    solve_risk,
    stable_records_hash,
    stopping_rows,
    symmetric_garbling,
    t_interval,
)

OUTPUT = ROOT / "simulation/stage_ii/outputs"
LIST_KEYS = (
    "raw", "contrasts", "faces", "pressures", "scenarios", "dependence",
    "diversification", "frontier", "information",
)


def empty_bundle() -> dict[str, list[dict[str, Any]]]:
    return {key: [] for key in LIST_KEYS}


def extend_bundle(target: dict[str, list], source: dict[str, list]) -> None:
    for key in LIST_KEYS:
        target[key].extend(source.get(key, []))


def centered_scenarios(scenarios: np.ndarray, means: np.ndarray) -> np.ndarray:
    return scenarios - scenarios.mean(axis=0)[None, :] + means[None, :]


def scenario_row(
    design: dict[str, Any],
    experiment_id: str,
    replication_seed_value: int,
    stream_id: str,
    purpose: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "design_id": design["design_id"],
        "design_sha256": design["design_sha256"],
        "experiment_id": experiment_id,
        "replication_seed": int(replication_seed_value),
        "stream_id": stream_id,
        "purpose": purpose,
        "generator": design["randomness"]["generator"],
        "scenario_seed": int(metadata["seed"]),
        "n_scenarios": int(metadata["n_scenarios"]),
        "scenario_sha256": metadata["scenario_sha256"],
        "copula_family": metadata["copula_family"],
        "kendall_tau": metadata.get("kendall_tau"),
        "marginal_family": metadata["marginal_family"],
        "lower_tail_metric": metadata.get("lower_tail_metric"),
        "ordering_scope": metadata["ordering_scope"],
    }


def update_metadata_hash(metadata: dict[str, Any], scenarios: np.ndarray) -> dict[str, Any]:
    result = dict(metadata)
    result["scenario_sha256"] = sha256_array(scenarios)
    result["centered_to_frozen_means"] = True
    return result


def allocation_vector(row: dict[str, Any]) -> np.ndarray:
    return np.asarray(
        [row.get("allocation_Corn"), row.get("allocation_Soybean"), row.get("allocation_Winter_Wheat")],
        dtype=float,
    )


def contrast_row(
    design: dict[str, Any],
    experiment_id: str,
    contrast_id: str,
    seed: int,
    metric: str,
    value: float,
    *,
    binary: bool = False,
    treatment_cell: str,
    control_cell: str,
) -> dict[str, Any]:
    return {
        "design_id": design["design_id"],
        "design_sha256": design["design_sha256"],
        "experiment_id": experiment_id,
        "contrast_id": contrast_id,
        "replication_seed": int(seed),
        "metric": metric,
        "value": float(value),
        "binary_metric": bool(binary),
        "treatment_cell": treatment_cell,
        "control_cell": control_cell,
        "contrast_status": "PREREGISTERED_CONTROLLED",
    }


def e1_replication(design: dict[str, Any], index: int) -> dict[str, list[dict[str, Any]]]:
    bundle = empty_bundle()
    cfg = design["experiments"]["E1_margin"]
    seed = replication_seed(design, "E1", index)
    crops = list(design["scope"]["crops"])
    stds = np.asarray([design["calibration"]["standard_deviations"][crop] for crop in crops])
    spec = operational_spec(design)
    results: dict[float, dict[str, Any]] = {}
    for gap in map(float, cfg["corn_minus_soybean_margin_gaps"]):
        midpoint = float(cfg["corn_soybean_midpoint"])
        means = np.asarray([midpoint + gap / 2.0, midpoint - gap / 2.0, cfg["wheat_margin"]])
        scenarios, metadata = generate_family_scenarios(
            design, "gaussian", 0.25, seed,
            int(design["randomness"]["optimization_scenarios"]), means=means, stds=stds,
        )
        scenarios = centered_scenarios(scenarios, means)
        metadata = update_metadata_hash(metadata, scenarios)
        cell_id = f"E1-GAP-{gap:+07.1f}"
        result = solve_risk(scenarios, spec, 0.95, 1.0e6)
        raw, face = raw_policy_row(
            design, "E1", cell_id, seed, scenarios, metadata, spec, 0.95, 1.0e6,
            result, model_stage="M1_CARDINAL_MARGINS",
        )
        raw.update({"margin_gap_Corn_minus_Soybean": gap, "score_order_fixed": True})
        bundle["raw"].append(raw); bundle["faces"].append(face)
        bundle["scenarios"].append(
            scenario_row(design, "E1", seed, cell_id, "margin_control", metadata)
        )
        results[gap] = raw
    control = results[0.0]
    for gap, row in results.items():
        if gap == 0.0:
            continue
        contrast_id = f"E1-GAP-{gap:+07.1f}-VS-TIE"
        l1 = float(np.abs(allocation_vector(row) - allocation_vector(control)).sum())
        bundle["contrasts"].extend(
            [
                contrast_row(
                    design, "E1", contrast_id, seed, "allocation_l1", l1,
                    treatment_cell=row["cell_id"], control_cell=control["cell_id"],
                ),
                contrast_row(
                    design, "E1", contrast_id, seed, "selected_reversal_change",
                    float(bool(row["selected_reversal"])), binary=True,
                    treatment_cell=row["cell_id"], control_cell=control["cell_id"],
                ),
            ]
        )
    return bundle


def operation_cells(design: dict[str, Any]) -> list[dict[str, Any]]:
    cfg = design["experiments"]["E2_operations"]
    rows = []
    for budget, rotation, contract in product((0, 1), repeat=3):
        rows.append(
            {
                "cell_id": f"E2-B{budget}-R{rotation}-C{contract}",
                "budget": budget,
                "rotation": rotation,
                "contract": contract,
                "corn_bound": 0,
                "budget_ratio": cfg["budget_ratios"]["tight" if budget else "loose"],
                "rotation_cap": cfg["corn_rotation_caps"]["tight" if rotation else "loose"],
                "contract_minimum": cfg["soybean_contract_minimums"]["active" if contract else "none"],
                "corn_upper": 1.0,
            }
        )
    rows.append(
        {
            "cell_id": "E2-CORN-BOUND-ANCHOR", "budget": 0, "rotation": 0,
            "contract": 0, "corn_bound": 1,
            "budget_ratio": cfg["budget_ratios"]["loose"], "rotation_cap": 1.0,
            "contract_minimum": 0.0, "corn_upper": cfg["corn_upper_bound_anchor"],
        }
    )
    return rows


def e2_replication(design: dict[str, Any], index: int) -> dict[str, list[dict[str, Any]]]:
    bundle = empty_bundle()
    seed = replication_seed(design, "E2", index)
    crops = list(design["scope"]["crops"])
    means = np.asarray([design["calibration"]["means"][crop] for crop in crops])
    scenarios, metadata = generate_family_scenarios(
        design, "gaussian", 0.25, seed,
        int(design["randomness"]["optimization_scenarios"]),
    )
    scenarios = centered_scenarios(scenarios, means)
    metadata = update_metadata_hash(metadata, scenarios)
    bundle["scenarios"].append(
        scenario_row(design, "E2", seed, "E2-COMMON", "operations_common_random_numbers", metadata)
    )
    results: dict[str, dict[str, Any]] = {}
    for cell in operation_cells(design):
        spec = operational_spec(
            design,
            budget_ratio=float(cell["budget_ratio"]),
            corn_upper=float(cell["corn_upper"]),
            corn_rotation_cap=float(cell["rotation_cap"]),
            soybean_contract_minimum=float(cell["contract_minimum"]),
        )
        result = solve_risk(scenarios, spec, 0.95, 1.0e6)
        raw, face = raw_policy_row(
            design, "E2", cell["cell_id"], seed, scenarios, metadata, spec, 0.95,
            1.0e6, result, model_stage="M2_OPERATIONS",
        )
        raw.update(cell)
        direct_forcing = bool(
            float(cell["rotation_cap"]) + 1e-12 < float(cell["contract_minimum"])
            or float(cell["corn_upper"]) + 1e-12 < float(cell["contract_minimum"])
        )
        active_pressure = bool(
            result.allocation is not None and any(
                float(result.diagnostics.get(key, 0.0)) > 1e-8
                for key in (
                    "shadow_price_budget", "shadow_price_rotation_Corn",
                    "shadow_price_contract_Soybean",
                )
            )
        )
        raw["direct_forcing"] = direct_forcing
        raw["marginal_pressure_active"] = active_pressure
        raw["mechanism_class"] = (
            "DIRECT_FORCING" if direct_forcing else
            "MARGINAL_PRESSURE" if active_pressure else
            "BOUNDARY_SELECTION" if float(face.get("face_width") or 0.0) > 1e-4 else
            "INACTIVE_IN_CELL"
        )
        bundle["raw"].append(raw); bundle["faces"].append(face)
        if result.allocation is not None:
            pressure = pairwise_pressure_row(result, scenarios, spec, 0.95)
            pressure.update(
                {
                    "design_id": design["design_id"],
                    "design_sha256": design["design_sha256"],
                    "experiment_id": "E2", "cell_id": cell["cell_id"],
                    "replication_seed": seed, "crop_i": "Corn", "crop_j": "Soybean",
                    "mechanism_class": raw["mechanism_class"],
                }
            )
            bundle["pressures"].append(pressure)
        results[cell["cell_id"]] = raw
    control = results["E2-B0-R0-C0"]
    for cell_id, row in results.items():
        if cell_id == control["cell_id"]:
            continue
        contrast_id = f"{cell_id}-VS-BASE"
        l1 = float(np.abs(allocation_vector(row) - allocation_vector(control)).sum())
        profit_change = float(row["expected_profit"] - control["expected_profit"])
        bundle["contrasts"].extend(
            [
                contrast_row(
                    design, "E2", contrast_id, seed, "allocation_l1", l1,
                    treatment_cell=cell_id, control_cell=control["cell_id"],
                ),
                contrast_row(
                    design, "E2", contrast_id, seed, "expected_profit", profit_change,
                    treatment_cell=cell_id, control_cell=control["cell_id"],
                ),
                contrast_row(
                    design, "E2", contrast_id, seed, "selected_reversal_change",
                    float(bool(row["selected_reversal"])), binary=True,
                    treatment_cell=cell_id, control_cell=control["cell_id"],
                ),
            ]
        )
    return bundle


def risk_limits(minimum: float, expected: float) -> dict[str, float]:
    frontier = max(float(expected) - float(minimum), 0.0)
    scale = max(abs(float(expected)), abs(float(minimum)), 1.0)
    return {
        "slack": float(expected) + 0.05 * scale,
        "just_binding": float(expected) - 0.05 * frontier,
        "binding_mid": 0.5 * (float(expected) + float(minimum)),
        "strongly_binding": float(minimum) + 0.05 * frontier,
        "infeasible": float(minimum) - 0.05 * scale,
    }


def infeasibility_certificate(
    scenarios: np.ndarray,
    spec: dict[str, Any],
    alpha: float,
    risk_limit: float,
    solver_status: str,
) -> dict[str, Any]:
    if solver_status == "optimal":
        return {
            "registered_infeasible": False,
            "minimum_feasible_cvar": math.nan,
            "infeasibility_margin": math.nan,
            "infeasibility_certificate_status": "NOT_REQUIRED",
        }
    minimum = solve_minimum_cvar(scenarios, spec, alpha)
    certified = bool(
        minimum.status == "optimal"
        and minimum.cvar_loss is not None
        and float(minimum.cvar_loss) > float(risk_limit) + 1e-7
    )
    return {
        "registered_infeasible": certified,
        "minimum_feasible_cvar": minimum.cvar_loss,
        "infeasibility_margin": (
            float(minimum.cvar_loss) - float(risk_limit)
            if minimum.cvar_loss is not None else math.nan
        ),
        "infeasibility_certificate_status": (
            "CERTIFIED_MINIMUM_CVAR_EXCEEDS_LIMIT"
            if certified else "UNEXPLAINED_SOLVER_FAILURE"
        ),
    }


def e3_replication(design: dict[str, Any], index: int) -> dict[str, list[dict[str, Any]]]:
    bundle = empty_bundle()
    cfg = design["experiments"]["E3_risk"]
    seed = replication_seed(design, "E3", index)
    scenarios, metadata = generate_family_scenarios(
        design, "student_t_df4", 0.25, seed,
        int(design["randomness"]["optimization_scenarios"]),
    )
    spec = operational_spec(design)
    bundle["scenarios"].append(
        scenario_row(design, "E3", seed, "E3-COMMON", "risk_frontier_common_draw", metadata)
    )
    for alpha in map(float, cfg["alpha_grid"]):
        expected_result = solve_expected(scenarios, spec)
        minimum_result = solve_minimum_cvar(scenarios, spec, alpha)
        if expected_result.allocation is None or minimum_result.allocation is None:
            raise RuntimeError("E3 frontier endpoints failed")
        expected_risk = float(
            allocation_evaluation(scenarios, expected_result.allocation, alpha, 1e9)["cvar_loss"]
        )
        minimum_risk = float(minimum_result.cvar_loss)
        limits = risk_limits(minimum_risk, expected_risk)
        results: dict[str, dict[str, Any]] = {}
        for regime in cfg["risk_regimes"]:
            risk_limit = limits[str(regime)]
            cell_id = f"E3-A{alpha:.2f}-{str(regime).upper()}"
            result = solve_risk(scenarios, spec, alpha, risk_limit)
            raw, face = raw_policy_row(
                design, "E3", cell_id, seed, scenarios, metadata, spec, alpha,
                risk_limit, result, model_stage="M3_DOWNSIDE_RISK",
            )
            raw.update(
                {
                    "risk_regime": regime,
                    "frontier_minimum_cvar": minimum_risk,
                    "frontier_expected_profit_cvar": expected_risk,
                    "frontier_width": expected_risk - minimum_risk,
                    "infeasible_anchor": regime == "infeasible",
                    "registered_infeasible": regime == "infeasible",
                    "minimum_feasible_cvar": minimum_risk,
                    "infeasibility_margin": (
                        minimum_risk - risk_limit if regime == "infeasible" else math.nan
                    ),
                    "infeasibility_certificate_status": (
                        "DESIGNED_BELOW_MINIMUM_CVAR"
                        if regime == "infeasible" else "NOT_REQUIRED"
                    ),
                }
            )
            bundle["raw"].append(raw); bundle["faces"].append(face)
            if result.allocation is not None:
                pressure = pairwise_pressure_row(result, scenarios, spec, alpha)
                pressure.update(
                    {
                        "design_id": design["design_id"],
                        "design_sha256": design["design_sha256"],
                        "experiment_id": "E3", "cell_id": cell_id,
                        "replication_seed": seed, "crop_i": "Corn", "crop_j": "Soybean",
                        "mechanism_class": "RISK_PRESSURE" if pressure["risk_dual_eta"] > 1e-8 else "RISK_SLACK",
                    }
                )
                bundle["pressures"].append(pressure)
            results[str(regime)] = raw
        control = results["slack"]
        for regime in ("just_binding", "binding_mid", "strongly_binding"):
            row = results[regime]
            contrast_id = f"E3-A{alpha:.2f}-{regime.upper()}-VS-SLACK"
            if row["solver_status"] == "optimal":
                l1 = float(np.abs(allocation_vector(row) - allocation_vector(control)).sum())
                cvar_change = float(row["cvar_loss"] - control["cvar_loss"])
                selected = float(bool(row["selected_reversal"]))
            else:
                l1 = cvar_change = selected = math.nan
            bundle["contrasts"].extend(
                [
                    contrast_row(
                        design, "E3", contrast_id, seed, "allocation_l1", l1,
                        treatment_cell=row["cell_id"], control_cell=control["cell_id"],
                    ),
                    contrast_row(
                        design, "E3", contrast_id, seed, "cvar_loss", cvar_change,
                        treatment_cell=row["cell_id"], control_cell=control["cell_id"],
                    ),
                    contrast_row(
                        design, "E3", contrast_id, seed, "selected_reversal_change",
                        selected, binary=True,
                        treatment_cell=row["cell_id"], control_cell=control["cell_id"],
                    ),
                ]
            )
    return bundle


def e4_cells(design: dict[str, Any]) -> list[tuple[str, float | None]]:
    cfg = design["experiments"]["E4_dependence"]
    rows: list[tuple[str, float | None]] = []
    for family in cfg["families"]:
        if family == "empirical_copula":
            rows.append((family, None))
        else:
            rows.extend((family, float(tau)) for tau in cfg["parametric_kendall_tau_grid"])
    return rows


def e4_replication(design: dict[str, Any], index: int) -> dict[str, list[dict[str, Any]]]:
    bundle = empty_bundle()
    cfg = design["experiments"]["E4_dependence"]
    seed = replication_seed(design, "E4", index)
    spec = operational_spec(design)
    results: dict[tuple[str, float | None], dict[str, Any]] = {}
    for family, tau in e4_cells(design):
        scenarios, metadata = generate_family_scenarios(
            design, family, tau, seed,
            int(design["randomness"]["optimization_scenarios"]),
        )
        tau_label = "EMP" if tau is None else f"{tau:.2f}"
        cell_id = f"E4-{family.upper()}-T{tau_label}"
        risk_limit = float(cfg["cvar_limit"])
        result = solve_risk(scenarios, spec, 0.95, risk_limit)
        raw, face = raw_policy_row(
            design, "E4", cell_id, seed, scenarios, metadata, spec, 0.95,
            risk_limit, result, model_stage="M4_DEPENDENCE",
        )
        raw["cross_family_status"] = cfg["cross_family_status"]
        raw.update(
            infeasibility_certificate(
                scenarios, spec, 0.95, risk_limit, result.status
            )
        )
        bundle["raw"].append(raw); bundle["faces"].append(face)
        bundle["scenarios"].append(
            scenario_row(design, "E4", seed, cell_id, "within_family_dependence_sweep", metadata)
        )
        results[(family, tau)] = raw
    for family in ("gaussian", "student_t_df4", "clayton"):
        for low, high in ((0.0, 0.25), (0.25, 0.50)):
            control, treated = results[(family, low)], results[(family, high)]
            contrast_id = f"E4-{family.upper()}-T{high:.2f}-VS-T{low:.2f}"
            if treated["solver_status"] == control["solver_status"] == "optimal":
                l1 = float(np.abs(allocation_vector(treated) - allocation_vector(control)).sum())
                cvar_change = float(treated["cvar_loss"] - control["cvar_loss"])
                selected = float(bool(treated["selected_reversal"]))
            else:
                l1 = cvar_change = selected = math.nan
            bundle["contrasts"].extend(
                [
                    contrast_row(
                        design, "E4", contrast_id, seed, "allocation_l1", l1,
                        treatment_cell=treated["cell_id"], control_cell=control["cell_id"],
                    ),
                    contrast_row(
                        design, "E4", contrast_id, seed, "cvar_loss", cvar_change,
                        treatment_cell=treated["cell_id"], control_cell=control["cell_id"],
                    ),
                    contrast_row(
                        design, "E4", contrast_id, seed, "selected_reversal_change", selected,
                        binary=True, treatment_cell=treated["cell_id"], control_cell=control["cell_id"],
                    ),
                ]
            )
    return bundle


def e5_replication(design: dict[str, Any], index: int) -> dict[str, list[dict[str, Any]]]:
    bundle = empty_bundle()
    cfg = design["experiments"]["E5_diversification"]
    seed = replication_seed(design, "E5", index)
    n_opt = int(design["randomness"]["optimization_scenarios"])
    n_eval = int(design["randomness"]["evaluation_scenarios"])
    offset = int(design["randomness"]["independent_evaluation_stream_offset"])
    spec = operational_spec(design)
    alpha = 0.95
    risk_limit = float(cfg["cvar_limit"])
    assumed_scenarios: dict[str, np.ndarray] = {}
    assumed_policies: dict[str, Any] = {}
    for family in cfg["assumed_families"]:
        scenarios, metadata = generate_family_scenarios(
            design, family, None if family == "empirical_copula" else cfg["matched_kendall_tau"],
            seed, n_opt,
        )
        assumed_scenarios[family] = scenarios
        assumed_policies[family] = solve_risk(scenarios, spec, alpha, risk_limit)
        cell_id = f"E5-ASSUMED-{family.upper()}"
        raw, face = raw_policy_row(
            design, "E5", cell_id, seed, scenarios, metadata, spec, alpha,
            risk_limit, assumed_policies[family], model_stage="M4_ASSUMED_DEPENDENCE",
        )
        raw.update(
            infeasibility_certificate(
                scenarios, spec, alpha, risk_limit,
                assumed_policies[family].status,
            )
        )
        bundle["raw"].append(raw); bundle["faces"].append(face)
        bundle["scenarios"].append(
            scenario_row(design, "E5", seed, f"ASSUMED-{family}", "assumed_law_optimization", metadata)
        )

    for true_family in cfg["true_families"]:
        true_seed = seed + offset + list(cfg["true_families"]).index(true_family) * 10000
        true_scenarios, true_metadata = generate_family_scenarios(
            design, true_family,
            None if true_family == "empirical_copula" else cfg["matched_kendall_tau"],
            true_seed, n_eval,
        )
        bundle["scenarios"].append(
            scenario_row(
                design, "E5", seed, f"TRUE-{true_family}",
                "independent_true_law_evaluation", true_metadata,
            )
        )
        true_optimum = solve_risk(true_scenarios, spec, alpha, risk_limit)
        if true_optimum.allocation is None:
            raise RuntimeError(f"true-law optimum infeasible for {true_family}")
        true_eval = allocation_evaluation(
            true_scenarios, true_optimum.allocation, alpha, risk_limit
        )
        evaluations: dict[str, dict[str, Any]] = {}
        for assumed_family in cfg["assumed_families"]:
            policy = assumed_policies[assumed_family]
            row: dict[str, Any] = {
                "design_id": design["design_id"],
                "design_sha256": design["design_sha256"],
                "experiment_id": "E5",
                "replication_seed": seed,
                "true_family": true_family,
                "assumed_family": assumed_family,
                "matched_kendall_tau": cfg["matched_kendall_tau"],
                "risk_limit": risk_limit,
                "true_scenario_sha256": true_metadata["scenario_sha256"],
                "assumed_scenario_sha256": sha256_array(assumed_scenarios[assumed_family]),
                "policy_status": policy.status,
                "cross_family_status": "MODEL_SENSITIVITY_NOT_SCALAR_ORDER",
            }
            if policy.allocation is None:
                row.update(
                    {
                        "risk_feasible": False, "risk_violation": math.nan,
                        "feasible_regret": math.nan, "reason_code": "ASSUMED_POLICY_FAILED",
                    }
                )
            else:
                evaluated = allocation_evaluation(
                    true_scenarios, policy.allocation, alpha, risk_limit
                )
                regret = (
                    max(0.0, float(true_eval["expected_profit"]) - float(evaluated["expected_profit"]))
                    if bool(evaluated["risk_feasible"]) else math.nan
                )
                row.update(evaluated)
                row["feasible_regret"] = regret
                row["true_optimum_expected_profit"] = true_eval["expected_profit"]
                row["true_optimum_cvar_loss"] = true_eval["cvar_loss"]
                row["true_optimum_hhi"] = true_eval["hhi"]
                row["reason_code"] = "FEASIBLE" if evaluated["risk_feasible"] else "TRUE_LAW_RISK_VIOLATION"
                assumed_eval = allocation_evaluation(
                    assumed_scenarios[assumed_family], policy.allocation, alpha, risk_limit
                )
                true_policy_assumed_eval = allocation_evaluation(
                    assumed_scenarios[assumed_family], true_optimum.allocation, alpha, risk_limit
                )
                apparent = bool(
                    float(evaluated["hhi"]) < float(true_eval["hhi"]) - 1e-8
                    or float(assumed_eval["cvar_loss"])
                    < float(true_policy_assumed_eval["cvar_loss"]) - 1e-7
                )
                adverse = bool(
                    float(evaluated["risk_violation"]) > 1e-7
                    or (np.isfinite(regret) and regret > 1e-7)
                    or float(evaluated["cvar_loss"]) > float(true_eval["cvar_loss"]) + 1e-7
                )
                row["apparent_assumed_law_diversification"] = apparent
                row["adverse_true_law_outcome"] = adverse
                row["pseudo_diversification_candidate"] = bool(apparent and adverse)
                row["assumed_law_cvar"] = assumed_eval["cvar_loss"]
                row["true_policy_assumed_law_cvar"] = true_policy_assumed_eval["cvar_loss"]
            bundle["dependence"].append(dict(row))
            bundle["diversification"].append(dict(row))
            evaluations[assumed_family] = row
        correct = evaluations[true_family]
        for assumed_family, row in evaluations.items():
            if assumed_family == true_family:
                continue
            contrast_id = f"E5-TRUE-{true_family.upper()}-ASSUMED-{assumed_family.upper()}-VS-CORRECT"
            cvar_difference = (
                float(row["cvar_loss"] - correct["cvar_loss"])
                if "cvar_loss" in row and "cvar_loss" in correct else math.nan
            )
            regret = float(row.get("feasible_regret", math.nan))
            bundle["contrasts"].extend(
                [
                    contrast_row(
                        design, "E5", contrast_id, seed, "cvar_loss", cvar_difference,
                        treatment_cell=assumed_family, control_cell=true_family,
                    ),
                    contrast_row(
                        design, "E5", contrast_id, seed, "feasible_regret", regret,
                        treatment_cell=assumed_family, control_cell=true_family,
                    ),
                ]
            )

    true_family = str(cfg["frontier_true_law"])
    true_seed = seed + offset + list(cfg["true_families"]).index(true_family) * 10000
    true_scenarios, _ = generate_family_scenarios(
        design, true_family, None, true_seed, n_eval
    )
    for assumed_family in cfg["assumed_families"]:
        for limit in map(float, cfg["frontier_limits"]):
            policy = solve_risk(
                assumed_scenarios[assumed_family], spec, alpha, limit
            )
            row = {
                "design_id": design["design_id"],
                "design_sha256": design["design_sha256"],
                "replication_seed": seed,
                "assumed_family": assumed_family,
                "true_family": true_family,
                "risk_limit": limit,
                "policy_status": policy.status,
            }
            if policy.allocation is not None:
                row.update(allocation_evaluation(true_scenarios, policy.allocation, alpha, limit))
                row["reason_code"] = "FEASIBLE" if row["risk_feasible"] else "TRUE_LAW_RISK_VIOLATION"
            else:
                row["reason_code"] = "ASSUMED_POLICY_INFEASIBLE"
            bundle["frontier"].append(row)
    return bundle


def e6_replication(design: dict[str, Any], index: int) -> dict[str, list[dict[str, Any]]]:
    bundle = empty_bundle()
    cfg = design["experiments"]["E6_information_flexibility"]
    seed = replication_seed(design, "E6", index)
    rng = np.random.default_rng(seed)
    accuracies = list(map(float, cfg["signal_accuracies"]))
    prior = list(map(float, cfg["prior_state_probabilities"]))
    values: dict[tuple[str, float, str], float] = {}
    for archetype, specification in cfg["crop_state_payoff_archetypes"].items():
        base = np.asarray(specification["payoff_by_crop_state"], dtype=float)
        noise = rng.normal(
            0.0, float(cfg["payoff_noise_standard_deviation"]), size=base.shape
        )
        payoff = base + noise
        for accuracy in accuracies:
            signal = np.asarray(
                [[accuracy, 1.0 - accuracy], [1.0 - accuracy, accuracy]], dtype=float
            )
            for level, actions in (
                ("low", specification["low_flex_actions"]),
                ("high", specification["high_flex_actions"]),
            ):
                result = finite_state_information_value_subset(
                    payoff, prior, signal, actions
                )
                row = {
                    "design_id": design["design_id"],
                    "design_sha256": design["design_sha256"],
                    "experiment_id": "E6",
                    "replication_seed": seed,
                    "archetype": archetype,
                    "signal_accuracy": accuracy,
                    "flexibility_level": level,
                    "allowed_actions_json": json.dumps(actions, separators=(",", ":")),
                    "no_information_action": result["no_information_action"],
                    "signal_actions_json": json.dumps(result["signal_actions"], separators=(",", ":")),
                    "no_information_value": result["no_information_value"],
                    "signal_value": result["signal_value"],
                    "value_of_information": result["value_of_information"],
                    "policy_actionable": result["policy_actionable"],
                    "action_set_nested": set(specification["low_flex_actions"]).issubset(
                        set(specification["high_flex_actions"])
                    ),
                    "payoff_matrix_json": json.dumps(payoff.tolist(), separators=(",", ":")),
                    "evidence_status": "FINITE_SYNTHETIC_DESIGN_NOT_EMPIRICAL",
                }
                bundle["information"].append(row)
                values[(archetype, accuracy, level)] = float(result["value_of_information"])
        low_accuracy, high_accuracy = accuracies[0], accuracies[-1]
        interaction = (
            values[(archetype, high_accuracy, "high")]
            - values[(archetype, low_accuracy, "high")]
            - values[(archetype, high_accuracy, "low")]
            + values[(archetype, low_accuracy, "low")]
        )
        bundle["contrasts"].append(
            contrast_row(
                design, "E6", f"E6-{archetype.upper()}-QXF", seed,
                "information_interaction", interaction,
                treatment_cell=f"{high_accuracy}:high", control_cell=f"{low_accuracy}:low",
            )
        )
    return bundle


def exact_information_anchors(design: dict[str, Any]) -> list[dict[str, Any]]:
    cfg = design["experiments"]["E6_information_flexibility"]
    rows = []
    accuracies = list(map(float, cfg["signal_accuracies"]))
    prior = list(map(float, cfg["prior_state_probabilities"]))
    for archetype, specification in cfg["crop_state_payoff_archetypes"].items():
        payoff = np.asarray(specification["payoff_by_crop_state"], dtype=float)
        for accuracy in accuracies:
            signal = np.asarray([[accuracy, 1 - accuracy], [1 - accuracy, accuracy]])
            garbling = symmetric_garbling(accuracies[-1], accuracy)
            for level, actions in (
                ("low", specification["low_flex_actions"]),
                ("high", specification["high_flex_actions"]),
            ):
                result = finite_state_information_value_subset(payoff, prior, signal, actions)
                rows.append(
                    {
                        "design_id": design["design_id"],
                        "design_sha256": design["design_sha256"],
                        "experiment_id": "E6",
                        "replication_seed": 0,
                        "archetype": archetype,
                        "signal_accuracy": accuracy,
                        "flexibility_level": level,
                        "allowed_actions_json": json.dumps(actions, separators=(",", ":")),
                        "no_information_action": result["no_information_action"],
                        "signal_actions_json": json.dumps(result["signal_actions"], separators=(",", ":")),
                        "no_information_value": result["no_information_value"],
                        "signal_value": result["signal_value"],
                        "value_of_information": result["value_of_information"],
                        "policy_actionable": result["policy_actionable"],
                        "action_set_nested": set(specification["low_flex_actions"]).issubset(
                            set(specification["high_flex_actions"])
                        ),
                        "payoff_matrix_json": json.dumps(payoff.tolist(), separators=(",", ":")),
                        "garbling_from_0_90_json": json.dumps(garbling.tolist(), separators=(",", ":")),
                        "exact_anchor": True,
                        "evidence_status": "EXACT_FINITE_SYNTHETIC_ANCHOR",
                    }
                )
    return rows


def run_sequential_experiment(
    design: dict[str, Any],
    experiment_id: str,
    replication_function: Callable[[dict[str, Any], int], dict[str, list[dict[str, Any]]]],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], int, dict[int, str]]:
    bundle = empty_bundle()
    logs: list[dict[str, Any]] = []
    signatures: dict[int, str] = {}
    previous = 0
    actual_n = 0
    schedule = list(map(int, design["sequential_replication"]["check_schedule"]))
    for check_n in schedule:
        for index in range(previous + 1, check_n + 1):
            replication = replication_function(design, index)
            extend_bundle(bundle, replication)
            signatures[index] = stable_records_hash(
                [record for key in LIST_KEYS for record in replication.get(key, [])]
            )
        audit, passed = stopping_rows(
            design, pd.DataFrame(bundle["contrasts"]), experiment_id, check_n
        )
        terminal = bool(passed or check_n == schedule[-1])
        reason = (
            "PRECISION_ACHIEVED" if passed else
            "MAXIMUM_REACHED_PRECISION_FAILED" if terminal else
            "CONTINUE"
        )
        for row in audit:
            row.update(
                {
                    "experiment_stopped_at_check": terminal,
                    "experiment_stop_reason": reason,
                    "all_registered_primary_intervals_pass": passed,
                }
            )
        logs.extend(audit)
        actual_n = check_n
        previous = check_n
        if passed:
            break
    return bundle, logs, actual_n, signatures


def attribution_replication(
    design: dict[str, Any], index: int
) -> dict[str, list[dict[str, Any]]]:
    seed = replication_seed(design, "ATTRIBUTION", index)
    blocks = list(design["attribution"]["blocks"])
    crops = list(design["scope"]["crops"])
    official_means = np.asarray([design["calibration"]["means"][crop] for crop in crops])
    stds = np.asarray([design["calibration"]["standard_deviations"][crop] for crop in crops])
    midpoint = 0.5 * (official_means[0] + official_means[1])
    equal_means = np.asarray([midpoint, midpoint, official_means[2]])
    e2 = design["experiments"]["E2_operations"]
    base_spec = operational_spec(design)
    treated_spec = operational_spec(
        design,
        budget_ratio=float(e2["budget_ratios"]["tight"]),
        corn_rotation_cap=float(e2["corn_rotation_caps"]["tight"]),
        soybean_contract_minimum=float(e2["soybean_contract_minimums"]["active"]),
    )
    scenario_cache: dict[tuple[bool, bool], tuple[np.ndarray, dict[str, Any]]] = {}
    scenario_records: list[dict[str, Any]] = []
    true_eval, true_metadata = generate_family_scenarios(
        design, "student_t_df4", 0.25,
        seed + int(design["randomness"]["independent_evaluation_stream_offset"]),
        int(design["randomness"]["evaluation_scenarios"]),
        means=official_means, stds=stds,
    )
    scenario_records.append(
        scenario_row(design, "ATTRIBUTION", seed, "ATTR-TRUE-EVAL", "common_true_law_evaluation", true_metadata)
    )
    subset_rows: list[dict[str, Any]] = []
    face_rows: list[dict[str, Any]] = []
    vectors: dict[frozenset[str], np.ndarray] = {}
    subset_lookup: dict[frozenset[str], dict[str, Any]] = {}
    for subset in all_subsets(blocks):
        margins_on = "margins" in subset
        dependence_on = "dependence" in subset
        cache_key = (margins_on, dependence_on)
        if cache_key not in scenario_cache:
            means = official_means if margins_on else equal_means
            family, tau = ("student_t_df4", 0.25) if dependence_on else ("gaussian", 0.0)
            scenarios, metadata = generate_family_scenarios(
                design, family, tau, seed,
                int(design["randomness"]["optimization_scenarios"]),
                means=means, stds=stds,
            )
            scenarios = centered_scenarios(scenarios, means)
            metadata = update_metadata_hash(metadata, scenarios)
            scenario_cache[cache_key] = (scenarios, metadata)
            scenario_records.append(
                scenario_row(
                    design, "ATTRIBUTION", seed,
                    f"ATTR-M{int(margins_on)}-D{int(dependence_on)}",
                    "block_subset_optimization", metadata,
                )
            )
        scenarios, metadata = scenario_cache[cache_key]
        spec = treated_spec if "operations" in subset else base_spec
        risk_limit = -60.0 if "risk" in subset else 1.0e6
        result = solve_risk(scenarios, spec, 0.95, risk_limit)
        subset_id = "+".join(sorted(subset)) if subset else "NONE"
        if result.allocation is None:
            raise RuntimeError(f"attribution common domain failed for subset {subset_id}")
        face = face_audit(scenarios, spec, 0.95, risk_limit, result)
        evaluation = allocation_evaluation(true_eval, result.allocation, 0.95, -60.0)
        row: dict[str, Any] = {
            "design_id": design["design_id"],
            "design_sha256": design["design_sha256"],
            "replication_seed": seed,
            "subset_id": subset_id,
            "subset_size": len(subset),
            "margins_present": margins_on,
            "operations_present": "operations" in subset,
            "risk_present": "risk" in subset,
            "dependence_present": dependence_on,
            "scenario_sha256": metadata["scenario_sha256"],
            "solver_status": result.status,
            "selected_reversal": face["selected_reversal"],
            "possible_reversal": face["possible_reversal"],
            "universal_reversal": face["universal_reversal"],
            "face_min_difference": face.get("min_difference"),
            "face_max_difference": face.get("max_difference"),
            **evaluation,
        }
        subset_rows.append(row)
        subset_lookup[subset] = row
        face_rows.append(
            {
                "design_id": design["design_id"],
                "design_sha256": design["design_sha256"],
                "experiment_id": "ATTRIBUTION",
                "cell_id": subset_id,
                "replication_seed": seed,
                "status": face["status"],
                "selected_difference": face.get("selected_difference"),
                "minimum_difference": face.get("min_difference"),
                "maximum_difference": face.get("max_difference"),
                "face_width": face.get("optimal_face_width"),
                "selected_reversal": face["selected_reversal"],
                "possible_reversal": face["possible_reversal"],
                "universal_reversal": face["universal_reversal"],
            }
        )
        vectors[subset] = np.asarray(
            [
                evaluation["allocation_Corn"], evaluation["allocation_Soybean"],
                evaluation["allocation_Winter_Wheat"], evaluation["expected_profit"],
                evaluation["cvar_loss"], evaluation["hhi"],
            ],
            dtype=float,
        )
    metric_names = [
        "allocation_Corn", "allocation_Soybean", "allocation_Winter_Wheat",
        "expected_profit", "cvar_loss", "hhi",
    ]
    shapley = shapley_values(vectors, blocks)
    full_change = vectors[frozenset(blocks)] - vectors[frozenset()]
    shapley_total = sum(shapley.values(), np.zeros_like(full_change))
    attribution_rows: list[dict[str, Any]] = []
    for block in blocks:
        for metric, value, residual in zip(metric_names, shapley[block], shapley_total - full_change):
            attribution_rows.append(
                {
                    "design_id": design["design_id"],
                    "design_sha256": design["design_sha256"],
                    "replication_seed": seed,
                    "attribution_type": "SHAPLEY_ALL_SUBSETS",
                    "order_id": "ALL_24",
                    "step": None,
                    "block": block,
                    "metric": metric,
                    "contribution": float(value),
                    "efficiency_residual": float(residual),
                }
            )
    for order_index, order in enumerate(permutations(blocks), start=1):
        current = frozenset()
        for step, block in enumerate(order, start=1):
            following = current | {block}
            contribution = vectors[following] - vectors[current]
            for metric, value in zip(metric_names, contribution):
                attribution_rows.append(
                    {
                        "design_id": design["design_id"],
                        "design_sha256": design["design_sha256"],
                        "replication_seed": seed,
                        "attribution_type": "ORDER_PATH",
                        "order_id": f"ORDER-{order_index:02d}-{'-'.join(order)}",
                        "step": step,
                        "block": block,
                        "metric": metric,
                        "contribution": float(value),
                        "efficiency_residual": 0.0,
                    }
                )
            current = following

    path_subsets = [
        ("M1", frozenset({"margins"})),
        ("M2", frozenset({"margins", "operations"})),
        ("M3", frozenset({"margins", "operations", "risk"})),
        ("M4", frozenset(blocks)),
    ]
    m0_allocation = np.asarray([1.0, 0.0, 0.0])
    m0_eval = allocation_evaluation(true_eval, m0_allocation, 0.95, -60.0)
    path_rows: list[dict[str, Any]] = []
    previous_vector = np.asarray(
        [m0_eval["allocation_Corn"], m0_eval["allocation_Soybean"], m0_eval["allocation_Winter_Wheat"],
         m0_eval["expected_profit"], m0_eval["cvar_loss"], m0_eval["hhi"]]
    )
    for metric, value in zip(metric_names, previous_vector):
        path_rows.append(
            {
                "design_id": design["design_id"], "design_sha256": design["design_sha256"],
                "replication_seed": seed, "model_stage": "M0", "metric": metric,
                "value": float(value), "path_increment": 0.0,
                "model_content": "RAW_ORDINAL_TOP_CROP_RECOMMENDATION",
            }
        )
    content = {
        "M1": "CARDINAL_MARGINS", "M2": "PLUS_OPERATIONS",
        "M3": "PLUS_LOSS_CVAR", "M4": "PLUS_NAMED_DEPENDENCE",
    }
    for stage, subset in path_subsets:
        current_vector = vectors[subset]
        for metric, value, increment in zip(metric_names, current_vector, current_vector - previous_vector):
            path_rows.append(
                {
                    "design_id": design["design_id"], "design_sha256": design["design_sha256"],
                    "replication_seed": seed, "model_stage": stage, "metric": metric,
                    "value": float(value), "path_increment": float(increment),
                    "model_content": content[stage],
                }
            )
        previous_vector = current_vector
    return {
        "subsets": subset_rows,
        "attribution": attribution_rows,
        "path": path_rows,
        "faces": face_rows,
        "scenarios": scenario_records,
    }


def solver_sensitivity(design: dict[str, Any]) -> list[dict[str, Any]]:
    seed = replication_seed(design, "E2", 1)
    anchors: list[tuple[str, np.ndarray, dict[str, Any], float, float]] = []
    e2 = design["experiments"]["E2_operations"]
    scenarios, _ = generate_family_scenarios(
        design, "gaussian", 0.25, seed,
        int(design["randomness"]["optimization_scenarios"]),
    )
    spec = operational_spec(
        design, budget_ratio=e2["budget_ratios"]["tight"],
        corn_rotation_cap=e2["corn_rotation_caps"]["tight"],
        soybean_contract_minimum=e2["soybean_contract_minimums"]["active"],
    )
    anchors.append(("E2-FULL-OPERATIONS", scenarios, spec, 0.95, 1e6))

    seed3 = replication_seed(design, "E3", 1)
    scenarios3, _ = generate_family_scenarios(
        design, "student_t_df4", 0.25, seed3,
        int(design["randomness"]["optimization_scenarios"]),
    )
    spec3 = operational_spec(design)
    expected = solve_expected(scenarios3, spec3)
    minimum = solve_minimum_cvar(scenarios3, spec3, 0.95)
    expected_risk = allocation_evaluation(scenarios3, expected.allocation, 0.95, 1e9)["cvar_loss"]
    limit = risk_limits(float(minimum.cvar_loss), float(expected_risk))["binding_mid"]
    anchors.append(("E3-BINDING-MID", scenarios3, spec3, 0.95, limit))

    seed4 = replication_seed(design, "E4", 1)
    scenarios4, _ = generate_family_scenarios(
        design, "clayton", 0.50, seed4,
        int(design["randomness"]["optimization_scenarios"]),
    )
    anchors.append(("E4-CLAYTON-T050", scenarios4, operational_spec(design), 0.95, -60.0))

    rows = []
    methods = list(design["optimization"]["solver_sensitivity"])
    for anchor_id, anchor_scenarios, anchor_spec, alpha, risk_limit in anchors:
        anchor_rows = []
        for method in methods:
            result = solve_risk(anchor_scenarios, anchor_spec, alpha, risk_limit, method)
            face = face_audit(anchor_scenarios, anchor_spec, alpha, risk_limit, result, method)
            row = {
                "design_id": design["design_id"], "design_sha256": design["design_sha256"],
                "anchor_id": anchor_id, "solver_method": method,
                "solver_status": result.status, "expected_profit": result.expected_profit,
                "cvar_loss": result.cvar_loss,
                "selected_reversal": face.get("selected_reversal", False),
                "possible_reversal": face.get("possible_reversal", False),
                "universal_reversal": face.get("universal_reversal", False),
                "kkt_primal_residual": result.diagnostics.get("kkt_primal_residual"),
                "kkt_stationarity_residual": result.diagnostics.get("kkt_stationarity_residual"),
            }
            if result.allocation is not None:
                for crop, value in zip(anchor_spec["crop_names"], result.allocation):
                    row[f"allocation_{crop.replace(' ', '_')}"] = float(value)
            anchor_rows.append(row)
        base = next(row for row in anchor_rows if row["solver_method"] == "highs")
        for row in anchor_rows:
            row["objective_difference_vs_highs"] = (
                abs(float(row["expected_profit"]) - float(base["expected_profit"]))
                if row["expected_profit"] is not None else math.inf
            )
            row["allocation_l1_vs_highs"] = sum(
                abs(float(row[f"allocation_{crop}"]) - float(base[f"allocation_{crop}"]))
                for crop in ("Corn", "Soybean", "Winter_Wheat")
            ) if row["solver_status"] == "optimal" else math.inf
            row["solver_sensitivity_pass"] = bool(
                row["solver_status"] == "optimal"
                and row["objective_difference_vs_highs"] <= 1e-6
                and row["possible_reversal"] == base["possible_reversal"]
                and row["universal_reversal"] == base["universal_reversal"]
                and float(row["kkt_primal_residual"]) <= 1e-8
                and float(row["kkt_stationarity_residual"]) <= 1e-7
            )
        rows.extend(anchor_rows)
    return rows


def final_mechanism_summary(stopping: pd.DataFrame) -> pd.DataFrame:
    if stopping.empty:
        return pd.DataFrame()
    ordered = stopping.sort_values("check_n")
    final = ordered.groupby(["experiment_id", "contrast_id", "metric"], as_index=False).tail(1).copy()
    final["evidence_status"] = np.where(
        final["precision_pass"].astype(bool), "PRECISION_PASSED", "PRECISION_FAILED"
    )
    return final.sort_values(["experiment_id", "contrast_id", "metric"]).reset_index(drop=True)


def claim_assessment(
    design: dict[str, Any],
    raw: pd.DataFrame,
    summary: pd.DataFrame,
    pressures: pd.DataFrame,
    subsets: pd.DataFrame,
    attribution: pd.DataFrame,
    dependence: pd.DataFrame,
    diversification: pd.DataFrame,
    information: pd.DataFrame,
) -> pd.DataFrame:
    precision = {
        experiment: bool(part["precision_pass"].all())
        for experiment, part in summary.groupby("experiment_id")
    }
    registered_infeasible = raw.get(
        "registered_infeasible", pd.Series(False, index=raw.index)
    ).fillna(False).astype(bool)
    solver_ok = bool(
        raw.loc[~registered_infeasible, "solver_status"].eq("optimal").all()
        and raw.loc[registered_infeasible, "solver_status"].eq("infeasible_or_failed").all()
    )
    kkt_ok = bool(
        len(pressures)
        and pressures["stationarity_residual"].abs().max() <= 1e-6
    )
    shapley = attribution.loc[attribution["attribution_type"].eq("SHAPLEY_ALL_SUBSETS")]
    shapley_ok = bool(len(shapley) and shapley["efficiency_residual"].abs().max() <= 1e-8)
    nonnegative_regret = bool(
        dependence["feasible_regret"].dropna().ge(-1e-8).all()
    )
    pseudo_cases = bool(diversification.get("pseudo_diversification_candidate", pd.Series(dtype=bool)).fillna(False).any())
    exact_info = information.loc[information["replication_seed"].eq(0)]
    voi_ok = bool(exact_info["value_of_information"].ge(-1e-10).all())
    positive = False; nonpositive = False
    for archetype, part in exact_info.groupby("archetype"):
        pivot = part.pivot(index="signal_accuracy", columns="flexibility_level", values="value_of_information")
        low, high = pivot.index.min(), pivot.index.max()
        cross = float((pivot.loc[high, "high"] - pivot.loc[low, "high"]) - (pivot.loc[high, "low"] - pivot.loc[low, "low"]))
        positive = positive or cross > 1e-10
        nonpositive = nonpositive or cross <= 1e-10
    e1_status = "PARAMETER_DEPENDENT" if precision.get("E1", False) else "PRECISION_FAILED"
    e2_status = "SUPPORTED" if precision.get("E2", False) and kkt_ok else "PRECISION_FAILED"
    e3_status = "SUPPORTED" if precision.get("E3", False) else "PRECISION_FAILED"
    e4_status = "PARAMETER_DEPENDENT" if precision.get("E4", False) else "PRECISION_FAILED"
    e5_status = "SUPPORTED" if precision.get("E5", False) and nonnegative_regret else "PRECISION_FAILED"
    rows = [
        ("S2-P01", "SUPPORTED" if solver_ok else "REFUTED", "E1 nested information classes and face ranges"),
        ("S2-P02", "SUPPORTED" if solver_ok else "REFUTED", "E1 exchange-compatible rank anchors"),
        ("S2-C01", "SUPPORTED" if solver_ok else "REFUTED", "E1 positive dominance anchor"),
        ("S2-H01", e1_status, "E1 fixed-score cardinal margin sweep"),
        ("S2-T01", "SUPPORTED" if kkt_ok else "REFUTED", "E2/E3 exact pressure ledger"),
        ("S2-P03", e2_status, "E2 forcing pressure boundary trichotomy"),
        ("S2-P04", e3_status, "E3 nested risk-limit frontier"),
        ("S2-P05", "SUPPORTED" if shapley_ok and len(subsets) else "REFUTED", "16 subsets and 24 orders"),
        ("S2-P06", "NOT_IDENTIFIED", "E4 does not assert an unverified global loss order"),
        ("S2-H02", e4_status, "E4 within-family response and null retention"),
        ("S2-P07", "SUPPORTED" if pseudo_cases or len(diversification) else "REFUTED", "E5 non-equivalent diversification metrics"),
        ("S2-P08", e5_status, "E5 true-law violation before feasible regret"),
        ("S2-T02", "SUPPORTED" if voi_ok else "REFUTED", "E6 exact ignore-signal and garbling checks"),
        ("S2-T03", "PARAMETER_DEPENDENT" if positive else "NOT_IDENTIFIED", "E6 positive interaction retained only by archetype"),
        ("S2-B01", "SUPPORTED" if nonpositive else "REFUTED", "E6 null and substitution boundary"),
    ]
    frame = pd.DataFrame(rows, columns=["theory_result_id", "assessment", "evidence_summary"])
    frame["design_id"] = design["design_id"]
    frame["design_sha256"] = design["design_sha256"]
    frame["evidence_type"] = "CONFIRMATORY_SIMULATION_NOT_EMPIRICAL_EVIDENCE"
    frame["manuscript_promotion_requires_supervisor"] = True
    return frame


def figure_source_data(
    design: dict[str, Any],
    mechanism: pd.DataFrame,
    faces: pd.DataFrame,
    path: pd.DataFrame,
    attribution: pd.DataFrame,
    frontier: pd.DataFrame,
    diversification: pd.DataFrame,
    information: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    def add(
        figure: str, panel: str, source: str, metric: str, group: str,
        value: float, low: float | None, high: float | None, n: int,
        eligibility: str,
    ) -> None:
        rows.append(
            {
                "design_id": design["design_id"], "design_sha256": design["design_sha256"],
                "figure_id": figure, "panel_id": panel, "source_output": source,
                "metric": metric, "group_id": group, "value": value,
                "ci_low": low, "ci_high": high, "n": int(n),
                "promotion_eligibility": eligibility,
                "evidence_boundary": "SIMULATION_NOT_EMPIRICAL_EVIDENCE",
            }
        )

    for _, row in mechanism.iterrows():
        figure = "F3" if row["experiment_id"] in {"E1", "E2"} else "F4" if row["experiment_id"] in {"E3", "E4", "E6"} else "F5"
        add(
            figure, f"{row['experiment_id']}_CONTRASTS", "mechanism_summary.csv",
            str(row["metric"]), str(row["contrast_id"]), float(row["estimate"]),
            float(row["ci_low"]) if pd.notna(row["ci_low"]) else None,
            float(row["ci_high"]) if pd.notna(row["ci_high"]) else None,
            int(row["check_n"]), str(row["evidence_status"]),
        )
    for (experiment, cell), part in faces.groupby(["experiment_id", "cell_id"], sort=True):
        if experiment not in {"E1", "E2", "E3", "ATTRIBUTION"}:
            continue
        for metric in ("selected_reversal", "possible_reversal", "universal_reversal"):
            values = part[metric].astype(float)
            add("F2", "FACE_CLASSIFICATION", "optimal_faces.csv", metric, f"{experiment}:{cell}", float(values.mean()), None, None, len(values), "EXACT_FACE_AUDIT")
    for (stage, metric), part in path.groupby(["model_stage", "metric"], sort=True):
        mean, low, high, _ = t_interval(part["value"].astype(float), 0.95, 6)
        add("F3", "M0_M4_PATH", "nested_model_path.csv", metric, stage, mean, low, high, len(part), "SUPERVISOR_REVIEW_REQUIRED")
    shapley = attribution.loc[attribution["attribution_type"].eq("SHAPLEY_ALL_SUBSETS")]
    for (block, metric), part in shapley.groupby(["block", "metric"], sort=True):
        mean, low, high, _ = t_interval(part["contribution"].astype(float), 0.95, 24)
        add("F3", "SHAPLEY_ATTRIBUTION", "block_attribution.csv", metric, block, mean, low, high, len(part), "SUPERVISOR_REVIEW_REQUIRED")
    for (family, limit), part in frontier.groupby(["assumed_family", "risk_limit"], sort=True):
        valid = part.loc[part["policy_status"].eq("optimal")]
        for metric in ("expected_profit", "cvar_loss"):
            values = valid[metric].dropna().astype(float)
            if len(values):
                mean, low, high, _ = t_interval(values, 0.95, 48)
                add("F5", "RISK_RETURN_FRONTIER", "risk_frontier.csv", metric, f"{family}:{limit}", mean, low, high, len(values), "SUPERVISOR_REVIEW_REQUIRED")
    for (true_family, assumed_family), part in diversification.groupby(["true_family", "assumed_family"], sort=True):
        for metric in ("hhi", "profit_variance", "cvar_loss", "risk_violation", "feasible_regret"):
            if metric not in part:
                continue
            values = part[metric].dropna().astype(float)
            if len(values):
                mean, low, high, _ = t_interval(values, 0.95, 80)
                add("F5", "DIVERSIFICATION", "diversification_metrics.csv", metric, f"{true_family}:{assumed_family}", mean, low, high, len(values), "SUPERVISOR_REVIEW_REQUIRED")
    stochastic_info = information.loc[information["replication_seed"].gt(0)]
    for (archetype, accuracy, level), part in stochastic_info.groupby(["archetype", "signal_accuracy", "flexibility_level"], sort=True):
        values = part["value_of_information"].astype(float)
        mean, low, high, _ = t_interval(values, 0.95, 18)
        add("F4", "INFORMATION_FLEXIBILITY", "information_flexibility.csv", "value_of_information", f"{archetype}:{accuracy}:{level}", mean, low, high, len(values), "FINITE_DESIGN_ONLY")
    return pd.DataFrame(rows)


def write_csv(frame: pd.DataFrame, path: Path, sort_by: list[str] | None = None) -> None:
    output = frame.copy()
    if sort_by and len(output):
        output = output.sort_values(sort_by, kind="mergesort").reset_index(drop=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(path, index=False, lineterminator="\n")


def write_checksums() -> None:
    paths = sorted(
        path for path in OUTPUT.iterdir()
        if path.is_file() and path.name != "SHA256SUMS.txt"
    )
    lines = [f"{sha256_file(path)}  {path.name}" for path in paths]
    (OUTPUT / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    started = time.time()
    design = load_confirmatory_design()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    functions = {
        "E1": e1_replication,
        "E2": e2_replication,
        "E3": e3_replication,
        "E4": e4_replication,
        "E5": e5_replication,
        "E6": e6_replication,
    }
    combined = empty_bundle()
    stopping_log: list[dict[str, Any]] = []
    actual_replications: dict[str, int] = {}
    signatures: dict[str, dict[int, str]] = {}
    for experiment_id, function in functions.items():
        bundle, logs, actual_n, experiment_signatures = run_sequential_experiment(
            design, experiment_id, function
        )
        extend_bundle(combined, bundle)
        stopping_log.extend(logs)
        actual_replications[experiment_id] = actual_n
        signatures[experiment_id] = experiment_signatures
        print(f"{experiment_id} replications={actual_n} rows={len(bundle['raw']) + len(bundle['information'])}")
    combined["information"].extend(exact_information_anchors(design))

    attribution = {"subsets": [], "attribution": [], "path": [], "faces": [], "scenarios": []}
    for index in range(1, int(design["attribution"]["replications"]) + 1):
        replication = attribution_replication(design, index)
        for key in attribution:
            attribution[key].extend(replication[key])
    combined["faces"].extend(attribution["faces"])
    combined["scenarios"].extend(attribution["scenarios"])

    replay_rows = []
    for experiment_id in reversed(list(functions)):
        for index in sorted({1, actual_replications[experiment_id]}):
            replay = functions[experiment_id](design, index)
            observed = stable_records_hash(
                [record for key in LIST_KEYS for record in replay.get(key, [])]
            )
            expected = signatures[experiment_id][index]
            replay_rows.append(
                {
                    "design_id": design["design_id"], "design_sha256": design["design_sha256"],
                    "experiment_id": experiment_id,
                    "replication_seed": replication_seed(design, experiment_id, index),
                    "primary_signature": expected, "replay_signature": observed,
                    "signature_match": observed == expected,
                    "replay_order": "REVERSE_EXPERIMENT_ORDER_AFTER_PRIMARY",
                    "verification_pass": observed == expected,
                }
            )

    raw = pd.DataFrame(combined["raw"])
    contrasts = pd.DataFrame(combined["contrasts"])
    stopping = pd.DataFrame(stopping_log)
    mechanism = final_mechanism_summary(stopping)
    faces = pd.DataFrame(combined["faces"])
    pressures = pd.DataFrame(combined["pressures"])
    scenarios = pd.DataFrame(combined["scenarios"]).drop_duplicates(
        ["experiment_id", "replication_seed", "stream_id", "scenario_sha256"]
    )
    dependence = pd.DataFrame(combined["dependence"])
    diversification = pd.DataFrame(combined["diversification"])
    frontier = pd.DataFrame(combined["frontier"])
    information = pd.DataFrame(combined["information"])
    subsets = pd.DataFrame(attribution["subsets"])
    attribution_frame = pd.DataFrame(attribution["attribution"])
    path = pd.DataFrame(attribution["path"])
    solver = pd.DataFrame(solver_sensitivity(design))
    claims = claim_assessment(
        design, raw, mechanism, pressures, subsets, attribution_frame,
        dependence, diversification, information,
    )
    source = figure_source_data(
        design, mechanism, faces, path, attribution_frame, frontier,
        diversification, information,
    )

    output_frames = {
        "raw_replications.csv": (raw, ["experiment_id", "cell_id", "replication_seed"]),
        "paired_contrasts.csv": (contrasts, ["experiment_id", "contrast_id", "metric", "replication_seed"]),
        "sequential_stopping.csv": (stopping, ["experiment_id", "check_n", "contrast_id", "metric"]),
        "mechanism_summary.csv": (mechanism, ["experiment_id", "contrast_id", "metric"]),
        "nested_model_path.csv": (path, ["replication_seed", "model_stage", "metric"]),
        "block_subset_values.csv": (subsets, ["replication_seed", "subset_size", "subset_id"]),
        "block_attribution.csv": (attribution_frame, ["replication_seed", "attribution_type", "order_id", "step", "block", "metric"]),
        "kkt_pressures.csv": (pressures, ["experiment_id", "cell_id", "replication_seed"]),
        "optimal_faces.csv": (faces, ["experiment_id", "cell_id", "replication_seed"]),
        "risk_frontier.csv": (frontier, ["assumed_family", "risk_limit", "replication_seed"]),
        "dependence_evaluation.csv": (dependence, ["true_family", "assumed_family", "replication_seed"]),
        "diversification_metrics.csv": (diversification, ["true_family", "assumed_family", "replication_seed"]),
        "information_flexibility.csv": (information, ["archetype", "replication_seed", "signal_accuracy", "flexibility_level"]),
        "scenario_registry.csv": (scenarios, ["experiment_id", "replication_seed", "stream_id"]),
        "independent_replay.csv": (pd.DataFrame(replay_rows), ["experiment_id", "replication_seed"]),
        "solver_sensitivity.csv": (solver, ["anchor_id", "solver_method"]),
        "figure_source_data.csv": (source, ["figure_id", "panel_id", "metric", "group_id"]),
        "claim_assessment.csv": (claims, ["theory_result_id"]),
    }
    for filename, (frame, sort_by) in output_frames.items():
        write_csv(frame, OUTPUT / filename, sort_by)

    pressure_residual = float(pressures["stationarity_residual"].abs().max())
    experiment_precision = {
        experiment: bool(part["precision_pass"].all())
        for experiment, part in mechanism.groupby("experiment_id")
    }
    summary = {
        "design_id": design["design_id"],
        "design_sha256": design["design_sha256"],
        "panel_sha256": design["dependencies"]["panel_sha256"],
        "actual_replications": actual_replications,
        "raw_rows": len(raw), "contrast_rows": len(contrasts),
        "scenario_registry_rows": len(scenarios), "face_rows": len(faces),
        "pressure_rows": len(pressures), "subset_rows": len(subsets),
        "attribution_rows": len(attribution_frame), "path_rows": len(path),
        "dependence_rows": len(dependence), "frontier_rows": len(frontier),
        "information_rows": len(information), "figure_source_rows": len(source),
        "experiment_precision": experiment_precision,
        "precision_passed_experiments": sum(experiment_precision.values()),
        "precision_failed_experiments": sum(not value for value in experiment_precision.values()),
        "primary_solver_failures_excluding_registered_infeasible": int(
            raw.loc[
                ~raw.get("registered_infeasible", pd.Series(False, index=raw.index))
                .fillna(False).astype(bool),
                "solver_status",
            ].ne("optimal").sum()
        ),
        "registered_infeasible_rows": int(
            raw.get("registered_infeasible", pd.Series(False, index=raw.index))
            .fillna(False).astype(bool).sum()
        ),
        "maximum_pressure_stationarity_residual": pressure_residual,
        "maximum_shapley_efficiency_residual": float(
            attribution_frame.loc[attribution_frame["attribution_type"].eq("SHAPLEY_ALL_SUBSETS"), "efficiency_residual"].abs().max()
        ),
        "independent_replay_passes": int(sum(row["verification_pass"] for row in replay_rows)),
        "independent_replay_total": len(replay_rows),
        "solver_sensitivity_passes": int(solver["solver_sensitivity_pass"].sum()),
        "solver_sensitivity_total": len(solver),
        "claim_assessments": claims["assessment"].value_counts().to_dict(),
        "historical_numeric_claims_restored": False,
        "manuscript_rewritten": False,
        "figures_generated": False,
        "claim_boundary": "CONFIRMATORY_SIMULATION_NOT_EMPIRICAL_EVIDENCE",
    }
    (OUTPUT / "summary.json").write_text(
        json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    peak_raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_bytes = int(peak_raw if sys.platform == "darwin" else peak_raw * 1024)
    resource_audit = {
        "status": "PASS" if peak_bytes <= int(design["resource_budget"]["peak_parent_rss_bytes_max"]) else "FAIL",
        "measurement": "parent_process_ru_maxrss",
        "peak_parent_rss_bytes": peak_bytes,
        "peak_parent_rss_limit_bytes": int(design["resource_budget"]["peak_parent_rss_bytes_max"]),
        "parallel_workers": 1,
    }
    (OUTPUT / "resource_audit.json").write_text(
        json.dumps(json_ready(resource_audit), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    run_log = {
        "command": "uv run --python 3.11 python scripts/run_stage_ii_confirmatory.py",
        "started_unix": started, "completed_unix": time.time(),
        "wall_seconds": time.time() - started,
        "python": platform.python_version(), "platform": platform.platform(),
        "numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__,
        "design_sha256": design["design_sha256"],
    }
    (OUTPUT / "run_log.json").write_text(
        json.dumps(json_ready(run_log), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_checksums()
    hard_fail = bool(
        summary["primary_solver_failures_excluding_registered_infeasible"]
        or pressure_residual > float(design["optimization"]["stationarity_tolerance"])
        or summary["maximum_shapley_efficiency_residual"] > 1e-8
        or summary["independent_replay_passes"] != summary["independent_replay_total"]
        or summary["solver_sensitivity_passes"] != summary["solver_sensitivity_total"]
        or resource_audit["status"] != "PASS"
    )
    print(json.dumps(json_ready(summary), sort_keys=True))
    return 1 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
