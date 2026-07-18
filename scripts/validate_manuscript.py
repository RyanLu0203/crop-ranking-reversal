#!/usr/bin/env python3
"""Audit the modular manuscript against verified claims, numbers and assets."""

from __future__ import annotations

import csv
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def csv_rows(path:Path):
    with path.open(newline="",encoding="utf-8") as handle: return list(csv.DictReader(handle))


def tex_tree(entry:Path)->str:
    text=entry.read_text(encoding="utf-8"); base=entry.parent
    for rel in re.findall(r"\\input\{([^}]+)\}",text):
        child=(base/rel).with_suffix(".tex") if not Path(rel).suffix else base/rel
        if child.exists(): text+="\n"+tex_tree(child)
    return text


def main()->None:
    errors=[]; main_text=tex_tree(ROOT/"manuscript/main.tex"); supp_text=tex_tree(ROOT/"supplementary/supplementary.tex"); all_text=main_text+"\n"+supp_text
    required=["Introduction","Related literature","Integrated multi-crop stochastic model","Repaired structural results","Numerical experiments","Data and empirical design","Empirical results","Robustness and extensions","Discussion","Conclusion","Methods"]
    positions=[]
    for section in required:
        token=f"\\section{{{section}}}"
        if token not in main_text: errors.append(f"missing section: {section}")
        else: positions.append(main_text.index(token))
    if positions!=sorted(positions): errors.append("main sections are out of required order")
    bib_keys=set(re.findall(r"^@\w+\{([^,]+),",(ROOT/"references.bib").read_text(),re.M)); cited=set()
    for group in re.findall(r"\\cite[pt]?\{([^}]+)\}",all_text): cited.update(k.strip() for k in group.split(","))
    if cited-bib_keys: errors.append(f"unknown bibliography keys: {sorted(cited-bib_keys)}")
    allowed=set()
    valid={"SUPPORTED","PROVED","PROVED_WITH_RESTRICTION","VERIFIED","VERIFIED_NONHEADLINE","VERIFIED_QUALIFIED","VERIFIED_BOUNDARY"}
    claim_rows=csv_rows(ROOT/"manuscript/registries/claim_citation.csv")
    for row in claim_rows:
        allowed.update(k for k in row["citation_keys"].split(";") if k)
        if row["status"] not in valid: errors.append(f"unresolved claim {row['claim_id']}")
    if cited-allowed: errors.append(f"citations absent from claim registry: {sorted(cited-allowed)}")
    numbers=csv_rows(ROOT/"manuscript/registries/number_output.csv"); macro_text=(ROOT/"manuscript/generated/numbers.tex").read_text()
    if len(numbers)!=27: errors.append(f"expected 27 generated numeric macros, found {len(numbers)}")
    for row in numbers:
        if f"\\newcommand{{\\{row['macro']}}}{{{row['displayed_value']}}}" not in macro_text: errors.append(f"macro mismatch: {row['macro']}")
        if row["verification_status"]!="VERIFIED" or not (ROOT/row["output_file"]).exists(): errors.append(f"number provenance fails: {row['macro']}")
    dispositions=csv_rows(ROOT/"manuscript/registries/draft_completion_disposition.csv")
    if len(dispositions)!=44 or any(r["final_status"]!="CLOSED_ISSUE_9" for r in dispositions): errors.append("teacher-Draft completion matrix is not 44/44 closed")
    usage=csv_rows(ROOT/"manuscript/registries/figure_table_usage.csv")
    if len(usage)!=8: errors.append("figure/table usage registry is incomplete")
    for row in usage:
        if not (ROOT/row["source_path"]).exists(): errors.append(f"missing manuscript asset: {row['source_path']}")
    forbidden=["8,150","42,300","19--34\\%","unique reversal threshold","first formal analysis","CVaR-optimal policy achieves"]
    for phrase in forbidden:
        if phrase.lower() in all_text.lower(): errors.append(f"inadmissible teacher-Draft phrase: {phrase}")
    abstract=(ROOT/"manuscript/sections/abstract.tex").read_text()
    if "UniversalReplications" in abstract or "RiskBindingReplications" in abstract: errors.append("nonheadline simulation result promoted to abstract")
    discussion=(ROOT/"manuscript/sections/discussion.tex").read_text().lower()
    for term in ["not identified","nonheadline","national null"]:
        if term not in discussion: errors.append(f"discussion missing boundary: {term}")
    plain=re.sub(r"\\[A-Za-z]+(?:\[[^]]*\])?\{([^}]*)\}",r"\1",main_text); words=re.findall(r"\b[A-Za-z][A-Za-z'-]*\b",plain)
    supp_plain=re.sub(r"\\[A-Za-z]+(?:\[[^]]*\])?\{([^}]*)\}",r"\1",supp_text); supp_words=re.findall(r"\b[A-Za-z][A-Za-z'-]*\b",supp_plain)
    if len(words)<3500: errors.append(f"main manuscript too short: {len(words)} words")
    if len(supp_words)<1200: errors.append(f"supplement too short: {len(supp_words)} words")
    if errors: raise SystemExit("Manuscript validation failed:\n- "+"\n- ".join(errors))
    print(f"Manuscript validation passed: main_words={len(words)} supplement_words={len(supp_words)} citations={len(cited)} claims={len(claim_rows)} numbers={len(numbers)} completion=44/44")


if __name__=="__main__": main()

