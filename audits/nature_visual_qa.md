# Nature visual-system QA

## Scope and result

Issue #8 defines five canonical figures and three publication tables. The visual
system reads only verified Issue #6 simulation outputs and Issue #7 empirical
outputs. `make figures` regenerates every artifact and runs the mandatory
validator. The final visual, grayscale, dimensional, accessibility, provenance
and evidence-boundary checks pass.

## Evidence boundary

- Figure 1 separates ordinal ranking, cardinalization, feasibility, the optimal
  face and optimizer selection. Possible and universal reversal are face
  properties; selected reversal is solver-dependent.
- Figure 2 reports descriptive discordance for 26 states and 77 state-years.
  The exact 2/3 permutation result is labelled a combinatorial reference, not a
  sampling null. The national comparison is a null descriptive check (0/9).
- Figures S1 and S2 are supplementary and `NONHEADLINE`: no convergence row
  passes the frozen numeric-plus-precision gate (0/5), even though independent
  replay (450/450) and solver sensitivity (9/9) pass.
- Figure S3 is descriptive robustness evidence. It does not identify observed
  acreage as optimal, CVaR binding, a copula mechanism or causality.

## Technical QA

- Width: all figures are exactly 183 mm; heights are 120, 150, 140, 105 and
  120 mm for Figures 1, 2, S1, S2 and S3.
- Vector: SVG retains editable text and shapes and contains no embedded raster;
  PDF uses TrueType font embedding.
- Raster: PNG is 300 dpi and TIFF is 600 dpi with LZW compression.
- Accessibility: every semantic color has a label, hatch, marker, edge or direct
  annotation. Five grayscale proofs and a contact sheet were inspected.
- Provenance: per-artifact SHA-256 ledgers and a source-data lineage registry
  bind derived extracts to frozen upstream inputs.
- Legacy isolation: `visualization/src/crop_visualization/plotting.py` is not
  called by the canonical generator and remains unadmitted.

## Reproduction

```sh
make figures
```

The same command regenerates source data, figures, tables, captions, QA records,
checksums, and figure/table evidence registries before validation.
