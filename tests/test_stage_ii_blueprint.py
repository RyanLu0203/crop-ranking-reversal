import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "audits/stage_ii"


def read_rows(name: str):
    with (BASE / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_five_research_questions_have_end_to_end_traceability():
    rows = read_rows("reconstruction_traceability.csv")
    assert {row["question_id"] for row in rows} == {"Q1", "Q2", "Q3", "Q4", "Q5"}
    assert all(row["theory_requirement"] and row["confirmatory_simulation"] for row in rows)
    assert all(row["empirical_relevance"] and row["claim_gate"] for row in rows)


def test_six_main_figures_are_blocked_on_scientific_evidence():
    rows = read_rows("figure_blueprint.csv")
    assert {row["figure_id"] for row in rows} == {f"F{i}" for i in range(1, 7)}
    assert all(row["status"].startswith("BLOCKED_PENDING_") for row in rows)
    assert all(row["required_source_data"] and row["evidence_gate"] for row in rows)


def test_goal_11_acceptance_matrix_is_complete_and_bounded():
    rows = read_rows("acceptance_matrix.csv")
    assert {row["requirement_id"] for row in rows} == {f"G11-{i:02d}" for i in range(1, 15)}
    assert all(row["status"] == "COMPLETE" for row in rows)
    roadmap = (BASE / "manuscript_restructuring_roadmap.md").read_text()
    assert "not a manuscript rewrite" in roadmap
    assert "GOAL-14" in roadmap and "GOAL-12" in roadmap and "GOAL-15" in roadmap
