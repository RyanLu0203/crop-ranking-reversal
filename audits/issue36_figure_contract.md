# Issue #36 figure contract

Core conclusion: three different mechanisms must not be conflated.  The
official Kansas result is a score--margin separation with a selected complete
rank reversal; a registered mean-preserving downside stress produces a
separate risk-induced Soybean--Corn crossing; and a controlled rotation-cap
path isolates an operational crossing.

Figure archetype: quantitative, asymmetric multi-panel composites.  The
mechanism-isolation figure is the hero figure; phase, diversification,
information--flexibility and uncertainty figures are validation figures.

Target journal/output: Nature-leaning double-column figures, 183 mm wide,
editable PDF/SVG, 600-dpi TIFF and 300-dpi PNG.

Authoritative palette: `ISSUE34_NATURE_REFERENCE_2026_07_27` in
`visualization/configs/issue34_palette.yaml`.  No new base hue is permitted.

Backend: Python/matplotlib only.

Panel map:

- Figure 1: decision architecture, official score--margin separation, primary
  Kansas allocation and repaired terminology.
- Figure 2: selected pairwise, selected complete and true strong reversal over
  all 165 cells, plus optimal-face and tolerance information.
- Figure 3: declared expected-profit benchmark, Gaussian mean--variance
  frontier/selected point, and true-law CVaR comparison.
- Figure 4: mechanism isolation---margin rank, risk-induced crossing, and
  operational active-set/rotation-cap transitions.
- Figure 5: shared-ex-ante-CVaR values and adjacent-grid cross-differences.
- Figure 6: exact-binomial reversal frequency, continuous bootstrap
  percentiles and descriptive external evidence.

Statistics needed: selected and optimal-face reversal classifications;
finite-scenario means, variances and loss-CVaR; adjacent-grid cross-differences;
exact Clopper--Pearson interval; deterministic tolerance sensitivity.

Source data: every plotted numeric value must be read from
`reconstruction/issue34/outputs/*.csv`.  Mechanism parameters come only from
`simulation/configs/issue34_full_model_design.yaml`.

Reviewer risks: the Kansas calibration has eight effective years; the
mean-preserving adverse event and rotation-cap path are controlled structural
stress tests, not estimated prevalence; asymptotic tail dependence is not
identified by the small official panel; cross-difference signs are numerical
evidence for the coupled model, not a proof of the restricted theorem.
