# GOAL-16 post-reconstruction visual QA

## Outcome

All six main figures and five supplementary figures pass full-size and 89-mm
inspection. No title, panel label, axis label, tick label, legend, annotation or
caption text overlaps another text element or a plotted point, line, bar,
interval or shaded region. Legends that initially covered marks in Figures 4,
6, S2 and S3 were moved outside the data region or removed before this pass.

## Scale and accessibility review

| View | Result | Evidence |
|---|---|---|
| Full/183 mm | PASS | `visualization/stage_ii/qa/contact_sheet_full.png` |
| 89 mm | PASS | `visualization/stage_ii/qa/contact_sheet_width89mm.png` |
| Grayscale | PASS | `visualization/stage_ii/qa/contact_sheet_grayscale.png` |
| Deuteranopia | PASS | `visualization/stage_ii/qa/contact_sheet_deuteranopia.png` |
| Protanopia | PASS | `visualization/stage_ii/qa/contact_sheet_protanopia.png` |

The categorical meaning remains redundant with position, labels, markers,
line style or fill style. Small-width review uses the actual 89-mm resample,
not a browser-scaled full-width screenshot.

## Colour contract

The SVG validator found no colour outside white and the six supplied colours:
`#3D3539`, `#0F9EA8`, `#008B82`, `#45728F`, `#8CD1B2` and `#8B84A3`.
Corn, soybean and winter wheat retain their fixed semantic mappings. Positive
simulation evidence and inconclusive experiments use distinct registered
colours and are also distinguished by labels and placement.

## Scientific display checks

- Figure 3 uses signed KKT point-line pressure terms, not a heatmap.
- Figure 4 contains E2 only; E3 appears only in Supplementary Figure S2.
- Figure 5 contains E6 only; E5 appears only in Supplementary Figure S3.
- Figure 6 uses a ranked state dot plot backed by official NASS state records,
  reports definition sensitivity and strictly lagged intervals, and labels the
  aggregation boundary without implying a map-based precision not present in
  the data.
- Supplementary Figures S1--S5 implement the frozen E1, E3, E4/E5, numerical
  integrity and empirical-robustness split.
