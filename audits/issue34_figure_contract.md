# Issue #34 figure contract

Core conclusion: a high agronomic rank can receive less land because the full
profit distribution, downside-risk boundary and operational feasible set jointly
determine acreage, with reversal occurring on a conditional and auditable frontier.

Figure archetype: quantitative composites with one schematic-led opening figure.

Target journal/output: Nature-leaning double-column figures; editable PDF/SVG plus
600-dpi TIFF and 300-dpi PNG.

Authoritative palette: `ISSUE34_NATURE_REFERENCE_2026_07_27`, supplied by the
user on 27 July 2026. The twelve registered colors are recorded in
`visualization/configs/issue34_palette.yaml`; no other base hue may be used.

Backend: Python/matplotlib only.

Final size: 183 mm wide; 118--150 mm high.

Panel map:

- Figure 1: decision architecture; genuine score; calibrated margins; primary allocation.
- Figure 2: reversal phase diagram; active-set transitions; family-specific frontier.
- Figure 3: matched-rank-dependence diversification test; allocation and tail-loss comparison.
- Figure 4: benchmark-policy allocations; profit--CVaR trade-off; feasibility and robustness.
- Figure 5: post-signal acreage flexibility and state-shock buffering information values.
- Figure 6: external score--acreage disagreement; lagged estimate; bootstrap uncertainty.

Evidence hierarchy:

- Hero evidence: primary full-model allocation and conditional reversal phase.
- Validation evidence: matched-dependence diversification test and full-policy comparison.
- Controls/robustness: bootstrap intervals, alternative copulas/marginals/solvers and
  aggregate descriptive evidence.

Statistics needed: finite-scenario optimum, exact LP residuals, cluster bootstrap
confidence intervals, historical bootstrap percentiles and deterministic sensitivity grid.

Source data needed: all panel values are read from
`reconstruction/issue34/outputs/*.csv`; no plotted number is hand-entered except
registered labels and model-stage annotations.

Image-integrity notes: charts contain no scientific raster images. All transformations
are performed on tables by the plotting script and vector text remains editable.

Reviewer risk: the eight-year Kansas calibration cannot estimate extreme-tail dependence
precisely; dependence is therefore a registered stress path, and the 31-state panel is
descriptive rather than causal.
