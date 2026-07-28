# Final figure contract

Backend: Python/Matplotlib only.

Target: a self-contained Nature-family supervisor-review manuscript. Every
main figure is designed at 183 mm and is also rendered for a dedicated
89-mm readability inspection. The approved `ISSUE34_NATURE_REFERENCE_2026_07_27`
colour card is the only non-neutral palette.

## Figure 1

Core conclusion: An external agronomic ranking becomes an allocation only
after margins, joint downside risk and the operational feasible set enter the
decision model.

Figure archetype: schematic-led composite.

Panel map:

- a: score-to-decision architecture and the exclusion-based reversal taxonomy.
- b: Kansas score, expected-margin and selected-allocation ordering.

Evidence hierarchy: the causal/decision architecture is the hero evidence;
the Kansas ordering is a compact calibrated illustration.

Statistics/source data: scores, mean margins and selected allocations from the
canonical reconstruction outputs; no inferential claim.

Reviewer risk: do not imply that rank disagreement alone identifies a risk or
constraint mechanism.

## Figure 2

Core conclusion: Reversal depends jointly on copula family, dependence and
risk tolerance, with null, disconnected and multiple-optimum regions retained.

Figure archetype: quantitative grid.

Panel map:

- a-c: aligned family-specific phase maps.
- d: first-crossing and disconnected-region summary.

Evidence hierarchy: phase maps are primary; frontier summaries are validation.

Statistics/source data: all solved phase cells, feasibility status and
optimal-face classifications.

Reviewer risk: no universal dependence threshold or cross-family ordering.

## Figure 3

Core conclusion: A Gaussian mean-variance policy selected by a fixed variance-
reduction target can reduce Gaussian variance yet be inferior under the
Student-t evaluation law.

Figure archetype: asymmetric quantitative composite.

Panel map:

- a: complete Gaussian mean-variance frontier with benchmark, selected policy,
  tail-aware policy projection and the weak/strong failure interval.
- b: policy allocations.
- c: Student-t loss-CVaR relative to the common ceiling.

Evidence hierarchy: the complete frontier and selected rule are primary;
allocation and tail-risk panels close the criterion.

Statistics/source data: every frontier point is solver-generated; all four
criteria, solver status, feasibility residuals and the dependence of tail
inferiority and ceiling violation are present in source data.

Reviewer risk: do not imply that a selected point proves universal failure or
count two numerically coincident inequalities as independent evidence.

## Figure 4

Core conclusion: Margin-, risk- and operationally induced reversals have
distinct signatures; the risk crossing occupies a bounded
probability-by-magnitude stress region.

Figure archetype: asymmetric mixed quantitative figure.

Panel map:

- a: score-versus-margin signature of the Kansas margin mechanism.
- b: risk-allocation crossing along the focal tolerance path.
- c: shock probability-by-magnitude map with no-crossing, crossing and
  infeasible states where present, plus first-crossing tolerance.
- d: staged operational sequence and soybean-cap illustration.

Evidence hierarchy: mechanism separation and the two-dimensional risk map are
primary; the crop-cap path is a structural illustration only.

Statistics/source data: complete mean-preserving stress grid, focal point,
solver status and first-crossing tolerance.

Reviewer risk: stress parameters are not farm-level estimates and the cap
experiment is not a causal Kansas estimate.

## Figure 5

Core conclusion: Under the shared ex-ante loss-CVaR model, information value is
non-negative when ignoring the signal is feasible, while its discrete
interaction with flexibility can be positive, null or negative.

Figure archetype: quantitative grid.

Panel map:

- a-b: information value on the two flexibility paths.
- c-d: signed adjacent-cell cross-differences with zero boundaries.

Evidence hierarchy: optimized values are primary; cross-difference maps
classify interaction without extending the restricted theorem.

Statistics/source data: four solved values per cross-difference and numerical
tolerance.

Reviewer risk: do not claim unconditional strict complementarity.

## Figure 6

Core conclusion: Rank-acreage disagreement is common in the descriptive
official-data panel but changes with score definition and is highly uncertain
in the eight-year Kansas calibration.

Figure archetype: asymmetric quantitative composite.

Panel map:

- a: definition-specific descriptive disagreement rates.
- b: exact 95% Clopper-Pearson interval for the 62/64 frequency.
- c: leakage-free lagged estimate and interval.

Evidence hierarchy: descriptive definition sensitivity is primary; short-record
uncertainty and the lagged null are equally visible boundaries.

Statistics/source data: state-year denominators, event counts, exact binomial
interval, cluster-bootstrap interval and effective years.

Reviewer risk: no causal interpretation and no treatment of bootstrap
replications as empirical observations.

## Shared QA contract

- Editable SVG/PDF text; 600-dpi TIFF and 300-dpi PNG.
- Minimum essential type 5.5 pt at the declared final-size render.
- Lowercase bold panel labels, direct labels where they reduce lookup, and a
  single shared crop mapping.
- Colour is duplicated by marker, hatch, line style, text or position.
- Automated bounds and title-collision checks, plus manual full-colour,
  grayscale, deuteranopia and protanopia inspection.
- Dedicated 89-mm and 183-mm renders, complete figure source tables, internal
  manifest and compiled-paper contact sheets.
