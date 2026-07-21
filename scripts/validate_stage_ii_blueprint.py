#!/usr/bin/env python3
"""Fail-closed acceptance gate for the GOAL-11 Stage II blueprint."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "audits/stage_ii"

REQUIRED = {
    "README.md",
    "scientific_gap_audit.md",
    "theory_gap_matrix.csv",
    "simulation_redesign_plan.md",
    "empirical_expansion_plan.md",
    "figure_blueprint.csv",
    "figure_redesign_plan.md",
    "manuscript_restructuring_roadmap.md",
    "reconstruction_traceability.csv",
    "acceptance_matrix.csv",
}


def read_csv(name: str) -> list[dict[str, str]]:
    with (BASE / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def require_tokens(errors: list[str], name: str, tokens: list[str]) -> None:
    text = (BASE / name).read_text(encoding="utf-8")
    for token in tokens:
        if token not in text:
            errors.append(f"missing_token:{name}:{token}")


def main() -> None:
    errors: list[str] = []
    for name in sorted(REQUIRED):
        if not (BASE / name).is_file():
            errors.append(f"missing_file:{name}")

    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)

    theory = read_csv("theory_gap_matrix.csv")
    figures = read_csv("figure_blueprint.csv")
    trace = read_csv("reconstruction_traceability.csv")
    acceptance = read_csv("acceptance_matrix.csv")

    theory_fields = {
        "gap_id", "research_question", "stage_i_anchor", "stage_i_status",
        "stage_ii_target", "allowed_result_class", "simulation_requirement",
        "empirical_requirement", "owner_issue", "acceptance_gate",
        "manuscript_destination", "priority",
    }
    figure_fields = {
        "figure_id", "scientific_question", "core_conclusion", "archetype",
        "hero_panel", "supporting_panels", "required_source_data",
        "statistics_and_uncertainty", "evidence_gate", "reviewer_risk",
        "planned_location", "owner_issue", "status",
    }
    trace_fields = {
        "question_id", "canonical_question", "positive_claim_target",
        "theory_requirement", "confirmatory_simulation", "empirical_relevance",
        "main_figure", "manuscript_sections", "owner_sequence", "claim_gate",
    }
    acceptance_fields = {
        "requirement_id", "source_requirement", "evidence_file",
        "verification_rule", "status", "notes",
    }

    for label, rows, expected in [
        ("theory", theory, theory_fields),
        ("figures", figures, figure_fields),
        ("trace", trace, trace_fields),
        ("acceptance", acceptance, acceptance_fields),
    ]:
        actual = set(rows[0]) if rows else set()
        if actual != expected:
            errors.append(f"schema:{label}:missing={sorted(expected-actual)}:extra={sorted(actual-expected)}")
        ids = [next(iter(row.values())) for row in rows]
        if len(ids) != len(set(ids)):
            errors.append(f"duplicate_ids:{label}")
        for index, row in enumerate(rows, 1):
            if None in row:
                errors.append(f"extra_csv_fields:{label}:{index}:{row[None]}")
            if any(not isinstance(value, str) or not value.strip() for key, value in row.items() if key is not None):
                errors.append(f"blank_field:{label}:{index}")

    if len(theory) < 10:
        errors.append(f"too_few_theory_gaps:{len(theory)}")
    if {row["priority"] for row in theory} - {"P0", "P1"}:
        errors.append("invalid_theory_priority")
    theory_owners = {owner for row in theory for owner in row["owner_issue"].split(";")}
    if theory_owners - {"22", "24", "25"}:
        errors.append("invalid_theory_owner_issue")

    if {row["figure_id"] for row in figures} != {f"F{i}" for i in range(1, 7)}:
        errors.append("figure_set_not_F1_to_F6")
    if any(row["owner_issue"] != "23" for row in figures):
        errors.append("figure_owner_not_issue_23")
    if any(not row["status"].startswith("BLOCKED_PENDING_") for row in figures):
        errors.append("figure_generated_before_evidence_gate")

    if {row["question_id"] for row in trace} != {f"Q{i}" for i in range(1, 6)}:
        errors.append("research_question_set_not_Q1_to_Q5")
    if any(row["owner_sequence"] != "24>22>23>25" for row in trace):
        errors.append("phase_order_violation")

    expected_requirements = {f"G11-{i:02d}" for i in range(1, 15)}
    if {row["requirement_id"] for row in acceptance} != expected_requirements:
        errors.append("acceptance_requirement_set_mismatch")
    if any(row["status"] != "COMPLETE" for row in acceptance):
        errors.append("acceptance_item_not_complete")

    require_tokens(errors, "README.md", [
        "4d6c14d48b6eb76cf0612c837341d3ee2afbf0d0",
        "codex/issue-21-stage-ii-blueprint", "Active issue: #21 only",
        "GOAL-14 / Issue #24", "GOAL-12 / Issue #22",
        "GOAL-13 / Issue #23", "GOAL-15 / Issue #25",
    ])
    require_tokens(errors, "scientific_gap_audit.md", [
        "450 primary", "zero of", "five convergence rows passed", "77 complete state-years",
        "Historical thresholds", "figure cannot precede validated source data",
    ])
    require_tokens(errors, "simulation_redesign_plan.md", [
        "M0 — ordinal recommendation", "M4 — dependence specification",
        "E1 — Ordinal versus cardinal", "E7 — Global robustness",
        "confidence-controlled stopping", "Promotion gates",
    ])
    require_tokens(errors, "empirical_expansion_plan.md", [
        "Directly observed", "Model generated", "Unidentified",
        "Acreage transitions", "rolling-origin", "Identification ladder",
        "Promotion gates",
    ])
    require_tokens(errors, "figure_redesign_plan.md", [
        "183 mm", "maximum height 170 mm", "5--7 pt", "editable",
        "Figure 1", "Figure 6", "Source-data and QA gate",
    ])
    require_tokens(errors, "manuscript_restructuring_roadmap.md", [
        "### 1. Introduction", "### 2. Conceptual framework",
        "### 3. Stochastic optimization model", "### 4. Ranking reversal mechanisms",
        "### 5. Numerical experiments", "### 6. Empirical validation",
        "### 7. Information and flexibility implications", "### 8. Discussion",
        "### 9. Conclusion", "Final reconstruction gate",
    ])

    print(
        f"stage_ii_files={len(REQUIRED)} theory_gaps={len(theory)} "
        f"research_questions={len(trace)} figure_groups={len(figures)} "
        f"acceptance_items={len(acceptance)} failures={len(errors)}"
    )
    for error in errors:
        print(error)
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
