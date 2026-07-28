#!/usr/bin/env python3
"""Render every final PDF page and create review contact sheets and metrics."""

from __future__ import annotations

import json
import math
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageChops, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
TMP=ROOT/"tmp/pdfs/page-review"
QA=ROOT/"output/qa"


def render(label:str,pdf:Path)->tuple[list[dict[str,object]], list[Path]]:
    folder=TMP/label
    if folder.exists(): shutil.rmtree(folder)
    folder.mkdir(parents=True)
    subprocess.run(["pdftoppm","-r","144","-png",str(pdf),str(folder/"page")],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    pages=sorted(folder.glob("page-*.png")); metrics=[]
    for i,path in enumerate(pages,1):
        im=Image.open(path).convert("RGB"); background=Image.new("RGB",im.size,"white")
        bbox=ImageChops.difference(im,background).getbbox()
        if bbox is None: margins=None
        else: margins={"left":bbox[0],"top":bbox[1],"right":im.width-bbox[2],"bottom":im.height-bbox[3]}
        metrics.append({"document":label,"page":i,"pixels":list(im.size),"ink_margins_pixels":margins,"blank":bbox is None})
    for start in range(0,len(pages),4):
        sheet=Image.new("RGB",(1700,2300),"#E8E8E8"); draw=ImageDraw.Draw(sheet)
        for offset,path in enumerate(pages[start:start+4]):
            im=Image.open(path).convert("RGB"); im.thumbnail((810,1080))
            x=25+(offset%2)*840; y=55+(offset//2)*1120
            draw.text((x,y-28),f"{label} page {start+offset+1}",fill="#3D3539")
            sheet.paste(im,(x,y))
        sheet.save(QA/f"contact_{label}_{start//4+1:02d}.png")
    return metrics, pages


def all_page_contact(name: str, labelled_pages: list[tuple[str, Path]], columns: int = 5) -> Path:
    """Create one compact, high-resolution contact sheet covering every supplied page."""
    cell_w, cell_h = 430, 565
    rows = math.ceil(len(labelled_pages) / columns)
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), "#E8E8E8")
    draw = ImageDraw.Draw(sheet)
    for index, (label, path) in enumerate(labelled_pages):
        im = Image.open(path).convert("RGB")
        im.thumbnail((390, 505), Image.Resampling.LANCZOS)
        row, col = divmod(index, columns)
        x = col * cell_w + (cell_w - im.width) // 2
        y = row * cell_h + 42 + (cell_h - 50 - im.height) // 2
        draw.text((col * cell_w + 18, row * cell_h + 14), label, fill="#3D3539")
        sheet.paste(im, (x, y))
    target = QA / name
    sheet.save(target, dpi=(180, 180))
    return target


def main()->None:
    QA.mkdir(parents=True,exist_ok=True); TMP.mkdir(parents=True,exist_ok=True)
    for old in QA.glob("contact_*.png"): old.unlink()
    metrics=[]
    main_metrics, main_pages = render("main",ROOT/"output/pdf/crop_ranking_reversal_main_supervisor_review.pdf")
    supplementary_metrics, supplementary_pages = render("supplementary",ROOT/"output/pdf/crop_ranking_reversal_supplementary_supervisor_review.pdf")
    metrics += main_metrics + supplementary_metrics
    main_labelled = [(f"Main page {i}", path) for i, path in enumerate(main_pages, 1)]
    supplementary_labelled = [(f"Supplement page {i}", path) for i, path in enumerate(supplementary_pages, 1)]
    all_page_contact("contact_main_all.png", main_labelled, columns=4)
    all_page_contact("contact_supplementary_all.png", supplementary_labelled, columns=4)
    all_page_contact("contact_all_pages.png", main_labelled + supplementary_labelled, columns=5)
    (QA/"page_metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
    if any(r["blank"] for r in metrics): raise SystemExit("blank page detected")
    print(f"rendered_pages={len(metrics)} contact_sheets={len(list(QA.glob('contact_*.png')))} full_contact_sheet=contact_all_pages.png")


if __name__=="__main__": main()
