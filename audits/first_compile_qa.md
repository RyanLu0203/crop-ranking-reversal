# First compile QA

## Outcome

The first main manuscript and Supplementary Information PDFs compile without
LaTeX errors, undefined citations or references, missing assets, overfull boxes
or fatal warnings. Both documents are labelled **first compiled draft for
supervisor review** and must not be described as submission-ready.

## Build controls

- Engine: pdfLaTeX through TeX Live 2025 `latexmk`, with BibTeX.
- Entry points: `manuscript/main.tex` and `supplementary/supplementary.tex`.
- Determinism: fixed `SOURCE_DATE_EPOCH`, UTC time zone and disabled variable
  trailer ID.
- Isolation: main and supplement are each built in two independent output
  directories. The two main hashes match; the two supplementary hashes match.
- Clean command: `make paper`.
- Bibliography: a single canonical root `references.bib` is discovered through
  `BIBINPUTS`; no duplicate bibliography is generated.
- Logs: portable compile records are exported under `output/logs/`; complete
  engine logs remain under the gitignored `build/paper/` tree for local diagnosis.

## PDF result

- Main manuscript: 12 letter-size pages, embedded fonts, selectable text,
  working hyperlinks and journal-neutral metadata.
- Supplementary Information: 5 letter-size pages, embedded fonts, selectable
  text, working hyperlinks and journal-neutral metadata.
- Figures: canonical Issue #8 vector PDFs; no missing figure or unreadable
  caption observed.
- Page numbers, section hierarchy, equations and references render consistently.

## Repairs made during first compile

1. Replaced output-directory-sensitive bibliography resolution with the clean
   build environment.
2. Broke long source paths using `\path` to remove overfull boxes.
3. Added deterministic trailer and timestamp controls for byte-stable builds.
4. Added widow/orphan penalties and shortened the bounded conclusion to remove
   a stranded final line.
5. Top-aligned supplementary figures to remove avoidable float-page whitespace.

No theory, evidence, figure, table or result was removed to obtain a clean build.
