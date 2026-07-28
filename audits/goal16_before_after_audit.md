# GOAL-16 before/after visual reconstruction audit

## Decision

PASS. The pre-reconstruction Stage II figures were preserved as the comparison
baseline at commit `4088e6223c3d6ac13841c2cacc90181e21741a86`; the reconstructed
set contains six main and five supplementary figures with one visual grammar,
one frozen colour card and one claim per panel group. The five contact sheets in
`audits/goal16_visual_comparison/` place the baseline and reconstructed renderings
side by side at 183 mm, 89 mm, grayscale, deuteranopia and protanopia views.

## Material changes

- Figure 1 now leads with the identification ladder and precise reversal
  definitions rather than a software-like workflow.
- Figure 2 presents four analytic mechanisms on shared two-crop coordinates.
- Figure 3 separates allocation, indexed outcomes, exact attribution and signed
  KKT pressures; no heatmap is used for signed pressure terms.
- Main Figures 4 and 5 contain only the conclusive E2 and E6 results. The
  inconclusive E1, E3, E4 and E5 inventories are retained in Figures S1--S3.
- Figure 6 is rebuilt from the official 2016--2024 state panel and shows spatial,
  definition, temporal, persistence and aggregation boundaries without a
  county-level or causal claim.
- Figure S4 isolates numerical integrity and infeasible rows; Figure S5 isolates
  empirical robustness and sample flow.

## Legibility and overlap closure

The reconstruction reduces repeated prose inside plotting regions, moves
legends away from data marks, and preserves labels at the actual 89-mm export.
Every row in `visualization/stage_ii/qa/overlap_audit.csv` passes text--text,
text--mark and legend--data checks at both full and 89-mm widths. Final compiled
page contact sheets independently show no clipped labels, blank pages or
text--image overlap.

## Colour contract

Only white and `#3D3539`, `#0F9EA8`, `#008B82`, `#45728F`, `#8CD1B2` and
`#8B84A3` occur in exported SVG artwork. Crop identity, positive evidence and
inconclusive results also use position, labels, marker shape, line style or fill
style so colour is never the sole carrier of meaning.
