#!/usr/bin/env python3
"""Issue #5 frozen-design and stochastic-optimization engine gate."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "simulation/src"), str(ROOT / "optimization/src")]

from crop_simulation.experiment_design import expand_design, load_experiment_design  # noqa: E402
from crop_simulation.stress_calibration import LEGACY_RESULT_DRIVEN_SEARCH_DISABLED  # noqa: E402


def rows(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


errors: list[str] = []
design = load_experiment_design()
cells = expand_design(design)
if len(cells) != 90 or cells["cell_id"].duplicated().any():
    errors.append("design_cell_cardinality")
if int(design["resource_budget"]["formal_cells"]) != len(cells):
    errors.append("resource_cell_mismatch")
expected_solves = len(cells) * int(design["design"]["formal_replications_per_cell"])
if int(design["resource_budget"]["formal_solves"]) != expected_solves:
    errors.append("resource_solve_mismatch")
if design["scientific_scope"]["manuscript_admissibility"] != "DRY_RUN_ONLY_UNTIL_ISSUE_6":
    errors.append("formal_run_boundary")

with (ROOT / "simulation/configs/base_config.yaml").open(encoding="utf-8") as handle:
    smoke = yaml.safe_load(handle)
if smoke.get("design_status") != "DRY_RUN_ONLY" or float(smoke.get("total_acres", -1)) != 1.0:
    errors.append("smoke_config_status_or_unit")
smoke_text = (ROOT / "simulation/configs/base_config.yaml").read_text(encoding="utf-8")
for forbidden in ("total_acres: 500", "budget: 220000", "cvar_limit: 30000", "tail_probability: 0.07", "20260703"):
    if forbidden in smoke_text:
        errors.append(f"draft_parameter_survives:{forbidden}")

summary = json.loads((ROOT / "simulation/dry_run/summary.json").read_text(encoding="utf-8"))
if summary.get("design_sha256") != design["design_sha256"]:
    errors.append("dry_run_design_hash")
for key in ("all_exact_repeat", "all_finite", "all_solvers_optimal"):
    if summary.get(key) is not True:
        errors.append(f"dry_run_failure:{key}")
dry_rows = rows("simulation/dry_run/design_cells.csv")
if len(dry_rows) != 3 or any(row["manuscript_admissible"] != "NO" for row in dry_rows):
    errors.append("dry_run_rows_or_admissibility")
if {row["copula_family"] for row in dry_rows} != {"gaussian", "student_t_df4", "clayton"}:
    errors.append("dry_run_copula_coverage")
if {row["marginal_family"] for row in dry_rows} != {"gaussian", "student_t_df5", "empirical_resample"}:
    errors.append("dry_run_marginal_coverage")

parameters = rows("evidence_registry/parameter_provenance.csv")
simulation_parameters = [row for row in parameters if row["parameter_id"].startswith("P-SIM-")]
if len(simulation_parameters) != 10:
    errors.append(f"simulation_parameter_count:{len(simulation_parameters)}")
for row in simulation_parameters:
    if row["config_path"] != "simulation/configs/experiment_design.yaml":
        errors.append(f"parameter_config_link:{row['parameter_id']}")
    if not row["evidence_status"] or not row["uncertainty_method"]:
        errors.append(f"parameter_incomplete:{row['parameter_id']}")
for parameter_id in ("P-SIM-001", "P-SIM-002", "P-SIM-003", "P-SIM-004", "P-SIM-008", "P-SIM-009", "P-SIM-010"):
    row = next(item for item in simulation_parameters if item["parameter_id"] == parameter_id)
    if row["evidence_status"] != "ILLUSTRATIVE_ONLY":
        errors.append(f"illustrative_boundary:{parameter_id}")

simulation_claims = [row for row in rows("evidence_registry/claims.csv") if row["claim_id"].startswith("SIM-C")]
if {row["claim_id"] for row in simulation_claims} != {f"SIM-C{i:02d}" for i in range(1, 9)}:
    errors.append("simulation_claim_set")
dry_claim = next((row for row in simulation_claims if row["claim_id"] == "SIM-C08"), None)
if not dry_claim or dry_claim["manuscript_admissible"] != "NO":
    errors.append("dry_claim_admissibility")

simulation_numbers = [row for row in rows("evidence_registry/numbers.csv") if row["number_id"].startswith("NUM-SIM-")]
if {row["number_id"] for row in simulation_numbers} != {"NUM-SIM-001", "NUM-SIM-002", "NUM-SIM-003"}:
    errors.append("simulation_number_set")
for row in simulation_numbers:
    path = ROOT / row["output_file"]
    if not path.is_file():
        errors.append(f"simulation_number_missing_output:{row['number_id']}")
    elif hashlib.sha256(path.read_bytes()).hexdigest() != row["checksum"]:
        errors.append(f"simulation_number_checksum:{row['number_id']}")

theory_map = rows("theory/repaired/theory_to_simulation_map.csv")
if {row["theory_result_id"] for row in theory_map} != {f"CT{i}" for i in range(1, 11)}:
    errors.append("theory_simulation_map")
if not LEGACY_RESULT_DRIVEN_SEARCH_DISABLED:
    errors.append("legacy_result_search_enabled")

required = {
    "simulation/configs/experiment_design.yaml",
    "simulation/contracts/output_schema.csv",
    "simulation/contracts/randomness_protocol.md",
    "simulation/src/crop_simulation/experiment_design.py",
    "simulation/src/crop_simulation/panel_calibration.py",
    "optimization/src/crop_optimization/optimal_face_audit.py",
    "optimization/src/crop_optimization/crossing_sets.py",
    "optimization/src/crop_optimization/oracles.py",
    "audits/experiment_design_freeze.md",
    "audits/simulation_engine_audit.md",
    "audits/issue_5_acceptance_report.md",
}
for relative in required:
    if not (ROOT / relative).is_file():
        errors.append(f"missing_simulation_asset:{relative}")

print(
    f"design_cells={len(cells)} dry_run_cells={len(dry_rows)} "
    f"simulation_parameters={len(simulation_parameters)} simulation_claims={len(simulation_claims)} "
    f"failures={len(errors)}"
)
for error in errors:
    print(error)
raise SystemExit(bool(errors))
