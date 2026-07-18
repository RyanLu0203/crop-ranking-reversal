#!/usr/bin/env python3
"""Render every final PDF page and create review contact sheets and metrics."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageChops, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
TMP=ROOT/"tmp/pdfs/page-review"
QA=ROOT/"output/qa"


def render(label:str,pdf:Path)->list[dict[str,object]]:
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
    return metrics


def main()->None:
    QA.mkdir(parents=True,exist_ok=True); TMP.mkdir(parents=True,exist_ok=True)
    for old in QA.glob("contact_*.png"): old.unlink()
    metrics=[]
    metrics+=render("main",ROOT/"output/pdf/crop_ranking_reversal_main_supervisor_review.pdf")
    metrics+=render("supplementary",ROOT/"output/pdf/crop_ranking_reversal_supplementary_supervisor_review.pdf")
    (QA/"page_metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
    if any(r["blank"] for r in metrics): raise SystemExit("blank page detected")
    print(f"rendered_pages={len(metrics)} contact_sheets={len(list(QA.glob('contact_*.png')))}")


if __name__=="__main__": main()
