# First compiled draft for supervisor review

This package is the first complete end-to-end compilation milestone. It is ready for scientific and editorial review by the supervisor; it is not a submission-ready package.

## Review files

- `pdf/crop_ranking_reversal_main_supervisor_review.pdf` — main manuscript
- `pdf/crop_ranking_reversal_supplementary_supervisor_review.pdf` — Supplementary Information
- `../audits/first_compile_qa.md` — build and PDF checks
- `../audits/final_claim_evidence_audit.md` — final evidence-level audit
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

The headline empirical result is descriptive. Simulation prevalence and
mechanism patterns are supplementary and nonheadline because the convergence
gate fails. Observed acreage optimality, private constraints, CVaR binding,
copula mechanism, causal effects and welfare are not identified.
