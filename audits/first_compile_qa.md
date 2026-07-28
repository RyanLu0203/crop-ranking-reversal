# GOAL-17 deterministic compile QA

The main manuscript and Supplementary Information compile twice in isolated
directories with identical hashes. pdfLaTeX, BibTeX and `latexmk` report no
LaTeX error, undefined citation, undefined reference, missing asset, overfull
box or fatal warning.

- Main manuscript: 16 pages, SHA-256
  `56d71370a1fba93c2e86fd5a0c814d90c774034391aba76dad0263667d225f25`.
- Supplementary Information: 11 pages, SHA-256
  `37ce4e42aea74295dfbf22be2127412c9d6da6261b706480e5155538d5acc393`.
- Combined page review: 27 nonblank pages across seven contact sheets.
- Figure assets: six main and seven supplementary figures; all references
  resolve and all fonts are embedded.

The build uses a fixed source date, UTC timezone and disabled variable trailer
identifier. Portable compile records are in `output/logs/`; full transient logs
remain under the ignored `build/paper/` directory.
