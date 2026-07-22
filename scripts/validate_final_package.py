#!/usr/bin/env python3
"""Validate Stage II PDFs, page QA, checksums and evidence closure."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]


def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path:Path):
    with path.open(newline="",encoding="utf-8") as handle: return list(csv.DictReader(handle))


def fonts_embedded(reader:PdfReader)->bool:
    for page in reader.pages:
        resources=page.get("/Resources",{}).get_object()
        fonts=resources.get("/Font",{}).get_object()
        for ref in fonts.values():
            font=ref.get_object()
            if font.get("/Subtype")=="/Type3": continue
            descriptor=font.get("/FontDescriptor")
            if descriptor is None: return False
            desc=descriptor.get_object()
            if not any(key in desc for key in ["/FontFile","/FontFile2","/FontFile3"]): return False
    return True


def main()->None:
    errors=[]
    pdfs={"main":(ROOT/"output/pdf/crop_ranking_reversal_main_supervisor_review.pdf","manuscript"),"supplementary":(ROOT/"output/pdf/crop_ranking_reversal_supplementary_supervisor_review.pdf","supplementary")}
    report=json.loads((ROOT/"output/reproducibility/build_report.json").read_text())
    page_counts={}
    for label,(pdf,report_key) in pdfs.items():
        if not pdf.exists(): errors.append(f"missing {label} PDF"); continue
        reader=PdfReader(str(pdf))
        page_counts[label]=len(reader.pages)
        if len(reader.pages)<5: errors.append(f"{label}: unexpectedly short PDF")
        if "Stage II final scientific draft" not in str(reader.metadata.get("/Subject","")): errors.append(f"{label}: Stage II metadata missing")
        if report[report_key]["sha256"]!=sha(pdf) or not report[report_key]["byte_stable"]: errors.append(f"{label}: deterministic build report fails")
        text="\n".join(page.extract_text() or "" for page in reader.pages)
        if "??" in text: errors.append(f"{label}: unresolved reference token in extracted text")
        if not fonts_embedded(reader): errors.append(f"{label}: unembedded font detected")
    prohibited=["undefined citations","undefined references","Citation `","Reference `","Overfull \\hbox","Overfull \\vbox","LaTeX Error","Fatal error"]
    for log in (ROOT/"output/logs").glob("*.txt"):
        text=log.read_text(errors="replace")
        for token in prohibited:
            if token in text: errors.append(f"{log.name}: {token}")
    metrics=json.loads((ROOT/"output/qa/page_metrics.json").read_text())
    expected_pages=sum(page_counts.values())
    if len(metrics)!=expected_pages or any(r["blank"] for r in metrics): errors.append(f"page rendering must cover {expected_pages} nonblank pages")
    expected_contacts=sum((count+3)//4 for count in page_counts.values())
    if len(list((ROOT/"output/qa").glob("contact_*.png")))!=expected_contacts: errors.append(f"expected {expected_contacts} page-review contact sheets")
    manifest=rows(ROOT/"output/reproducibility/package_manifest.csv")
    if len(manifest)<12: errors.append("release manifest is incomplete")
    for row in manifest:
        p=ROOT/row["path"]
        if not p.exists() or sha(p)!=row["sha256"] or p.stat().st_size!=int(row["bytes"]): errors.append(f"release manifest mismatch: {row['path']}")
    for line in (ROOT/"output/reproducibility/SHA256SUMS").read_text().splitlines():
        digest,rel=line.split("  ",1); p=ROOT/rel
        if not p.exists() or sha(p)!=digest: errors.append(f"release checksum mismatch: {rel}")
    acceptance=["audits/issue_1_acceptance_report.md","audits/issue_2_theory_acceptance_report.md","audits/issue_3_literature_acceptance_report.md","audits/issue_4_data_acceptance_report.md","audits/issue_5_acceptance_report.md","audits/issue_6_acceptance_report.md","audits/issue_7_acceptance_report.md","audits/nature_visual_qa.md","audits/manuscript_claim_audit.md","audits/first_compile_qa.md","audits/final_claim_evidence_audit.md","audits/visual_page_review.md"]
    for rel in acceptance:
        if not (ROOT/rel).exists(): errors.append(f"missing milestone audit: {rel}")
    readme=(ROOT/"output/SUPERVISOR_REVIEW_README.md").read_text()
    if "not a journal-submission archive" not in readme or "make paper" not in readme: errors.append("Stage II README boundary/build command missing")
    usage=rows(ROOT/"manuscript/registries/figure_table_usage.csv")
    if len(usage)!=10: errors.append("Stage II figure-use registry must contain ten figures")
    if not (ROOT/"audits/stage_ii_final_claim_evidence.csv").exists(): errors.append("missing Stage II claim-evidence lineage")
    archive=ROOT/"output/stage_ii_final_scientific_package.zip"
    archive_sum=ROOT/"output/stage_ii_final_scientific_package.zip.sha256"
    if not archive.exists() or not archive_sum.exists():
        errors.append("missing Stage II final archive or checksum")
    else:
        digest,name=archive_sum.read_text().strip().split("  ",1)
        if name!=archive.name or digest!=sha(archive): errors.append("Stage II archive checksum mismatch")
        with zipfile.ZipFile(archive) as zf:
            names=set(zf.namelist())
            required={"PACKAGE_MANIFEST.csv","manuscript/main.tex","supplementary/supplementary.tex","figures/stage_ii/main/Figure6.pdf","figures/stage_ii/supplementary/FigureS4.pdf","visualization/stage_ii/source_data/figure6_stage2_transition_summary.csv","audits/stage_ii_final_claim_evidence.csv"}
            if required-names: errors.append(f"Stage II archive missing entries: {sorted(required-names)}")
    if len((ROOT/"output/remaining_actions.md").read_text().splitlines())<10: errors.append("remaining-actions list is incomplete")
    if errors: raise SystemExit("Final package validation failed:\n- "+"\n- ".join(errors))
    print(f"Final package validation passed: pdfs=2 pages={expected_pages} logs=2 contacts={expected_contacts} release_rows={len(manifest)} figures=10 milestone_audits={len(acceptance)}")


if __name__=="__main__": main()
