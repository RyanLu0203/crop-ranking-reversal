#!/usr/bin/env python3
"""Fail-closed acceptance gate for GOAL-14 Stage II theory strengthening."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "theory/stage_ii"

REQUIRED = {
    "README.md",
    "canonical_theory_extension.md",
    "proofs.md",
    "assumption_registry.csv",
    "proposition_audit.csv",
    "mechanism_decomposition.md",
    "counterfactual_attribution_specification.md",
    "diversification_framework.md",
    "information_flexibility_framework.md",
    "theory_to_simulation_mapping.csv",
    "theory_to_empirical_mapping.csv",
    "proof_gap_reconciliation.csv",
    "source_verification.md",
    "baseline_integrity.csv",
    "supervisor_decisions.md",
    "theory_change_log.csv",
    "acceptance_matrix.csv",
}

ASSUMPTION_FIELDS = {
    "assumption_id", "assumption", "scope", "needed_for", "status",
    "verification_or_falsification", "failure_effect",
}
RESULT_FIELDS = {
    "result_id", "result_type", "title", "evidence_class", "assumption_ids",
    "claim_summary", "proof_location", "mechanism_interpretation",
    "simulation_link", "empirical_link", "status",
}
SIM_FIELDS = {
    "theory_result_id", "mechanism", "required_parameters",
    "parameters_to_hold_fixed", "treatment_parameter", "outcome_metrics",
    "necessary_controls", "required_copula_family", "expected_pattern",
    "falsification_pattern", "convergence_requirement", "evidence_status", "notes",
}
EMP_FIELDS = {
    "theory_result_id", "model_prediction", "empirical_construct", "required_data",
    "required_geographic_resolution", "required_temporal_resolution", "sign_or_pattern",
    "timing", "aggregation_risk", "identification_level", "descriptive_or_causal",
    "observable_or_latent", "feasible_with_current_data", "additional_data_needed",
    "admissible_claim", "inadmissible_claim", "notes",
}
GAP_FIELDS = {
    "gap_id", "stage_i_result_id", "stage_i_gap", "stage_ii_disposition",
    "canonical_resolution", "proof_or_boundary", "remaining_owner", "next_action",
    "manuscript_rule",
}
ACCEPTANCE_FIELDS = {
    "requirement_id", "source_requirement", "evidence_file", "verification_rule",
    "status", "notes",
}
ALLOWED_EVIDENCE = {
    "PROVED", "PROVED_CONDITIONAL", "NUMERICAL_HYPOTHESIS",
    "COUNTEREXAMPLE_BOUNDARY", "EMPIRICAL_HYPOTHESIS",
}
ALLOWED_GAPS = {
    "CLOSED_BY_REPAIR", "CLOSED_BY_REPLACEMENT",
    "FALSE_BOUNDARY_RETAINED", "OPEN_STAGE_II",
}
EXPECTED_SIM = {
    "S2-P01", "S2-P02", "S2-C01", "S2-H01", "S2-T01", "S2-P03",
    "S2-P04", "S2-P05", "S2-P06", "S2-H02", "S2-P07", "S2-P08",
    "S2-T02", "S2-T03", "S2-B01",
}


def read_csv(name: str) -> list[dict[str, str]]:
    with (BASE / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check_table(
    errors: list[str], name: str, rows: list[dict[str, str]], fields: set[str]
) -> None:
    actual = set(rows[0]) if rows else set()
    if actual != fields:
        errors.append(
            f"schema:{name}:missing={sorted(fields-actual)}:extra={sorted(actual-fields)}"
        )
    for index, row in enumerate(rows, 1):
        if None in row:
            errors.append(f"extra_csv_fields:{name}:{index}:{row[None]}")
        for key, value in row.items():
            if key is not None and (not isinstance(value, str) or not value.strip()):
                errors.append(f"blank_field:{name}:{index}:{key}")


def require_tokens(errors: list[str], name: str, tokens: list[str]) -> None:
    text = (BASE / name).read_text(encoding="utf-8")
    for token in tokens:
        if token not in text:
            errors.append(f"missing_token:{name}:{token}")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_listing_sha256(path: Path) -> str:
    listing = "".join(
        f"{file_sha256(item)}  {item.relative_to(ROOT).as_posix()}\n"
        for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file())
    )
    return hashlib.sha256(listing.encode("utf-8")).hexdigest()


def main() -> None:
    errors: list[str] = []
    for name in sorted(REQUIRED):
        if not (BASE / name).is_file():
            errors.append(f"missing_file:{name}")
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)

    assumptions = read_csv("assumption_registry.csv")
    results = read_csv("proposition_audit.csv")
    simulation = read_csv("theory_to_simulation_mapping.csv")
    empirical = read_csv("theory_to_empirical_mapping.csv")
    gaps = read_csv("proof_gap_reconciliation.csv")
    acceptance = read_csv("acceptance_matrix.csv")
    integrity = read_csv("baseline_integrity.csv")

    check_table(errors, "assumptions", assumptions, ASSUMPTION_FIELDS)
    check_table(errors, "results", results, RESULT_FIELDS)
    check_table(errors, "simulation", simulation, SIM_FIELDS)
    check_table(errors, "empirical", empirical, EMP_FIELDS)
    check_table(errors, "gaps", gaps, GAP_FIELDS)
    check_table(errors, "acceptance", acceptance, ACCEPTANCE_FIELDS)

    expected_assumptions = {f"S2-A{i:02d}" for i in range(1, 23)}
    assumption_ids = {row["assumption_id"] for row in assumptions}
    if assumption_ids != expected_assumptions:
        errors.append("assumption_id_set_mismatch")
    if len(assumptions) != len(assumption_ids):
        errors.append("duplicate_assumption_id")

    result_ids = [row["result_id"] for row in results]
    if len(result_ids) != len(set(result_ids)):
        errors.append("duplicate_result_id")
    for row in results:
        if row["evidence_class"] not in ALLOWED_EVIDENCE:
            errors.append(f"invalid_evidence_class:{row['result_id']}")
        linked = set(row["assumption_ids"].split(";"))
        if linked - assumption_ids:
            errors.append(f"unknown_assumption:{row['result_id']}:{sorted(linked-assumption_ids)}")
        if row["evidence_class"] == "PROVED" and row["status"].startswith("PREREGISTER"):
            errors.append(f"proved_result_marked_hypothesis:{row['result_id']}")

    simulation_ids = {row["theory_result_id"] for row in simulation}
    empirical_ids = {row["theory_result_id"] for row in empirical}
    if simulation_ids != EXPECTED_SIM:
        errors.append(f"simulation_result_set_mismatch:{sorted(simulation_ids ^ EXPECTED_SIM)}")
    if empirical_ids != EXPECTED_SIM:
        errors.append(f"empirical_result_set_mismatch:{sorted(empirical_ids ^ EXPECTED_SIM)}")

    if {row["gap_id"] for row in gaps} != {f"G{i:02d}" for i in range(1, 21)}:
        errors.append("proof_gap_set_mismatch")
    if {row["stage_ii_disposition"] for row in gaps} - ALLOWED_GAPS:
        errors.append("invalid_proof_gap_disposition")
    if not any(row["stage_ii_disposition"] == "OPEN_STAGE_II" for row in gaps):
        errors.append("no_explicit_open_stage_ii_gap")

    expected_acceptance = {f"G14-{i:02d}" for i in range(1, 17)}
    if {row["requirement_id"] for row in acceptance} != expected_acceptance:
        errors.append("acceptance_requirement_set_mismatch")
    if any(row["status"] != "COMPLETE" for row in acceptance):
        errors.append("acceptance_item_not_complete")

    integrity_by_id = {row["asset_id"]: row for row in integrity}
    # Teacher assets remain immutable.  The manuscript hash is a phase-specific
    # GOAL-14 snapshot: the project control explicitly authorizes the final
    # manuscript rewrite only after GOAL-12/13/15 close, so it must not be
    # compared with the live post-Stage-II manuscript tree.
    expected_integrity = {
        "BASE-TEACHER-TEX": file_sha256(
            ROOT / "baselines/teacher_draft/Crop_ranking_reversal_total.tex"
        ),
        "BASE-TEACHER-PDF": file_sha256(
            ROOT / "baselines/teacher_draft/Crop_ranking_reversal_total.pdf"
        ),
        "BASE-MANUSCRIPT-TREE": "0068bf01eeb3976c4df7ad0639c920c05c0ca60ce11dc323642e9b26a57cd02e",
    }
    for asset_id, observed in expected_integrity.items():
        row = integrity_by_id.get(asset_id)
        if row is None:
            errors.append(f"missing_integrity_asset:{asset_id}")
        elif row["baseline_sha256"] != observed:
            errors.append(
                f"baseline_hash_mismatch:{asset_id}:expected={row['baseline_sha256']}:observed={observed}"
            )

    dispositions = ROOT / "manuscript/registries/draft_completion_disposition.csv"
    if tree_listing_sha256(ROOT / "manuscript") != expected_integrity["BASE-MANUSCRIPT-TREE"]:
        if not dispositions.is_file() or "CLOSED_STAGE_II" not in dispositions.read_text(encoding="utf-8"):
            errors.append("post_goal14_manuscript_rewrite_missing_stage_ii_authorization_marker")

    require_tokens(errors, "README.md", [
        "55b495045fe7a0539c497f3eda1002812fb86506",
        "codex/issue-24-theory-strengthening", "Active issue", "GOAL-12 implementation does not begin",
    ])
    require_tokens(errors, "canonical_theory_extension.md", [
        "Definition S2-D01", "Proposition S2-P02", "Theorem S2-T01",
        "Proposition S2-P04", "Proposition S2-P07", "Theorem S2-T02",
        "Theorem S2-T03", "multi-crop fixed-land simplex is not closed",
    ])
    require_tokens(errors, "proofs.md", [
        "S2-P01", "S2-P02", "S2-C01", "S2-T01", "S2-P03", "S2-P04",
        "S2-P05", "S2-P06", "S2-P07", "S2-P08", "S2-T02", "S2-T03", "S2-B01",
    ])
    require_tokens(errors, "mechanism_decomposition.md", [
        "margin_pressure", "tail_risk_pressure", "budget_pressure",
        "shared_pressure", "boundary_pressure", "not an additive acreage cause",
    ])
    require_tokens(errors, "counterfactual_attribution_specification.md", [
        "M0", "M1", "M2", "M3", "M4", "all 16 subsets", "all 24 block orders",
    ])
    require_tokens(errors, "information_flexibility_framework.md", [
        "garbling matrix", "strong set order", "fixed-land multi-crop simplex fails",
        "substitution",
    ])
    require_tokens(errors, "source_verification.md", [
        "2026-07-21", "rtr179-CVaR1.pdf", "rtr187-CVaR2.pdf",
        "10.1515/demo-2024-0002", "10.21236/ADA016836", "No Topkis citation",
    ])

    check_file = ROOT / "theory/proofs/computational_checks/test_stage_ii_theory.py"
    helper_file = ROOT / "theory/proofs/computational_checks/stage_ii_mechanism_checks.py"
    if not check_file.is_file() or not helper_file.is_file():
        errors.append("missing_stage_ii_computational_checks")

    print(
        f"stage_ii_theory_files={len(REQUIRED)} assumptions={len(assumptions)} "
        f"classified_results={len(results)} simulation_links={len(simulation)} "
        f"empirical_links={len(empirical)} reconciled_gaps={len(gaps)} "
        f"acceptance_items={len(acceptance)} failures={len(errors)}"
    )
    for error in errors:
        print(error)
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
