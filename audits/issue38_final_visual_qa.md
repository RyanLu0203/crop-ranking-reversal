# Final visual QA

Status: **PASS after manual inspection**

## Scope

- Figures 1–6 at 183 mm and 89 mm review widths.
- Full colour, grayscale, deuteranopia and protanopia transforms.
- Final compiled `main_manuscript.pdf`, 20 pages.
- Final compiled `supplementary_information.pdf`, 7 pages.

## Automated checks

- renderer out-of-bounds failures: 0;
- panel-title collisions: 0;
- minimum SVG text size: 5.6 pt at declared final size;
- all six figures have PDF, editable SVG, 300-dpi PNG and 600-dpi TIFF;
- all six figures have source-data tables and SHA-256 entries;
- LaTeX logs contain no overfull or underfull boxes, unresolved references or
  unresolved citations.

## Manual figure inspection

- Figure 1: decision architecture is visually dominant; ranking, margins and
  allocation are aligned and labels are unobstructed.
- Figure 2: the three phase maps use common scales; family paths use distinct
  marker shapes; null and complete regions remain distinguishable in
  grayscale and colour-vision transforms.
- Figure 3: the full 301-point frontier, fixed selection rule, selected point,
  interval, allocations, evaluation loss-CVaR and common ceiling are legible;
  the dependence of the tail and ceiling conditions is stated once.
- Figure 4: the margin, focal risk, probability-by-magnitude and operational
  panels are distinct; the focal star is offset from its numeric label; the
  infeasible cell and no-crossing cells remain visible without colour alone.
- Figure 5: both information-value paths and both signed cross-difference maps
  share consistent axes and readable symbols.
- Figure 6: definition sensitivity, exact binomial uncertainty and the lagged
  null are separated and directly labelled.

No text–text, text–marker or panel-title overlap, clipping, legend collision or
unreadable mathematical symbol was found at either review width.

## Manual compiled-page inspection

All 27 pages were inspected in whole-document contacts and two-page detail
sheets. Figures and captions remain together, body text does not collide with
floats, no content extends beyond page bounds, no heading is orphaned and no
blank page remains. The bibliography was compacted so the main paper ends on a
fully used page 20 rather than a sparse page 21.

Colour is never the only carrier of crop, policy or status identity: marker
shape, hatch, line style, sign, position and direct text labels provide
redundant encodings.
