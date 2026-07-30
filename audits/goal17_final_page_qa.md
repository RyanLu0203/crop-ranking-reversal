# Final manuscript-page QA

## Scope and result

- Main manuscript: **16 pages**.
- Supplementary Information: **11 pages**.
- Every page rendered at 144 dpi; blank pages: **0**.
- Full combined page contact sheet: `output/qa/contact_all_pages.png`.

## QA checklist

| Check | Evidence | Result |
|---|---|---|
| Manuscript font hierarchy | 11 pt body; 10 pt captions; 9 pt references | PASS |
| Minimum effective figure font | Native minimum 5.50 pt; embedded scale 0.923; effective minimum 5.08 pt | PASS (>= 5.0 pt) |
| Caption accuracy | Figure 3 states native units; Figure 5 declares exact-null tolerance; Figure 6 panel a is a state map | PASS |
| Label overlap / clipping | Renderer bounds failures 0; title collisions 0; all pages rendered and inspected | PASS |
| Lagged coefficient units | `audits/goal17_unit_consistency_audit.csv` and `.md` | PASS |
| Stale figure text | No normalized/indexed Figure 3 wording; no ranked-state-dot-plot Figure 6 wording | PASS |
| Visual balance and whitespace | Full-page contact-sheet inspection; no blank or isolated spill pages | PASS |
| Colour-card consistency | SVG/PDF palette validator | PASS |
| Grayscale and CVD readability | Full, grayscale, deuteranopia and protanopia contact sheets generated | PASS |

## Page-render artifacts

- `output/qa/contact_all_pages.png`
- `output/qa/contact_main_01.png`
- `output/qa/contact_main_02.png`
- `output/qa/contact_main_03.png`
- `output/qa/contact_main_04.png`
- `output/qa/contact_main_all.png`
- `output/qa/contact_supplementary_01.png`
- `output/qa/contact_supplementary_02.png`
- `output/qa/contact_supplementary_03.png`
- `output/qa/contact_supplementary_all.png`

## Focused visual findings

- Figure 1 now separates observed objects, decision-system assumptions, model outputs and nested identified claims without a requirement matrix.
- Figure 2 uses four shared-coordinate simplex panels; each exposes a feasible region, common rank boundary, objective direction and optimal point or face.
- Figure 4 preserves all scientific panels at 183 mm while giving the intervention-to-allocation response the primary row and separating supporting contrast and KKT panels.
- Figure 5 displays the dominated-option interaction as exact zero at a declared `1e-12` display tolerance; no scientific-notation noise axis remains.
