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


def test_simulation_numbers_preserve_design_dry_run_and_nonheadline_boundaries():
    with (ROOT / "evidence_registry/numbers.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert all(row["number_id"].startswith("NUM-SIM-") for row in rows)
    allowed = {
        "VERIFIED_DESIGN_ONLY", "VERIFIED_RESOURCE_PLAN", "DRY_RUN_ONLY",
        "FORMAL_VERIFIED_NONHEADLINE", "FORMAL_RESULT_NONHEADLINE",
        "REPRODUCIBILITY_VERIFIED", "ADVERSE_RESULT_VERIFIED", "RESOURCE_CAP_VERIFIED",
    }
    assert all(row["verification_status"] in allowed for row in rows)
    formal_results = [row for row in rows if row["verification_status"] == "FORMAL_RESULT_NONHEADLINE"]
    assert formal_results
    assert all("Supplementary" in row["manuscript_location"] for row in formal_results)
