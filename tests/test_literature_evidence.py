"""Regression checks for the Issue #3 literature evidence contract."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _rows(relative: str):
    with (ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_every_canonical_reference_is_full_text_verified():
    rows = _rows("evidence_registry/literature_registry.csv")
    assert len(rows) >= 19
    assert all(row["full_text_verified"] == "YES" for row in rows)
    assert all(row["doi"].startswith("10.") for row in rows)


def test_canonical_dois_are_unique_case_insensitively():
    dois = [row["doi"].lower() for row in _rows(
        "evidence_registry/literature_registry.csv"
    )]
    assert len(dois) == len(set(dois))


def test_quality_matrix_documents_inclusion_and_exclusion():
    rows = _rows("audits/literature_quality_matrix.csv")
    assert sum(row["included"] == "YES" for row in rows) >= 19
    assert sum(row["included"] == "NO" for row in rows) >= 10
    assert all(
        row["exclusion_reason"]
        for row in rows
        if row["included"] == "NO"
    )


def test_novelty_matrix_contains_closest_cvar_crop_predecessor():
    rows = _rows("audits/novelty_comparison_matrix.csv")
    closest = next(row for row in rows if row["citation_key"] == "filippi2017mixed")
    assert closest["crop_or_agriculture"] == "YES"
    assert closest["loss_cvar"] == "YES"
    assert closest["solution_set_reversal"] == "NO"


def test_literature_claims_are_qualified_and_source_backed():
    claims = [
        row for row in _rows("evidence_registry/claims.csv")
        if row["claim_id"].startswith("LIT-C")
    ]
    assert {row["claim_id"] for row in claims} == {
        f"LIT-C{i:02d}" for i in range(1, 12)
    }
    assert all(row["supporting_assets"] for row in claims)
    assert all(row["qualification_required"] == "YES" for row in claims)
