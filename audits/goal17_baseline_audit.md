# GOAL-17 baseline audit and reconstruction freeze

## Frozen starting point

- Branch: `codex/goal17-high-information-nature-scientific-deepening`.
- Parent commit: `fe55149d0021511cc5e7a704d4da8579f029e284` (the clean GOAL-16 scientific reconstruction head).
- Main manuscript: 12 pages, approximately 3,194 prose words.
- Supplement: 9 pages, approximately 2,378 prose words.
- Empirical frame: official 2016--2024 data, 31 states, 248 complete state-years.
- Confirmatory boundary: E2 and E6 support promoted conclusions; E1, E3, E4 and E5 remain inconclusive. All 206 infeasible outcomes remain visible in the evidence ledger.

This branch deepens the scientific presentation without overwriting or force-pushing the GOAL-16 review branch. The final deliverable will be a new unmerged Draft pull request.

## Baseline scientific strengths to preserve

1. The central claim is already disciplined: score rankings are not allocations without cardinal payoffs, uncertainty, feasibility and an optimizer-selection rule.
2. The model distinguishes an optimal face from an arbitrarily selected solution and separates possible, universal and selected reversal.
3. E2 identifies operational constraints as a reversal mechanism, while E6 demonstrates that information and flexibility need not be complementary.
4. The empirical analysis is explicitly descriptive and never treats observed acreage as the solution to the paper's optimizer.
5. Generated numbers, claims, figures and tables are linked to versioned registries and reproducible source tables.

## Baseline gaps GOAL-17 must close

### Visual evidence

- The six main groups are clean but too conservative for the information density of the argument.
- Several panels allocate too much area to prose cards or one-dimensional diagrams.
- Figure 4 uses compact treatment codes; Figure 5 overloads six lines in one axes; Figure 6 underuses geography and previously allowed an annotation to enter the point field.
- Main and supplementary evidence need a stronger editorial hierarchy, especially for promoted versus inconclusive experiments.

### Scientific narrative

- Literature positioning is compressed and should explicitly connect crop planning, CVaR, dependence modelling, predict-then-optimize learning, value of information/flexibility and rank-based recommendation.
- The stochastic program, CVaR linearization, geometry of the optimal face, reversal definitions, selection rule and KKT interpretation need a more continuous main-text derivation.
- E2 and E6 require fuller design-to-estimand-to-result narratives.
- Empirical sections should integrate sample flow, definition sensitivity, state/year heterogeneity, lagged specifications, persistence, transitions, aggregation, leave-one-state-out and missingness evidence.
- Discussion and Conclusion should distinguish identified mechanisms, descriptive observations and unresolved boundaries without repository/audit jargon.

## Reconstruction targets

- Main manuscript: approximately 14--18 scientifically justified pages, with no padding.
- Supplement: substantial proofs, complete experiment ledgers, adverse results, empirical robustness, maps/transitions and reproducibility details.
- Main figures: six 183-mm editorial composites, each answering one scientific question.
- Candidate requirement: at least two meaningfully different, final-size concepts per main group, retained in a checksum-backed contact sheet and compared in `audits/goal17_visual_exploration.md`.
- Exports: editable SVG/PDF, 300-dpi PNG and 600-dpi TIFF.

## Non-negotiable visual constraints

1. Exact palette: `#3D3539`, `#0F9EA8`, `#008B82`, `#45728F`, `#8CD1B2`, `#8B84A3`.
2. Body labels 6--7 pt; no essential text below 5.5 pt; bold lowercase panel labels.
3. Text and graphical marks must not overlap. Text belongs in reserved annotation lanes, outside plotting domains, or at collision-tested direct-label positions.
4. No label, legend, annotation, panel marker or axis title may be clipped at final size.
5. Grayscale, deuteranopia and protanopia views must preserve interpretation through position, shape, hatch or line style rather than colour alone.
6. All final charts remain Python/matplotlib-native; raster images are not used as scientific source material.

## Completion evidence

Completion requires: candidate and final visual manifests; full-size and accessibility contact sheets; overlap/bounds QA; manuscript and supplement compilation; all repository validators; archive file count and SHA-256; exact branch and commit; and a new Draft pull request that remains unmerged.

