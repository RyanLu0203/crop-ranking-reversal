#!/usr/bin/env python3
"""Perform two isolated deterministic LaTeX builds for the Stage II package."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/"build/paper"
OUTPUT=ROOT/"output"
SOURCE_DATE_EPOCH="1784390400"


def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command:list[str],*,cwd:Path,env:dict[str,str]|None=None)->subprocess.CompletedProcess[str]:
    result=subprocess.run(command,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if result.returncode: raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}\n{result.stdout[-6000:]}")
    return result


def compile_one(name:str,entry:Path,pass_name:str,env:dict[str,str])->tuple[Path,Path]:
    out=BUILD/pass_name/name; out.mkdir(parents=True,exist_ok=True)
    result=run(["latexmk","-norc","-pdf","-interaction=nonstopmode","-halt-on-error","-synctex=1",f"-outdir={out}",str(entry)],cwd=entry.parent,env=env)
    stem=entry.stem; pdf=out/f"{stem}.pdf"; log=out/f"{stem}.log"
    if not pdf.exists() or not log.exists(): raise RuntimeError(f"missing build output for {name}")
    bad=["undefined citations","undefined references","Citation `","Reference `","Overfull \\hbox","Overfull \\vbox","LaTeX Error","Emergency stop","Fatal error"]
    log_text=log.read_text(errors="replace")
    found=[token for token in bad if token in log_text]
    if found: raise RuntimeError(f"{name} log contains prohibited diagnostics: {found}")
    return pdf,log


def version(command:list[str])->str:
    try: return subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT).stdout.splitlines()[0]
    except Exception as exc: return f"unavailable: {exc}"


def write_compile_record(name: str, entry: Path, pdf: Path, target: Path) -> None:
    """Write a portable audit record; full raw logs remain in ignored build/."""
    target.write_text(
        "\n".join([
            "STAGE II FINAL SCIENTIFIC DRAFT",
            f"document={name}",
            f"source={entry.relative_to(ROOT).as_posix()}",
            "engine=pdfLaTeX via latexmk and BibTeX",
            "isolated_build_passes=2",
            "pass1_exit_code=0",
            "pass2_exit_code=0",
            "byte_stable=YES",
            f"pdf_sha256={sha(pdf)}",
            f"pdf_bytes={pdf.stat().st_size}",
            "diagnostic_scan=PASS",
            "latex_errors=0",
            "undefined_citations=0",
            "undefined_references=0",
            "missing_assets=0",
            "overfull_boxes=0",
            "raw_logs=build/paper/pass*/<document>/<entry>.log (transient; gitignored)",
            "",
        ]),
        encoding="utf-8",
    )


def main()->None:
    if BUILD.exists(): shutil.rmtree(BUILD)
    for rel in ["pdf","logs","reproducibility"]: (OUTPUT/rel).mkdir(parents=True,exist_ok=True)
    env=os.environ.copy(); env.update({"SOURCE_DATE_EPOCH":SOURCE_DATE_EPOCH,"FORCE_SOURCE_DATE":"1","TZ":"UTC","BIBINPUTS":str(ROOT)+os.pathsep})
    run(["uv","run","--python","3.11","python","scripts/generate_manuscript_inputs.py"],cwd=ROOT,env=env)
    run(["uv","run","--python","3.11","python","scripts/validate_manuscript.py"],cwd=ROOT,env=env)
    entries={"manuscript":ROOT/"manuscript/main.tex","supplementary":ROOT/"supplementary/supplementary.tex"}
    results={}
    for name,entry in entries.items():
        p1,_l1=compile_one(name,entry,"pass1",env); p2,_l2=compile_one(name,entry,"pass2",env)
        stable=sha(p1)==sha(p2)
        if not stable: raise RuntimeError(f"{name} PDF is not byte-stable across isolated builds")
        final_name=f"crop_ranking_reversal_{'main' if name=='manuscript' else 'supplementary'}_supervisor_review.pdf"
        final=OUTPUT/"pdf"/final_name; shutil.copy2(p1,final)
        log_target=OUTPUT/"logs"/f"{name}_compile.txt"; write_compile_record(name,entry,final,log_target)
        results[name]={"pdf":str(final.relative_to(ROOT)),"sha256":sha(final),"repeat_sha256":sha(p2),"byte_stable":stable,"log":str(log_target.relative_to(ROOT)),"source":str(entry.relative_to(ROOT))}
    environment={"label":"STAGE II FINAL SCIENTIFIC DRAFT","source_date_epoch":SOURCE_DATE_EPOCH,"platform":platform.platform(),"python":platform.python_version(),"latexmk":version(["latexmk","-v"]),"pdflatex":version(["pdflatex","--version"]),"bibtex":version(["bibtex","--version"]),"source_identity":"canonical repository manifest plus Stage II release checksums","build_command":"make paper"}
    (OUTPUT/"reproducibility/build_environment.json").write_text(json.dumps(environment,indent=2)+"\n")
    (OUTPUT/"reproducibility/build_report.json").write_text(json.dumps(results,indent=2)+"\n")
    checksum_paths=list((OUTPUT/"pdf").glob("*.pdf"))+list((OUTPUT/"logs").glob("*.txt"))+[OUTPUT/"reproducibility/build_environment.json",OUTPUT/"reproducibility/build_report.json"]
    (OUTPUT/"reproducibility/SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(ROOT)}\n" for p in sorted(checksum_paths)))
    print(json.dumps(results,indent=2))


if __name__=="__main__": main()
