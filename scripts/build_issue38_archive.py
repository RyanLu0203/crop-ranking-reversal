#!/usr/bin/env python3
"""Build the deterministic Issue #40 reproducibility archive."""

from __future__ import annotations

import gzip
import hashlib
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"
ARCHIVE = RELEASE / "crop-ranking-reversal-issue40-supervisor-review.tar.gz"

PATHS = [
    "main_manuscript.tex",
    "main_manuscript.pdf",
    "supplementary_information.tex",
    "supplementary_information.pdf",
    "references.bib",
    "literature_registry.csv",
    "claim_reference_matrix.csv",
    "source_registry.csv",
    "data_dictionary.md",
    "analysis_manifest.json",
    "README_REPRODUCIBILITY.md",
    "SUPERVISOR_REVIEW_NOTE.md",
    "TEACHER_DRAFT_ALIGNMENT_AUDIT.md",
    "MATHEMATICAL_REPAIR_LOG.md",
    "EXPERIMENT_RELIABILITY_AUDIT.md",
    "REFERENCE_RELIABILITY_AUDIT.md",
    "LIMITATIONS_AND_CLAIM_BOUNDARIES.md",
    "SCIENTIFIC_CLAIM_REPAIR_AUDIT.md",
    "MECHANISM_ISOLATION_AUDIT.md",
    "DIVERSIFICATION_FAILURE_VALIDATION.md",
    "STRONG_REVERSAL_SENSITIVITY.md",
    "HEURISTIC_PROJECTION_VALIDATION.md",
    "INFORMATION_FLEXIBILITY_VALIDATION.md",
    "PR_INTEGRATION_PLAN.md",
    "audits/issue_34_acceptance_matrix.md",
    "audits/issue34_figure_contract.md",
    "audits/issue36_figure_contract.md",
    "audits/issue38_figure_contract.md",
    "audits/issue40_figure_contract.md",
    "audits/issue38_manuscript_language_scan.json",
    "audits/issue40_deterministic_build.json",
    "audits/issue40_final_consistency.json",
    "audits/issue40_final_visual_qa.md",
    "audits/issue38_final_visual_qa.md",
    "audits/issue34_final_page_qa.md",
    "audits/issue40_visual_qa",
    "literature/issue34_search_log.md",
    "manuscript/issue34",
    "figures/issue34",
    "reconstruction/issue34",
    "simulation/configs/issue34_full_model_design.yaml",
    "visualization/configs/issue34_palette.yaml",
    "scripts/run_issue34_reconstruction.py",
    "scripts/render_issue34_manuscript_numbers.py",
    "scripts/make_issue34_figures.py",
    "scripts/build_issue38_visual_qa.py",
    "scripts/build_issue38_papers_deterministic.py",
    "scripts/validate_issue38_finalization.py",
    "scripts/validate_issue40_final_consistency.py",
    "scripts/build_issue38_archive.py",
    "optimization",
    "theory/issue34",
    "theory/proofs/computational_checks/test_issue34_theory.py",
    "tests",
    "empirical/goal16/outputs/extended_state_crop_panel.csv",
    "empirical/goal16/raw",
    "data/raw",
    "data/processed/canonical_crop_year_panel.csv",
    "pyproject.toml",
    "uv.lock",
    "Makefile",
]


def iter_files():
    seen = set()
    for rel in PATHS:
        path = ROOT / rel
        if not path.exists():
            raise FileNotFoundError(rel)
        candidates = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
        for file in candidates:
            if any(part in {".git", "__pycache__", ".pytest_cache"} for part in file.parts):
                continue
            key = file.relative_to(ROOT).as_posix()
            if key not in seen:
                seen.add(key)
                yield file, key


def normalize(info: tarfile.TarInfo) -> tarfile.TarInfo:
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    info.mode = 0o755 if info.name.endswith(".py") else 0o644
    return info


def main() -> None:
    RELEASE.mkdir(parents=True, exist_ok=True)
    with ARCHIVE.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w") as tar:
                for file, arcname in iter_files():
                    tar.add(file, arcname=arcname, recursive=False, filter=normalize)
    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    checksum = ARCHIVE.with_suffix(ARCHIVE.suffix + ".sha256")
    checksum.write_text(f"{digest}  {ARCHIVE.name}\n")
    print(f"{ARCHIVE}\n{digest}")


if __name__ == "__main__":
    main()
