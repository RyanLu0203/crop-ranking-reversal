import json
import csv
import re
from pathlib import Path
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]


def test_final_build_is_byte_stable():
    report=json.loads((ROOT/"output/reproducibility/build_report.json").read_text())
    assert all(item["byte_stable"] for item in report.values())
    assert all(item["sha256"]==item["repeat_sha256"] for item in report.values())


def test_all_final_pages_were_rendered():
    metrics=json.loads((ROOT/"output/qa/page_metrics.json").read_text())
    pdfs=list((ROOT/"output/pdf").glob("*.pdf"))
    assert len(pdfs)==2
    assert len(metrics)==sum(len(PdfReader(str(path)).pages) for path in pdfs)
    assert not any(row["blank"] for row in metrics)


def test_package_is_review_not_submission_labelled():
    text=(ROOT/"output/SUPERVISOR_REVIEW_README.md").read_text()
    assert "closes the authorized Stage II reconstruction" in text
    assert "not a journal-submission archive" in text


def test_exported_compile_records_are_portable():
    paths=list((ROOT/"output/logs").glob("*_compile.txt"))
    assert len(paths)==2
    for path in paths:
        text=path.read_text()
        assert str(ROOT) not in text
        assert "/private/tmp/" not in text
        assert "diagnostic_scan=PASS" in text
        assert "byte_stable=YES" in text


def test_canonical_manifest_excludes_transient_and_collision_paths():
    with (ROOT/"provenance/canonical_asset_manifest.csv").open(newline="") as handle:
        rows=list(csv.DictReader(handle))
    paths=[Path(row["canonical_path"]) for row in rows]
    assert not any(path.parts[0] in {"build","dist","scratch","tmp"} for path in paths)
    assert not any(re.search(r" \d+$", path.stem) for path in paths)
