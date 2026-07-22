#!/usr/bin/env python3
"""Build a deterministic Stage II final scientific archive."""

from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "output/stage_ii_final_scientific_package.zip"
FIXED_TIME = (2026, 7, 22, 0, 0, 0)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect() -> list[Path]:
    exact = [
        "Makefile", "pyproject.toml", "uv.lock", "PROJECT_PROTOCOL.md", "references.bib",
        "output/SUPERVISOR_REVIEW_README.md", "output/remaining_actions.md",
        "audits/first_compile_qa.md", "audits/final_claim_evidence_audit.md",
        "audits/stage_ii_final_claim_evidence.csv", "audits/visual_page_review.md",
        "audits/goal16_narrative_after.md", "audits/goal16_post_visual_qa.md",
        "audits/goal16_before_after_audit.md", "audits/goal16_title_and_terminology_audit.md",
        "visualization/configs/stage_ii_nature_style.yaml",
        "scripts/generate_manuscript_inputs.py", "scripts/validate_manuscript.py",
        "scripts/build_paper.py", "scripts/render_pdf_qa.py",
        "scripts/build_release_manifest.py", "scripts/validate_final_package.py",
        "scripts/generate_stage_ii_figures.py", "scripts/validate_stage_ii_visualization.py",
        "scripts/run_stage_ii_confirmatory.py", "scripts/validate_stage_ii_confirmatory.py",
        "scripts/run_stage_ii_empirical.py", "scripts/validate_stage_ii_empirical.py",
        "scripts/verify_stage_ii_empirical_reproducibility.py",
        "scripts/run_goal16_empirical.py", "empirical/goal16/EMPIRICAL_AUDIT.md",
        "scripts/build_goal16_post_visual_audit.py",
        "scripts/fetch_goal17_census_geometry.py",
        "scripts/generate_goal17_visual_candidates.py",
        "scripts/generate_goal17_figures.py",
        "scripts/validate_goal17_visualization.py",
        "audits/goal17_baseline_audit.md",
        "audits/goal17_visual_contracts.md",
        "audits/goal17_visual_exploration.md",
        "audits/goal17_candidate_visual_qa.csv",
        "audits/goal17_acceptance_report.md",
        "data/goal17/source_registry.csv",
    ]
    trees = [
        "manuscript", "supplementary", "figures/stage_ii", "figures/goal17",
        "visualization/stage_ii", "visualization/goal17", "visualization/src/crop_visualization", "visualization/style",
        "theory/repaired", "theory/stage_ii",
        "simulation/configs", "simulation/stage_ii/outputs", "simulation/src/crop_simulation",
        "empirical/configs", "empirical/stage_ii/outputs", "empirical/goal16", "empirical/src/crop_empirical",
        "evidence_registry", "output/pdf", "output/logs", "output/reproducibility",
        "audits/goal16_visual_comparison", "audits/goal17_visual_candidates", "data/goal17/raw",
    ]
    paths = {ROOT / rel for rel in exact if (ROOT / rel).is_file()}
    for rel in trees:
        folder = ROOT / rel
        if folder.exists():
            paths.update(p for p in folder.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    paths.discard(TARGET)
    return sorted(paths, key=lambda p: p.relative_to(ROOT).as_posix())


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def main() -> None:
    paths = collect()
    rows = [{"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p), "bytes": p.stat().st_size} for p in paths]
    manifest_io = io.StringIO()
    writer = csv.DictWriter(manifest_io, fieldnames=["path", "sha256", "bytes"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(TARGET, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(zip_info("PACKAGE_MANIFEST.csv"), manifest_io.getvalue().encode("utf-8"))
        for path in paths:
            archive.writestr(zip_info(path.relative_to(ROOT).as_posix()), path.read_bytes())
    checksum = TARGET.with_suffix(TARGET.suffix + ".sha256")
    checksum.write_text(f"{sha(TARGET)}  {TARGET.name}\n", encoding="utf-8")
    print(f"stage_ii_archive_files={len(paths)} bytes={TARGET.stat().st_size} sha256={sha(TARGET)}")


if __name__ == "__main__":
    main()
