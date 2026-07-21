# Crop ranking reversal

Canonical research-engineering repository for rebuilding the crop-ranking-reversal paper from the immutable teacher Draft.

## Evidence boundary

The teacher Draft fixes the research question and multi-crop stochastic model architecture. Its citations, datasets, parameters, numerical examples, thresholds, figures, tables, results, and conclusions are illustrative only. They cannot enter the manuscript without independent full-source verification and reproducible regeneration.

Synthetic tests validate mathematics and software only; they are never empirical evidence.

## Issue execution contract

Work through the existing Issues in dependency order:

1. #1 baseline, evidence governance, and repository structure
2. #2 theory repair and proofs
3. #3 verified literature foundation
4. #4 official data and parameter provenance
5. #5 frozen simulation design and optimization engine
6. #6 main numerical experiments
7. #7 full empirical rerun and robustness
8. #8 Nature-style figures and tables
9. #9 manuscript and supplementary rewrite
10. #10 clean build, QA, and first compiled draft

For each Issue:

- read its full scope, prohibitions, dependencies, deliverables, and acceptance criteria;
- inspect existing branches, PRs, files, and validation evidence before editing;
- work on a dedicated `codex/issue-N-*` branch (or a documented dependent-Issue group);
- commit with the Issue number, push, and open/update a PR;
- comment on the Issue with deliverables, exact commands, results, paths, limitations, and whether the next dependency is unblocked;
- never close an acceptance criterion using a smoke test whose scope is narrower than the criterion.

Issues #6 and #7 may run in parallel only after their dependencies are satisfied and their definitions and evidence registries are synchronized.

## Repository layout

- `baselines/teacher_draft/`: immutable teacher TeX/PDF and hash contract
- `theory/`: audited specifications, proofs, and Issue #2 repair work
- `literature/`: Issue #3 search synthesis
- `data/`: Issue #4 official-source snapshots and processing specifications
- `simulation/`, `optimization/`: Issues #5–#6 engines and registered outputs
- `empirical/`: Issue #7 pipeline
- `visualization/`, `figures/`, `tables/`: Issue #8 generated visual system
- `manuscript/`, `supplementary/`: canonical modular LaTeX sources
- `output/`: deterministic supervisor-review PDFs, compile logs, page QA and release checksums
- `evidence_registry/`, `audits/`, `provenance/`: claim-level governance and reproducibility records

## Reproducible setup

Python 3.11 is canonical. With [`uv`](https://docs.astral.sh/uv/):

```bash
uv sync --locked --extra test
make paper
make check
```

`make paper` performs two isolated deterministic builds of each PDF, renders all pages and validates the release package. `make check` runs every repository, theory, literature, data, simulation, empirical, visual, manuscript and final-package validator plus the canonical test suite.

## Current milestone

Issues #1--#10 are integrated in the Stage I package labelled **“First compiled draft for supervisor review.”** Commit `4d6c14d` is the theory-repair and reproducibility foundation, not the final scientific manuscript.

Stage II begins with GOAL-11 / Issue #21. Its evidence-gated reconstruction blueprint is in `audits/stage_ii/`. Later phases must execute in the fixed order GOAL-14 theory → GOAL-12 confirmatory simulation → GOAL-13 visualization → GOAL-15 empirical strengthening. The manuscript may be rebuilt only after all four scientific phases pass.
