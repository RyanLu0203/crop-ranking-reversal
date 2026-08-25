# Final editorial figure contracts

This pass preserves the approved claims, simulations, empirical sample and
evidence classification. All final figures remain Python/Matplotlib products
at a native width of 183 mm and use the approved colour card.

## Figure 1 — inference architecture

- Core conclusion: an observed rank--allocation mismatch is descriptive until
  cardinal payoffs, joint uncertainty, feasibility and the optimal face are
  supplied; a selected claim additionally needs a selection rule.
- Visual archetype: layered inference field, nested claim hierarchy and a
  compact optimal-face geometry strip.
- Evidence hierarchy: observed objects -> decision-system assumptions ->
  model outputs -> identified claims.
- Reviewer risk controlled: avoid a checklist or pipeline that falsely implies
  that observed acreage alone reveals the private decision system.
- Source: exact definitions and theorem statements in the manuscript.

## Figure 2 — mechanism atlas

- Core conclusion: the same rank--allocation reversal can arise through four
  geometrically distinct mechanisms.
- Visual archetype: 2 x 2 small-multiple feasible-set atlas in a common
  Corn-share/Soybean-share simplex.
- Required marks in every panel: feasible region, common rank boundary,
  objective direction, and optimal point or optimal face.
- Mechanism-specific geometry: cardinal objective rotation; operational
  clipping; downside-risk truncation; set-valued crossing face.
- Reviewer risk controlled: no inference from visually identical one-
  dimensional interval strips.
- Source: exact constructive examples summarized in
  `visualization/stage_ii/source_data/figure2_geometry.csv` and manuscript
  theory.

## Figure 4 — operational evidence composite

- Core conclusion: assigned operational interventions force universal reversal
  in the controlled domain, with all 24 family-wise intervals meeting their
  precision criterion.
- Visual archetype: aligned intervention-to-allocation hero matrix, supporting
  outcome forests, then local pressure fingerprint and compact result facts.
- Hierarchy: allocation response is primary; margin/mechanism are secondary;
  intervals and pressure identities are confirmatory support.
- Reviewer risk controlled: preserve all scientifically useful content while
  separating row labels, titles and graphical marks at 183 mm.
- Source: Figure 4 source CSVs and exact KKT summaries.

## Figure 5 — information/flexibility interaction

- Core conclusion: information and action-set flexibility may complement,
  substitute or have an exact-null interaction.
- Visual archetype: three archetype response columns plus interval forest and
  finite-state invariants.
- Exact-null rule: interaction values with absolute magnitude below
  `1e-12` are displayed as exactly zero and explicitly labelled; raw source
  values remain unchanged.
- Reviewer risk controlled: no floating-point scientific-notation axis that
  visually exaggerates numerical noise.
- Source: Figure 5 information summary and interaction CSVs.

