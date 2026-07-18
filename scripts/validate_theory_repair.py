#!/usr/bin/env python3
"""Acceptance gate for Issue #2's canonical repaired theory package."""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPAIRED = ROOT / "theory/repaired"
REQUIRED = {
    "README.md",
    "canonical_theorem_set.md",
    "canonical_theorem_set.tex",
    "proofs.md",
    "assumptions_definitions_notation_crosswalk.csv",
    "theorem_transition_registry.csv",
    "theory_to_simulation_map.csv",
    "theory_to_empirical_map.csv",
    "supervisor_memo_en.md",
    "supervisor_memo_zh.md",
    "method_source_verification.md",
}
REQUIRED_REVERSAL_TERMS = {
    "possible reversal",
    "universal reversal",
    "selected reversal",
    "pairwise reversal",
    "top-rank reversal",
    "strong reversal",
}
REQUIRED_CROSSWALK_OBJECTS = {
    "Portfolio loss",
    "Operational feasible set",
    "CVaR",
    "Optimal solution set",
    "Land dual",
    "Budget dual",
    "Shared-constraint duals",
    "Bound duals",
    "Risk dual",
    "Crossing set",
    "Value of information",
}


def rows(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


errors: list[str] = []
for name in sorted(REQUIRED):
    if not (REPAIRED / name).is_file():
        errors.append(f"missing:{name}")

canonical = (REPAIRED / "canonical_theorem_set.md").read_text(encoding="utf-8")
proofs = (REPAIRED / "proofs.md").read_text(encoding="utf-8")
for number in range(1, 11):
    result_id = f"CT{number}"
    if result_id not in canonical:
        errors.append(f"missing_canonical_result:{result_id}")
    if f"Proof of {result_id}" not in proofs:
        errors.append(f"missing_proof:{result_id}")

canonical_lower = canonical.lower()
for term in sorted(REQUIRED_REVERSAL_TERMS):
    if term not in canonical_lower:
        errors.append(f"missing_reversal_definition:{term}")

for forbidden in (
    "if and only if acreage ranking reversal",
    "tail-dependence coefficient monotonically raises",
    "a unique reversal threshold exists",
    "strictly increasing and supermodular",
    "gap_ij",
):
    if forbidden in canonical_lower:
        errors.append(f"forbidden_general_claim:{forbidden}")

transition = rows("theory/repaired/theorem_transition_registry.csv")
actual_ids = [row["draft_result_id"] for row in transition]
expected_ids = [f"R{i:02d}" for i in range(1, 32)]
if sorted(actual_ids) != expected_ids:
    errors.append("transition_registry_must_cover_R01_R31_exactly_once")
if any(not row["transition"].strip() or not row["canonical_status"].strip() for row in transition):
    errors.append("empty_transition_disposition")

crosswalk = rows("theory/repaired/assumptions_definitions_notation_crosswalk.csv")
objects = {row["draft_object"] for row in crosswalk}
for item in sorted(REQUIRED_CROSSWALK_OBJECTS - objects):
    errors.append(f"missing_crosswalk_object:{item}")

for map_name in ("theory_to_simulation_map.csv", "theory_to_empirical_map.csv"):
    mapped = rows(f"theory/repaired/{map_name}")
    mapped_ids = {row["theory_result_id"] for row in mapped}
    if mapped_ids != {f"CT{i}" for i in range(1, 11)}:
        errors.append(f"incomplete_map:{map_name}")

literature = rows("evidence_registry/literature_registry.csv")
theory_sources = [row for row in literature if row["reference_id"].startswith("LIT-THEORY-")]
if len(theory_sources) < 3:
    errors.append("insufficient_full_text_theory_sources")
for row in theory_sources:
    if row["full_text_verified"] != "YES":
        errors.append(f"unverified_full_text:{row['reference_id']}")
    if row["citation_status"] != "THEORY_FOUNDATION_ONLY":
        errors.append(f"invalid_theory_source_role:{row['reference_id']}")
    if not re.fullmatch(r"10\.\S+", row["doi"]):
        errors.append(f"missing_doi:{row['reference_id']}")

print(
    f"repaired_files={len(REQUIRED)} canonical_results=10 "
    f"transitions={len(transition)} crosswalk_rows={len(crosswalk)} "
    f"theory_sources={len(theory_sources)} failures={len(errors)}"
)
for error in errors:
    print(error)
raise SystemExit(bool(errors))
