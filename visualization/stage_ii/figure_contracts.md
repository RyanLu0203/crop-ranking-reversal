# GOAL-13 Stage II figure contracts

## Global contract

- Target: Nature Food research article, six double-column main figure groups.
- Backend: Python/matplotlib exclusively for plotting, previews, exports and QA.
- Final width: 183 mm; height 118--158 mm; editable SVG and PDF, 300-dpi
  PNG, 600-dpi TIFF.
- Typography: Arial-compatible sans serif, 5.8--7.2 pt body, bold lowercase
  8-pt panel labels.
- Colour: user-supplied six-colour journal card (`#3D3539`, `#0F9EA8`,
  `#008B82`, `#45728F`, `#8CD1B2`, `#8B84A3`) with only documented light
  tints and neutral grey for adverse/unidentified evidence.
- Statistics: exact replication unit and n; declared family-wise intervals where
  inherited from GOAL-12; descriptive 95% t intervals only for closed
  attribution summaries; no unsupported p-values.
- Evidence boundary: E2 and E6 may support positive main-text conclusions. E1,
  E3, E4 and E5 remain adverse/non-promoted and must display the failed gate.
- Image integrity: every chart is vector-native; no raster source image, local
  contrast adjustment, smoothing, manual data positioning or hidden failed row.
- Reviewer risk: model outputs are synthetic evidence, observed acreage is not
  an optimizer, and KKT pressures are local optimality terms rather than
  acreage-causal shares.

## Figure 1 — Rankings become decisions only through added structure

Core conclusion: an ordinal ranking requires cardinal payoffs, uncertainty,
feasibility and optimizer selection before it can imply an allocation.

- Archetype: schematic-led composite.
- Panel a (hero): ranking-to-allocation architecture with observed, calibrated,
  design-controlled and latent inputs.
- Panel b: possible, universal and selected reversal as distinct properties of
  an optimal face.
- Panel c: theory → controlled simulation → descriptive observation evidence
  ladder and five scientific questions.
- Evidence hierarchy: GOAL-14 definitions; no numerical inference.
- Source data: `figure1_architecture.csv`, `figure1_definitions.csv`.

## Figure 2 — Distinct mechanisms reshape the optimal face

Core conclusion: margins, operational bounds and downside risk generate
geometrically distinct movement or truncation of the optimal face, while a
set-valued optimum separates possible from universal reversal.

- Archetype: asymmetric mixed-modality figure.
- Panel a (hero): common two-crop feasible line and ranking half-space.
- Panels b–e: margin-driven, operation-forced, risk-limited and set-valued exact
  cases.
- Evidence hierarchy: analytic geometry and GOAL-14 definitions; selected
  points never substitute for the full optimal set.
- Source data: `figure2_geometry.csv`.

## Figure 3 — Model blocks yield auditable, non-unique contributions

Core conclusion: the M0–M4 path changes allocation, profit and downside risk,
and all-subset attribution closes those changes without pretending that one
block order is causal or unique.

- Archetype: quantitative grid with dominant nested-model panel.
- Panel a (hero): mean crop allocation across M0–M4, n=16 closed-domain seeds.
- Panel b: expected-profit and CVaR paths with descriptive 95% t intervals.
- Panel c: all-subset Shapley allocation contributions with efficiency closure.
- Panel d: E2 KKT pressure terms by predeclared mechanism class.
- Source data: `figure3_nested_summary.csv`, `figure3_shapley_summary.csv`,
  `figure3_pressure_summary.csv`.

## Figure 4 — Operational constraints identify reversal; risk remains adverse

Core conclusion: predeclared E2 operational interventions produce universal
Corn–Soybean reversal with precise allocation shifts, whereas the E3 risk
frontier does not clear its experiment-level precision gate.

- Archetype: asymmetric quantitative grid.
- Panel a (hero): E2 factorial operational cells and mean allocations.
- Panel b: selected/possible/universal optimal-face classifications.
- Panel c: E2 allocation and profit contrasts with family-wise intervals.
- Panel d: E3 risk contrasts shown in grey with replication ceiling, uncertainty
  and `PRECISION FAILED` status.
- Source data: `figure4_e2_cells.csv`, `figure4_e2_contrasts.csv`,
  `figure4_e3_adverse.csv`.

## Figure 5 — Information value is flexibility-dependent, not universally complementary

Core conclusion: better information can complement flexibility, be exactly
null, or substitute for flexibility; cross-law diversification comparisons
remain a non-promoted model-sensitivity boundary.

- Archetype: asymmetric mixed-modality figure.
- Panel a (hero): E6 value of information by precision and action set.
- Panel b: positive, null and substitution interactions with family-wise
  intervals.
- Panel c: exact ignore-signal and Blackwell-garbling checks.
- Panel d: E5 true/assumed-law risk-violation matrix, visibly hatched and labelled
  `EXPERIMENT PRECISION FAILED`.
- Source data: `figure5_information_summary.csv`,
  `figure5_information_interaction.csv`, `figure5_dependence_boundary.csv`.

## Figure 6 — Observed transitions are weak while discordance remains heterogeneous

Core conclusion: the registered lagged top-score transition contrast includes
zero under every definition, whereas concurrent rank–acreage discordance varies
by definition, state, year and aggregation; these facts do not reveal private
objectives or constraints.

- Archetype: asymmetric quantitative grid.
- Panel a (hero): prior-score-top versus other-crop mean acreage-share change
  across 51 state-year transitions per definition, with 5,000-draw
  state-cluster intervals.
- Panel b: concurrent inversion intensity with state distributions and
  state-cluster intervals, n=77 state-years.
- Panel c: definition-by-year inversion-intensity heatmap.
- Panel d: state versus national aggregation comparison, retaining national
  relative-yield ties and definition-dependent nulls.
- Source data: admitted GOAL-15 outputs copied into the versioned source-data
  package; observed, model-generated and unidentified constructs remain
  separate.

## Supplementary allocation

- Figure S1: all E1–E6 stopping/precision outcomes.
- Figure S2: adverse E3/E4/E5 contrast inventory and certified infeasibility.
- Figure S3: replay, solver, KKT, checksum and resource diagnostics.
- Figure S4: attribution order sensitivity and exact Shapley closure.
