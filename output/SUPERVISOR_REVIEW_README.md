# Stage II final scientific package

This package closes the authorized Stage II reconstruction and GOAL-17 scientific deepening from theory through confirmatory simulation, the official-data empirical extension, six redesigned main figures, seven supplementary figures and results-led manuscript integration. It is a final scientific draft for author review; it is not a journal-submission archive until author-owned metadata and journal formatting are completed.

## Review files

- `pdf/crop_ranking_reversal_main_supervisor_review.pdf` — main manuscript
- `pdf/crop_ranking_reversal_supplementary_supervisor_review.pdf` — Supplementary Information
- `../audits/first_compile_qa.md` — deterministic build and PDF checks
- `../audits/final_claim_evidence_audit.md` — final evidence-level audit
- `../audits/stage_ii_final_claim_evidence.csv` — claim-to-artifact lineage
- `../audits/visual_page_review.md` — page-by-page rendering review
- `../audits/goal16_post_visual_qa.md` — full-width, 89-mm, grayscale, colour-vision and overlap audit
- `../audits/goal16_before_after_audit.md` — pre/post reconstruction comparison
- `../audits/goal17_visual_exploration.md` — two final-size concepts for each main figure and the selection record
- `../visualization/goal17/qa/validation_report.json` — vector, palette, size, font and collision validation
- `remaining_actions.md` — author and submission actions still required

## Reproduction

From a clean checkout with Python 3.11, TeX Live 2025/`latexmk`, BibTeX
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

E2 operational reversal and E6 information--flexibility sign heterogeneity are the only supported confirmatory simulation results. E1, E3, E4 and E5 remain inconclusive because they do not meet their experiment-level precision criteria. The empirical results are descriptive and accounting-identified only. Observed acreage optimality, private constraints, CVaR binding, copula mechanism, causal effects and welfare are not identified.

All figures use the frozen colour card `#3D3539`, `#0F9EA8`, `#008B82`, `#45728F`, `#8CD1B2`, `#8B84A3`, with redundant non-colour encodings and accessibility proofs. The eight new GOAL-17 compositions are designed at 183 mm; their editable SVG and vector PDF colours, 5.5-pt minimum text, bounds and title lanes validate without failures. Full-colour, grayscale, deuteranopia and protanopia contact sheets are included.
