# Stage II deterministic compile QA

## Acceptance contract

The main manuscript and Supplementary Information must compile without LaTeX errors, undefined citations or references, missing assets, overfull boxes or fatal warnings. Each document is built twice in isolated directories under a fixed source date and UTC timezone; the two hashes for a document must match exactly.

## Build controls

- Entry points: `manuscript/main.tex` and `supplementary/supplementary.tex`.
- Engine: pdfLaTeX through `latexmk`, with BibTeX.
- Determinism: fixed `SOURCE_DATE_EPOCH`, UTC timezone and disabled variable trailer ID.
- Bibliography: one canonical root `references.bib` resolved through `BIBINPUTS`.
- Figures: six Stage II main PDFs and four Stage II supplementary PDFs.
- Command: `make paper`; full scientific validation: `make check`.
- Portable compile records: `output/logs/`; transient engine logs: ignored `build/paper/`.

## PDF checks

The package validator checks byte stability, embedded fonts, selectable text, metadata, nonblank rendered pages, citations, references, missing assets and package checksums. Page counts and contact-sheet counts are derived from the compiled documents rather than hard-coded. The final visual decision is recorded separately in `audits/visual_page_review.md` after rendering.
