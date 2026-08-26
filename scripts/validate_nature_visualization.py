#!/usr/bin/env python3
"""Validate Issue 8 figure provenance, exports, registries and claim boundaries."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re

import yaml
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
FIGURES={"Figure1":("main",183,120),"Figure2":("main",183,150),"FigureS1":("supplementary",183,140),"FigureS2":("supplementary",183,105),"FigureS3":("supplementary",183,120)}


def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path:Path)->list[dict[str,str]]:
    with path.open(newline="",encoding="utf-8") as handle: return list(csv.DictReader(handle))


def main()->None:
    errors=[]
    config=yaml.safe_load((ROOT/"visualization/configs/nature_style.yaml").read_text())
    fixed={v.upper() for k,v in config["palette"].items() if k!="paper"}
    qa_by={r["figure_id"]:r for r in json.loads((ROOT/"visualization/qa/visual_regression.json").read_text())}
    for fid,(loc,wmm,hmm) in FIGURES.items():
        stem=ROOT/"figures"/loc/fid
        for ext in ["svg","pdf","png","tiff"]:
            p=stem.with_suffix("."+ext)
            if not p.exists() or p.stat().st_size==0: errors.append(f"missing export: {p.relative_to(ROOT)}")
        svg=stem.with_suffix(".svg").read_text(encoding="utf-8")
        if "<text" not in svg or "<image" in svg: errors.append(f"{fid}: SVG must contain editable text and no embedded raster")
        if "DejaVu Sans" not in svg and "Arial" not in svg: errors.append(f"{fid}: mandatory sans-serif font not recorded")
        prohibited={"#e41a1c","#377eb8","#4daf4a","#984ea3","#ff7f00","#ffff33"}
        hexes={h.lower() for h in re.findall(r"#[0-9A-Fa-f]{6}",svg)}
        if hexes & prohibited: errors.append(f"{fid}: prohibited palette color(s) {sorted(hexes & prohibited)}")
        for ext,dpi in [("png",300),("tiff",600)]:
            im=Image.open(stem.with_suffix("."+ext)); expected=(round(wmm/25.4*dpi),round(hmm/25.4*dpi))
            if any(abs(a-b)>1 for a,b in zip(im.size,expected)): errors.append(f"{fid}.{ext}: {im.size} != {expected}")
        if not qa_by.get(fid,{}).get("size_pass") or not qa_by.get(fid,{}).get("svg_editable_text"): errors.append(f"{fid}: visual-regression record fails")
        if not (ROOT/"visualization/qa"/f"{fid}_grayscale.png").exists(): errors.append(f"{fid}: grayscale proof missing")

    for ledger_path in [ROOT/"figures/SHA256SUMS",ROOT/"tables/SHA256SUMS",ROOT/"visualization/source_data/SHA256SUMS"]:
        for line in ledger_path.read_text().splitlines():
            digest,rel=line.split("  ",1); target=ROOT/rel
            if not target.exists() or sha(target)!=digest: errors.append(f"checksum mismatch: {rel}")
    for row in rows(ROOT/"visualization/source_data/lineage.csv"):
        src=ROOT/row["source_data"]; upstream=ROOT/row["upstream_input"]
        if sha(src)!=row["source_sha256"]: errors.append(f"source lineage mismatch: {src}")
        if upstream.exists() and sha(upstream)!=row["upstream_sha256"]: errors.append(f"upstream lineage mismatch: {upstream}")

    # Stage I and versioned Stage II figures share the registry. This validator
    # owns only the original Stage I identifiers; Stage II has its own fail-closed
    # validator and prefixed identifiers.
    fig_registry=[r for r in rows(ROOT/"evidence_registry/figures.csv") if r["figure_id"] in FIGURES]
    if {r["figure_id"] for r in fig_registry}!=set(FIGURES): errors.append("Stage I figure registry is incomplete")
    for row in fig_registry:
        if sha(ROOT/f"figures/{row['manuscript_location']}/{row['figure_id']}.svg")!=row["checksum"]: errors.append(f"registry checksum mismatch: {row['figure_id']}")
        if row["figure_id"] in {"FigureS1","FigureS2"} and row["evidence_status"]!="NONHEADLINE": errors.append(f"{row['figure_id']}: simulation must remain NONHEADLINE")
    table_registry=rows(ROOT/"evidence_registry/tables.csv")
    if {r["table_id"] for r in table_registry}!={"Table1","TableS1","TableS2"}: errors.append("table registry is incomplete")
    if next(r for r in table_registry if r["table_id"]=="TableS1")["evidence_status"]!="NONHEADLINE": errors.append("TableS1 must remain NONHEADLINE")
    captions=rows(ROOT/"visualization/captions.csv")
    if {r["figure_id"] for r in captions}!=set(FIGURES): errors.append("caption registry is incomplete")
    convergence=rows(ROOT/"visualization/source_data/convergence_summary.csv")
    if len(convergence)!=5 or any(r["convergence_pass"].lower()!="false" for r in convergence): errors.append("frozen 0/5 convergence boundary changed")
    claims={r["claim_domain"]:r["status"] for r in rows(ROOT/"visualization/source_data/claim_boundaries.csv")}
    for domain in ["observed acreage optimality","CVaR binding or causality","copula mechanism"]:
        if claims.get(domain)!="NOT_IDENTIFIED": errors.append(f"claim boundary changed: {domain}")
    access=json.loads((ROOT/"visualization/qa/accessibility.json").read_text())
    if access.get("status")!="PASS" or set(access.get("palette",{}).values())!=fixed: errors.append("accessibility/palette record fails")
    if errors: raise SystemExit("Nature visualization validation failed:\n- "+"\n- ".join(errors))
    print("Nature visualization validation passed: 5 figures, 3 tables, editable vectors, raster DPI, lineage, checksums and claim gates verified.")


if __name__=="__main__": main()
