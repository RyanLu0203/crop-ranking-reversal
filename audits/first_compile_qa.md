# GOAL-16 deterministic compile QA

The main manuscript and Supplementary Information compile twice in isolated
directories with identical hashes. pdfLaTeX, BibTeX and `latexmk` report no
LaTeX error, undefined citation, undefined reference, missing asset, overfull
box or fatal warning. An independent LaTeX-plugin build also succeeds.

- Main manuscript: 12 pages, SHA-256
  `cbc98e41acb0bb96b94aaaa8dcc9655679d122515e5dfd07ca991a2fed00ecad`.
- Supplementary Information: 9 pages, SHA-256
  `1fb522520c6071eed20e807254fd71475aadb6c6291624b08e51e84646c423a8`.
- Combined page review: 21 nonblank pages across six contact sheets.
- Figure assets: six main and five supplementary figures; all references
  resolve and all fonts are embedded.

The build uses a fixed source date, UTC timezone and disabled variable trailer
identifier. Portable compile records are in `output/logs/`; full transient logs
remain under the ignored `build/paper/` directory.
