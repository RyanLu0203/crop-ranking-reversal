# Repository baseline audit — Issue #1

Audit date: 2026-07-19.

## Initial remote state

The private GitHub repository contained one commit (`74566e9`) and one tracked file (`README.md`). It had no open or closed PRs and no remote branches other than `main`. Issues #1–#10 were all open and their complete descriptions were inspected.

## Baseline location and integrity

The authoritative teacher files were located in the previously audited local workspace and copied byte-for-byte into `baselines/teacher_draft/`. Their expected SHA-256 hashes are enforced by tests. The source TeX contains 1,204 lines and all main sections through the bibliography were inventoried.

No teacher file was edited. Local filesystem write permissions were removed as an additional guard; hashes remain the portable invariant.

## Imported versus deferred assets

Imported:

- teacher baseline TeX/PDF;
- prior theory audit, specifications, proofs, and counterexamples as Issue #2 input;
- tested modular optimization, simulation, empirical-processing, and visualization source components;
- Python environment specification and lock;
- prior migration/audit manifests under `provenance/upstream_audits/`.

Deliberately deferred or excluded:

- historical manuscripts and submission packages;
- all historical result figures/tables and Draft numerical outputs;
- large raw and processed datasets, pending Issue #4 official-source/license verification;
- smoke outputs and their displayed values;
- caches, local build products, secrets, and untracked scratch artifacts.

Upstream labels do not confer manuscript admissibility in this repository. The evidence registries have been reset to the Issue #1 evidence boundary.

## Draft completion coverage

`draft_content_completion_matrix.csv` registers 44 research/model/theorem/simulation/empirical/writing/build content groups. Every row has a canonical disposition and a dependent Issue destination or a supervisor-confirmation flag. Unmapped major-content count: **0**.

The matrix explicitly preserves all required multi-crop model components and quarantines Draft citations, data, parameters, thresholds, results, figures, and conclusions.

## Engineering baseline

- canonical Python: 3.11 through `uv`;
- dependencies locked in `uv.lock`;
- unified local gate: `make check`;
- CI: `.github/workflows/ci.yml`;
- baseline, schema, secret, absolute-runtime-path, and Draft-mapping checks: `scripts/validate_repository.py`;
- deterministic synthetic component tests: `tests/`;
- canonical manifest/checksum generator: `scripts/build_manifest.py`.

## Known limitations and isolation decisions

- No repository license exists; code is project-internal until the owner chooses one.
- No dataset is canonical in Issue #1. Issue #4 must verify official pages, documentation, licenses, raw snapshots, and parameter provenance.
- The prior theory audit is not the standalone repaired theorem package required by Issue #2.
- Imported empirical/visualization modules are candidates only; their end-to-end outputs have not been reproduced here.
- System Python is 3.9; all project commands pin Python 3.11 through `uv`.

These limitations do not block Issue #2. They correctly block substantive literature, data, simulation-result, empirical-result, and manuscript claims until their respective Issues pass.
