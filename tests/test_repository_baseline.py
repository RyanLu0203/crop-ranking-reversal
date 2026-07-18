import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "baselines/teacher_draft/Crop_ranking_reversal_total.tex": "e8885aa89be6a6010f0d3e6f8e40b4b8192a91fc90f6ca4fb16ae9b0aa9dd26c",
    "baselines/teacher_draft/Crop_ranking_reversal_total.pdf": "52ac1b4ef21c8d406fd6d722c877935a24d2cc6ea68520a6f35470ba8b334b44",
}


def test_teacher_baseline_hashes_are_immutable():
    for relative, expected in EXPECTED.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected


def test_draft_completion_matrix_has_no_unmapped_major_item():
    with (ROOT / "audits/draft_content_completion_matrix.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) >= 40
    assert len({row["content_id"] for row in rows}) == len(rows)
    assert all(row["canonical_disposition"] for row in rows)
    assert all(row["target_issue_ids"] or row["supervisor_confirmation_required"] == "YES" for row in rows)


def test_no_number_is_admitted_in_issue_one():
    with (ROOT / "evidence_registry/numbers.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == []
