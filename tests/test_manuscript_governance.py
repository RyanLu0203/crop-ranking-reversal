import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def rows(path):
    with path.open(newline="",encoding="utf-8") as handle: return list(csv.DictReader(handle))


def test_teacher_draft_completion_is_closed():
    data=rows(ROOT/"manuscript/registries/draft_completion_disposition.csv")
    assert len(data)==44
    assert {r["final_status"] for r in data}=={"CLOSED_STAGE_II"}


def test_simulation_promotion_obeys_stage_ii_gate():
    data=rows(ROOT/"manuscript/registries/claim_citation.csv")
    by_id={r["claim_id"]:r for r in data}
    assert by_id["S2MC-11"]["status"]=="VERIFIED"
    assert by_id["S2MC-12"]["status"]=="VERIFIED"
    assert by_id["S2MC-13"]["status"]=="VERIFIED"
    assert by_id["S2MC-14"]["status"]=="VERIFIED_NONHEADLINE"
    assert "E1 E3 E4 and E5" in by_id["S2MC-14"]["claim_summary"]


def test_author_owned_metadata_is_explicit():
    assert "to be confirmed" in (ROOT/"manuscript/frontmatter/title_page.tex").read_text()
    assert "authors must confirm" in (ROOT/"manuscript/frontmatter/declarations.tex").read_text()
