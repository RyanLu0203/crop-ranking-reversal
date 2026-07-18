# Project protocol

## Canonical baseline

1. The byte-identical teacher TeX and PDF in `baselines/teacher_draft/` are immutable.
2. The Draft is canonical only for the research question, concepts, multi-crop stochastic model architecture, mechanisms to investigate, and theory → simulation → empirical sequence.
3. No Draft or historical citation, datum, parameter, number, threshold, table, figure, result, or conclusion is evidence.
4. The model may be repaired only through documented theory transitions; its core multi-crop, stochastic-profit, operational-constraint, CVaR, dependence, reversal, diversification, and information components cannot be silently deleted.

## Evidence rules

1. Google Scholar is discovery/citation-tracing only. Canonical citations require the full paper, DOI/publisher record, or authoritative repository copy, with the exact supported claim recorded.
2. Canonical data require an official or recognized authoritative full source page, documentation, access date, version, coverage, units, missing codes, license/access conditions, immutable raw checksum, and executable lineage.
3. Every manuscript number must trace through `source → processing code → configuration → command → output field → checksum → manuscript location`.
4. Hand-entered result files, AI-generated values, search snippets, unsupported historical outputs, and manually adjusted plot data are inadmissible.
5. Evidence must be labeled as theorem, synthetic mathematical check, simulation, descriptive empirical evidence, causal evidence, or null/boundary result.
6. Observed acreage is not automatically an optimizer solution, and ranking discordance does not identify a CVaR/copula mechanism.

## Reproducibility and changes

1. Canonical code must not depend on an old-workspace absolute path.
2. Raw data are immutable; transformations occur only through code.
3. Parameters, seeds, tolerances, selection rules, convergence checks, and falsification criteria are frozen before main runs.
4. Synthetic smoke checks are `NOT_FOR_MANUSCRIPT`.
5. All generated figures/tables read registered tidy outputs; no hand edits.
6. Each Issue uses a dedicated branch, deliberate Issue-referencing commits, a PR, and a completion comment with exact commands and unresolved limitations.
7. A passing test proves only its declared scope. Completion requires acceptance-criterion-level evidence.
8. Secrets, credentials, caches, local paths, and license-prohibited data must not be committed.

## Status vocabulary

- `CANONICAL_BASELINE`: immutable architecture source, not external evidence.
- `THEORY_FOUNDATION_ONLY`: verified methodological source, not empirical evidence.
- `SYNTHETIC_CHECK_ONLY`: mathematical/software validation.
- `REQUIRES_FULL_RERUN`: potentially reusable asset without current end-to-end result proof.
- `ILLUSTRATIVE_ONLY`: cannot support a substantive claim.
- `INADMISSIBLE`: excluded from canonical evidence.
- `MANUSCRIPT_ADMISSIBLE`: allowed only after claim-level lineage and relevant Issue acceptance checks pass.
