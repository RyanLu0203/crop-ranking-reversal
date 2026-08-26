# GOAL-17 visual contracts and candidate freeze

## Shared rendering contract

- Backend: Python/matplotlib exclusively for generation, preview, export and QA.
- Final width: 183 mm. Every candidate is rendered at this width before selection.
- Typography: Arial-compatible sans serif, 6.0--7.0 pt text, 8-pt bold lowercase panel labels; no essential text below 5.5 pt.
- Palette: Corn `#45728F`; Soybean `#008B82`; Winter wheat `#8CD1B2`; supported confirmatory evidence `#0F9EA8`; inconclusive/adverse/unidentified evidence `#8B84A3`; text, axes and neutral structure `#3D3539`.
- Statistical grammar: points and intervals for estimands; distributions for heterogeneity; explicit zero or identity references; actual units unless an index is declared.
- Evidence grammar: promoted evidence uses teal with redundant filled/solid encoding; inconclusive evidence uses violet-grey with open/hatched encoding; unidentified objects use charcoal outlines or dashes.
- Collision rule: graphical marks are clipped to their axes; titles, captions and direct labels occupy reserved lanes. Automated artist-bounds checks and raster inspection must report zero text--mark overlaps and zero clipping.

## Figure 1 — From ranking to identified allocation claims

**Scientific question.** What additional structure is required before an ordinal crop ranking can imply an allocation or a ranking reversal?

**Source and estimand.** Formal definitions and model objects; no empirical estimand.

**Intended takeaway.** Cardinal payoffs, uncertainty, feasibility, the optimal face and a selection rule are distinct inferential layers; possible, universal and selected reversal are not interchangeable.

- Candidate A — **allocation fan**: an asymmetric left-to-right architecture with a dominant ranking-to-optimal-face fan, a compact identification ladder and a shared reversal axis.
- Candidate B — **claim matrix**: a rows-by-assumptions matrix showing which claims become available as structure is added, paired with an optimal-face strip and selected-solution glyphs.
- Reviewer risk: excessive prose or implying that one ranking uniquely determines an allocation.
- Selection criterion: maximum conceptual density with the fewest prose blocks and a visually dominant identification boundary.

## Figure 2 — Geometry of ranking reversal

**Scientific question.** How do margins, operational constraints, downside risk and non-unique optima alter the feasible or optimal set?

**Source and estimand.** Exact analytic cases in `figure2_geometry.csv`; feasible polyhedra and optimal faces, not Monte Carlo estimates.

**Intended takeaway.** The mechanisms are geometrically distinct: objective rotation, feasible-set truncation, risk-boundary truncation and a face crossing the ranking boundary.

- Candidate A — **coordinated simplex atlas**: four small multiples sharing barycentric coordinates, a common ranking boundary and mechanism-specific objective/constraint overlays.
- Candidate B — **common domain plus mechanism fingerprints**: one large shared feasible triangle with four inset difference strips showing before/after feasible and optimal sets.
- Reviewer risk: showing only selected points and hiding set-valued optima; decorative geometry without visible objective or constraint changes.
- Selection criterion: immediate before/after comparison, explicit optimal faces and no dependence on colour alone.

## Figure 3 — What changes across the model sequence

**Scientific question.** How do M0--M4 alter allocation, expected profit, tail risk and the accounting of model-block contributions?

**Source and estimand.** `figure3_nested_summary.csv`, `figure3_shapley_summary.csv`, `figure3_pressure_summary.csv`; n=16 closed-domain seeds; descriptive t intervals and exact accounting checks.

**Intended takeaway.** Operational structure changes the allocation path, outcome quantities stay in their native units, all-subset attribution closes the change, and KKT pressure terms describe local balance rather than causal acreage shares.

- Candidate A — **stage river**: a dominant allocation ribbon across M0--M4 with aligned native-unit outcome tracks, a compact attribution forest and signed KKT bars.
- Candidate B — **stage columns**: five vertical model columns containing mini-compositions, profit/risk dots and active-pressure glyphs, followed by a separate contribution summary.
- Reviewer risk: normalized or dual axes that falsely commensurate profit and risk; attribution language that sounds causal.
- Selection criterion: strongest stagewise continuity with exact-unit readability and closed accounting.

## Figure 4 — Operational identification of reversal (E2)

**Scientific question.** Which operational interventions identify universal Corn--Soybean reversal, and through which active constraints?

**Source and estimand.** `figure4_e2_cells.csv` and `figure4_e2_contrasts.csv`; allocation and profit contrasts with registered family-wise intervals.

**Intended takeaway.** Predeclared operational interventions move the feasible/optimal face and produce precise universal reversal; E3 remains outside the main figure.

- Candidate A — **intervention matrix**: descriptive intervention names, binary design matrix, mini allocation compositions, optimal-face classification glyphs and an effect-size forest.
- Candidate B — **feasible-set storyboard**: three representative pre/post feasible regions plus a compact full factorial matrix, active-constraint/KKT bars and the confirmatory forest.
- Reviewer risk: cryptic B/R/C codes, repetitive stacked bars or visual parity between E2 and failed E3 evidence.
- Selection criterion: descriptive labels, direct mapping from intervention to mechanism and a dominant confirmatory estimand panel.

## Figure 5 — Information value under flexible action sets (E6)

**Scientific question.** When does better information complement, leave unchanged or substitute for action flexibility?

**Source and estimand.** `figure5_information_summary.csv`, `figure5_information_interaction.csv`, exact finite-state checks; value of information and interaction contrasts with family-wise intervals.

**Intended takeaway.** Complementarity is not universal: the interaction is positive, exactly null or negative across registered archetypes.

- Candidate A — **archetype columns**: three aligned VOI panels, each with only low/high flexibility directly labelled, followed by an interaction forest and exact-check strip.
- Candidate B — **decision-timing schematic**: a compact signal-to-action tree feeding three payoff/action-set tiles, paired with interaction slopes and the confirmatory forest.
- Reviewer risk: a six-line legend, conflating VOI level with the flexibility interaction or placing E5 on equal footing.
- Selection criterion: effortless archetype comparison, direct labels in reserved margins and visible exact invariants.

## Figure 6 — Geographic, temporal and definitional empirical heterogeneity

**Scientific question.** Where and when does descriptive rank--acreage discordance occur, and does prior score leadership predict subsequent acreage change?

**Source and estimand.** Official 2016--2024 state data; 31 states and 248 complete state-years; state summaries, annual summaries, lagged transition contrasts, persistence, aggregation and leave-one-state-out outputs. Official Census state geometry is used only for spatial display.

**Intended takeaway.** Concurrent discordance is heterogeneous across definitions, states and years, while every registered lagged interval includes zero; neither observation identifies private objectives or constraints.

- Candidate A — **map-led composite**: a large state choropleth with a definition-sensitivity distribution, lagged forest, transition glyphs and state-versus-national aggregation dumbbells.
- Candidate B — **distribution-led composite**: ranked-state distributions and annual small multiples as the hero, with a compact map, transition alluvial and sample/aggregation strips.
- Reviewer risk: treating a choropleth as causal evidence, obscuring missing states or allowing annotations to enter the map/point field.
- Selection criterion: geographic pattern is legible without crowding, all non-data text remains in dedicated lanes and the null lagged result is visually prominent.

## Candidate comparison record

The two concepts for each figure will be rendered into `audits/goal17_visual_candidates/` at final width. `audits/goal17_visual_exploration.md` will record final-size strengths, weaknesses, density, accessibility, collision checks and the selected or hybrid design. The contact sheet and checksum manifest remain versioned even after final figures are implemented.
