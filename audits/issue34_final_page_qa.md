# Issue #34 final page-by-page visual QA

## Artifacts inspected

- `main_manuscript.pdf`: 19 pages.
- `supplementary_information.pdf`: 7 pages.
- `figures/issue34/Figure1` through `Figure6`: PDF, SVG, PNG and
  LZW-compressed TIFF exports, with matching source-data files.

## Procedure and result

Both PDFs were rendered page by page with `pdftoppm` after the final
`make issue34` build.  Every rendered page was inspected at contact-sheet and
full-page scale for clipping, unreadable labels, broken equations, truncated
tables, missing figure panels, unresolved references and unintended blank
pages.  No blocking visual defect was found.  The final main log contains no
unresolved citation/reference warnings and no overfull boxes; the supplement
contains only harmless float-placement warnings.

## Visual-system lock

The user-supplied colour card `截屏 2026-07-27 10.43.11.png` is the
authoritative Issue #34 palette.  Its twelve hexadecimal colours are registered in
`visualization/configs/issue34_palette.yaml` and used throughout the six-figure
narrative.  Legacy gold, red and viridis encodings are not used.  Text and
essential outlines use the darkest registered teal; uncertainty, category and
state encodings use only registered palette colours, with marker and line-style
redundancy where colour alone would be insufficient.

## Disposition

`PASS`.  The PDFs and figure exports are visually suitable for supervisor
review, subject to the scientific limitations and supervisor-confirmation
items documented elsewhere in the package.
