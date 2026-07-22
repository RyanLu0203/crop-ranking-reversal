#!/usr/bin/env python3
"""Audit the Stage II manuscript against claims, numbers and assets."""

from __future__ import annotations

import csv
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def tex_tree(entry: Path) -> str:
    text = entry.read_text(encoding="utf-8")
    base = entry.parent
    for rel in re.findall(r"\\input\{([^}]+)\}", text):
        child = base / rel
        if not child.suffix:
            child = child.with_suffix(".tex")
        if child.exists():
            text += "\n" + tex_tree(child)
    return text


def main() -> None:
    errors: list[str] = []
    main_text = tex_tree(ROOT / "manuscript/main.tex")
    supp_text = tex_tree(ROOT / "supplementary/supplementary.tex")
    all_text = main_text + "\n" + supp_text

    required = [
        "Introduction", "Ranking does not identify allocation",
        "Operational constraints identify reversal",
        "Information value depends on available actions",
        "Empirical patterns are definition-dependent", "Discussion", "Conclusion", "Methods",
    ]
    positions = []
    for section in required:
        token = f"\\section{{{section}}}"
        if token not in main_text:
            errors.append(f"missing section: {section}")
        else:
            positions.append(main_text.index(token))
    if positions != sorted(positions):
        errors.append("main sections are out of required order")

    bib_keys = set(re.findall(r"^@\w+\{([^,]+),", (ROOT / "references.bib").read_text(), re.M))
    cited: set[str] = set()
    for group in re.findall(r"\\cite[pt]?\{([^}]+)\}", all_text):
        cited.update(k.strip() for k in group.split(","))
    if cited - bib_keys:
        errors.append(f"unknown bibliography keys: {sorted(cited - bib_keys)}")

    allowed: set[str] = set()
    valid = {"SUPPORTED", "PROVED", "PROVED_WITH_RESTRICTION", "VERIFIED", "VERIFIED_NONHEADLINE", "VERIFIED_QUALIFIED", "VERIFIED_BOUNDARY"}
    claim_rows = csv_rows(ROOT / "manuscript/registries/claim_citation.csv")
    if len(claim_rows) < 20:
        errors.append("Stage II claim registry is incomplete")
    for row in claim_rows:
        allowed.update(k for k in row["citation_keys"].split(";") if k)
        if row["status"] not in valid:
            errors.append(f"unresolved claim {row['claim_id']}")
        for asset in row["evidence_assets"].split(";"):
            if asset and not (ROOT / asset).exists():
                errors.append(f"missing claim evidence: {asset}")
    if cited - allowed:
        errors.append(f"citations absent from claim registry: {sorted(cited - allowed)}")

    numbers = csv_rows(ROOT / "manuscript/registries/number_output.csv")
    macro_text = (ROOT / "manuscript/generated/numbers.tex").read_text()
    if len(numbers) < 45:
        errors.append(f"expected at least 45 Stage II numeric macros, found {len(numbers)}")
    for row in numbers:
        if f"\\newcommand{{\\{row['macro']}}}{{{row['displayed_value']}}}" not in macro_text:
            errors.append(f"macro mismatch: {row['macro']}")
        if row["verification_status"] != "VERIFIED" or not (ROOT / row["output_file"]).exists():
            errors.append(f"number provenance fails: {row['macro']}")

    dispositions = csv_rows(ROOT / "manuscript/registries/draft_completion_disposition.csv")
    if len(dispositions) != 44 or any(r["final_status"] != "CLOSED_STAGE_II" for r in dispositions):
        errors.append("teacher-Draft completion matrix is not 44/44 closed for Stage II")

    usage = csv_rows(ROOT / "manuscript/registries/figure_table_usage.csv")
    expected_assets = {f"Figure{i}" for i in range(1, 7)} | {f"FigureS{i}" for i in range(1, 8)}
    if {row["asset_id"] for row in usage} != expected_assets:
        errors.append("figure usage registry must contain six main and seven supplementary figures")
    for row in usage:
        if not (ROOT / row["source_path"]).exists():
            errors.append(f"missing manuscript asset: {row['source_path']}")
        if not (ROOT / row["source_registry"]).exists():
            errors.append(f"missing source registry: {row['source_registry']}")

    for i in range(1, 7):
        if f"../figures/goal17/main/Figure{i}.pdf" not in main_text:
            errors.append(f"main manuscript does not include GOAL-17 Figure{i}")
    for i in range(1, 6):
        if f"../figures/stage_ii/supplementary/FigureS{i}.pdf" not in supp_text:
            errors.append(f"supplement does not include Stage II FigureS{i}")
    for i in range(6, 8):
        if f"../figures/goal17/supplementary/FigureS{i}.pdf" not in supp_text:
            errors.append(f"supplement does not include GOAL-17 FigureS{i}")

    forbidden = ["8,150", "42,300", "19--34\\%", "unique reversal threshold", "CVaR-optimal policy achieves"]
    for phrase in forbidden:
        if phrase.lower() in all_text.lower():
            errors.append(f"inadmissible teacher-Draft phrase: {phrase}")

    abstract = (ROOT / "manuscript/sections/abstract.tex").read_text()
    if "Four other pre-specified experiments do not meet" not in abstract:
        errors.append("abstract must retain the failed-experiment boundary")
    for token in ["EtwoPassedIntervals", "EsixPositive", "OperatingInversion"]:
        if token not in abstract:
            errors.append(f"abstract missing promoted Stage II result: {token}")

    discussion = (ROOT / "manuscript/sections/discussion.tex").read_text().lower()
    for term in ["cannot identify", "inconclusive", "welfare", "private"]:
        if term not in discussion:
            errors.append(f"discussion missing boundary: {term}")

    plain = re.sub(r"\\[A-Za-z]+(?:\[[^]]*\])?\{([^}]*)\}", r"\1", main_text)
    words = re.findall(r"\b[A-Za-z][A-Za-z'-]*\b", plain)
    supp_plain = re.sub(r"\\[A-Za-z]+(?:\[[^]]*\])?\{([^}]*)\}", r"\1", supp_text)
    supp_words = re.findall(r"\b[A-Za-z][A-Za-z'-]*\b", supp_plain)
    if len(words) < 2800:
        errors.append(f"main manuscript too short: {len(words)} words")
    if len(supp_words) < 2000:
        errors.append(f"supplement too short: {len(supp_words)} words")

    if errors:
        raise SystemExit("Manuscript validation failed:\n- " + "\n- ".join(errors))
    print(f"Manuscript validation passed: main_words={len(words)} supplement_words={len(supp_words)} citations={len(cited)} claims={len(claim_rows)} numbers={len(numbers)} figures=13 completion=44/44")


if __name__ == "__main__":
    main()
