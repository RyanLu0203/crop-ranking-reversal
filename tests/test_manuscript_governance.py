import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def rows(path):
    with path.open(newline="",encoding="utf-8") as handle: return list(csv.DictReader(handle))


def test_teacher_draft_completion_is_closed():
    data=rows(ROOT/"manuscript/registries/draft_completion_disposition.csv")
    assert len(data)==44
    assert {r["final_status"] for r in data}=={"CLOSED_ISSUE_9"}


def test_simulation_claims_remain_nonheadline():
    data=rows(ROOT/"manuscript/registries/claim_citation.csv")
    assert next(r for r in data if r["claim_id"]=="MC-11")["status"]=="VERIFIED_NONHEADLINE"


def test_author_owned_metadata_is_explicit():
    assert "to be confirmed" in (ROOT/"manuscript/frontmatter/title_page.tex").read_text()
    assert "authors must confirm" in (ROOT/"manuscript/frontmatter/declarations.tex").read_text()

