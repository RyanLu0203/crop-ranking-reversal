# Issue #40 final visual QA

Status: **PASS**

Manual inspection was performed after the deterministic final figure and
manuscript builds. The review covered Figures 1--6, Supplementary Figure 1,
all 22 main-manuscript pages and all 8 Supplementary Information pages.

## Figure checks

- Final figure width is 183 mm; separate 89 mm and 183 mm review renders were
  inspected.
- Ordinary figure text is 5.4--7.0 pt, panel labels are 8 pt and figure titles
  are 9 pt. The 4.06 pt SVG minimum is confined to automatically scaled
  mathematical super/subscripts.
- Full-colour, grayscale, deuteranopia and protanopia contact sheets retain the
  intended categorical and signed distinctions. Marker, line, hatch and symbol
  redundancy prevents colour-only interpretation.
- The renderer reports zero out-of-bounds text elements and zero title
  collisions for all seven figures.
- PDF and SVG outputs retain editable vector text and elements; PNG and
  publication-grade 600-dpi LZW TIFF outputs are also present.
- Figure 6a and 6c rainclouds are based on the real 5,000-draw state-cluster
  bootstrap distributions. Their fixed 72-draw display subsets, IQRs, medians,
  observed estimates and 95% intervals remain readable at 89 mm. No density is
  fabricated for the distinct 62/64 binomial estimand in Figure 6b.

## Compiled-page checks

- Main manuscript pages 1--22: no clipped figures, captions, equations, tables,
  headings, footers or references; no unintended overlaps; Figure 6 and its
  expanded caption fit cleanly on page 15.
- Supplementary Information pages 1--8: no clipped or overlapping content;
  tables remain within the text block and Supplementary Figure 1 is legible on
  page 7.
- Final logs contain no overfull boxes, undefined citations or undefined
  references.

The contact sheets and page-detail sheets are retained under
`audits/issue40_visual_qa/`.
