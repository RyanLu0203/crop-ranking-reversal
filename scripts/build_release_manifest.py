#!/usr/bin/env python3
"""Create a checksum manifest for the Stage II final scientific package."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()


def main()->None:
    paths=[]
    for pattern in ["output/pdf/*.pdf","output/logs/*.txt","output/qa/*.png","output/qa/*.json","output/*.md","audits/first_compile_qa.md","audits/final_claim_evidence_audit.md","audits/visual_page_review.md","audits/stage_ii_final_claim_evidence.csv","audits/goal16_*.md","audits/goal16_visual_comparison/*"]:
        paths.extend(ROOT.glob(pattern))
    paths=sorted(set(p for p in paths if p.is_file()))
    role=lambda p: "review_pdf" if p.suffix==".pdf" else "compile_log" if "logs" in p.parts else "page_qa" if "qa" in p.parts else "review_documentation"
    rows=[{"path":str(p.relative_to(ROOT)),"sha256":sha(p),"bytes":p.stat().st_size,"role":role(p)} for p in paths]
    out=ROOT/"output/reproducibility/package_manifest.csv"
    with out.open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=rows[0].keys(),lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    ledger_paths=paths+[out,ROOT/"output/reproducibility/build_environment.json",ROOT/"output/reproducibility/build_report.json"]
    (ROOT/"output/reproducibility/SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(ROOT)}\n" for p in sorted(set(ledger_paths))))
    print(f"release_manifest_rows={len(rows)} checksum_rows={len(set(ledger_paths))}")


if __name__=="__main__": main()
