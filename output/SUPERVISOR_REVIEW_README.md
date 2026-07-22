# Stage II final scientific package

This package closes the authorized Stage II reconstruction from theory through confirmatory simulation, admitted-data empirical analysis, ten-figure visualization and manuscript integration. It is a final scientific draft for author review; it is not a journal-submission archive until author-owned metadata and journal formatting are completed.

## Review files

- `pdf/crop_ranking_reversal_main_supervisor_review.pdf` — main manuscript
- `pdf/crop_ranking_reversal_supplementary_supervisor_review.pdf` — Supplementary Information
- `../audits/first_compile_qa.md` — deterministic build and PDF checks
- `../audits/final_claim_evidence_audit.md` — final evidence-level audit
- `../audits/stage_ii_final_claim_evidence.csv` — claim-to-artifact lineage
- `../audits/visual_page_review.md` — page-by-page rendering review
- `remaining_actions.md` — author and submission actions still required

## Reproduction

From a clean checkout with Python 3.11, `uv`, TeX Live 2025/`latexmk`, BibTeX
and Poppler available:

```sh
make paper
make check
```

`make paper` regenerates manuscript numbers, builds main and supplementary PDFs
twice in isolated directories, requires byte-identical outputs, renders every
page, creates contact sheets, generates the release manifest, and validates the
package. Portable compile records are retained in `logs/`; full engine logs are
transient build products. `make check` runs every scientific validator and
canonical test.

## Evidence boundary

E2 operational reversal and E6 information--flexibility sign heterogeneity are the only promoted confirmatory simulation results. E1, E3, E4 and E5 remain adverse because their experiment-level precision gates fail. The empirical results are descriptive and accounting-identified only. Observed acreage optimality, private constraints, CVaR binding, copula mechanism, causal effects and welfare are not identified.

All figures use the frozen colour card `#3D3539`, `#0F9EA8`, `#008B82`, `#45728F`, `#8CD1B2`, `#8B84A3`, with redundant non-colour encodings and accessibility proofs.
