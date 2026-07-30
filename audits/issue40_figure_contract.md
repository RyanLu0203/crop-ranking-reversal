# Issue 40 figure contract

## Shared journal and export contract

- Target: Nature-style double-column scientific figures, 183 mm final width and no
  more than 170 mm height; 89 mm reductions are readability checks, not alternate
  scientific versions.
- Backend: Python/Matplotlib exclusively for drawing, preview, export and visual QA.
- Typography: sans serif; 5--7 pt ordinary text at final size; 8 pt bold upright
  lowercase panel labels; 0.25--1 pt strokes.
- Palette: only the approved 27 July 2026 palette. Neutral greys carry context;
  teal/aqua and violet carry focal evidence. Colour is always paired with shape,
  line style, hatch or position.
- Outputs: editable-text SVG, editable TrueType PDF, 300 dpi review PNG, 600 dpi
  LZW TIFF and panel-level CSV source data.
- Integrity: every quantitative mark is generated from reconstruction outputs; no
  omitted cells, smoothed nulls, fabricated uncertainty or local raster editing.

## Figure 1

- Core conclusion: agronomic scores affect planting only after cardinal margins,
  dependence, downside risk and operational feasibility translate ranking into a
  constrained allocation.
- Archetype: schematic-led asymmetric composite.
- Panel map: **a**, dominant left-to-right score-to-allocation causal chain;
  **b**, ordered external scores; **c**, mean margins with dispersion; **d**,
  selected allocation in the same crop order.
- Evidence hierarchy: the chain is the hero; aligned score/margin/allocation strips
  validate each transformation.
- Reviewer risk: a decorative workflow could imply causal estimation. Mitigation:
  label inputs and optimization objects precisely and keep all displayed values
  source-backed.

## Figure 2

- Core conclusion: selected reversal depends on copula family and risk tolerance,
  whereas zero strong reversal in the principal grid is structural because all
  crop lower bounds are positive.
- Archetype: quantitative grid with a frontier support panel.
- Panel map: **a--c**, common classification map for Gaussian, Student-t and
  Clayton; **d**, first selected-reversal boundary by dependence path.
- Evidence hierarchy: the complete cell map is primary; the boundary traces are a
  compact summary.
- Reviewer risk: readers may interpret absence of strong reversal as an empirical
  null. Mitigation: conventional categorical legend, hatched structural-zero key
  and caption cross-reference to zero-bound sensitivity.

## Figure 3

- Core conclusion: the pre-registered 15% Gaussian variance target selects one
  canonical mean--variance policy that genuinely reduces Gaussian variance but is
  inferior under the Student-t tail law.
- Archetype: asymmetric mixed quantitative composite.
- Panel map: **a**, dominant full 301-point frontier with target threshold,
  selected point and failure interval; **b**, allocation composition of the three
  policies; **c**, Student-t evaluation-law loss-CVaR against the common ceiling.
- Evidence hierarchy: selected-point geometry is primary; allocation and tail-law
  evaluation explain why the Gaussian target does not certify tail safety.
- Reviewer risk: conflating Gaussian construction and Student-t evaluation.
  Mitigation: visually separate those spaces and name each law on the axes.

## Figure 4

- Core conclusion: margin-, risk- and operationally induced reversals have distinct
  counterfactual signatures, and the risk crossing occupies only part of the
  declared stress grid.
- Archetype: asymmetric mixed quantitative composite.
- Panel map: **a**, score--margin separation; **b**, focal downside-risk crossing;
  **c**, complete probability-by-magnitude classification; **d**, operational cap
  crossing.
- Evidence hierarchy: the two crossing paths are primary; the categorical map
  establishes scope; the margin scatter identifies the baseline mechanism.
- Reviewer risk: focal stress appearing representative. Mitigation: subtle focal
  outline, neutral no-crossing/infeasible encodings and retention of every cell.

## Figure 5

- Core conclusion: information value is non-negative, but its discrete interaction
  with flexibility changes sign across the shared ex-ante CVaR model.
- Archetype: quantitative grid.
- Panel map: **a--b**, value surfaces for acreage reallocation and shock buffering;
  **c--d**, corresponding adjacent-grid cross-differences on one centred signed
  scale.
- Evidence hierarchy: signed interaction maps are primary; value surfaces verify
  that sign changes are not negative information values.
- Reviewer risk: colour-driven sign inference or interpolation beyond the grid.
  Mitigation: centred normalization, explicit zero colour and sparse symbolic
  overlays with all cells retained.

## Figure 6

- Core conclusion: descriptive disagreement, historical-resample reversal
  frequency and leakage-free lagged association have different estimands; raw
  resampling distributions are shown where they exist, while the binomial
  frequency retains its exact interval.
- Archetype: aligned uncertainty triptych.
- Panel map: **a**, definition-specific state-panel disagreement rainclouds;
  **b**, 62/64 exact Clopper--Pearson interval; **c**, lagged coefficient interval
  around zero with its state-cluster bootstrap raincloud.
- Evidence hierarchy: half densities show all bootstrap draws, a fixed 72-draw
  subset provides raw-point texture, IQR and median glyphs summarize the centre,
  and the observed estimate plus 95% interval remains focal.
- Reviewer risk: visually equating bootstrap distributions with the exact
  binomial interval. Mitigation: distinct axes and method labels, and no synthetic
  density is drawn for the 62/64 binomial estimand.

## Shared QA gate

Pass requires: correct 183 mm export geometry; readable 89 mm reductions; editable
SVG/PDF text; complete source-data copies; zero renderer bounds failures or title
collisions; no unintended overlap/clipping; interpretable full-colour, grayscale,
deuteranopia and protanopia contact sheets; and page-by-page inspection of the
compiled manuscript and Supplementary Information.
