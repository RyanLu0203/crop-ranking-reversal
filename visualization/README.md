# Visualization

Issue #8 freezes the canonical Nature-style visual system. Run `make figures` to
regenerate five figures, three publication tables, source-data extracts,
editable SVG/PDF exports, 300-dpi PNGs, 600-dpi TIFFs, grayscale proofs,
checksums and evidence registries.

The authoritative contract is `figure_plan.md`; typography, dimensions and the
six permitted semantic colors are frozen in `configs/nature_style.yaml`.
`configs/visual_encoding.csv` records redundant hatch/marker encodings.

`src/crop_visualization/nature_figures.py` is the only canonical renderer. The
pre-existing `plotting.py` remains an unadmitted historical candidate: it is not
called by the generator, manuscript or registries and must not be used for
claims. Simulation Figures S1--S2 remain supplementary and `NONHEADLINE`
because none of five predeclared convergence rows passes. Empirical figures are
descriptive and do not identify acreage optimality, CVaR binding or causality.
