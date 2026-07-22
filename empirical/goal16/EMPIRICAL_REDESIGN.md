# GOAL-16 frozen empirical redesign

## Freeze statement

This design was frozen before any extended-period or county-level result was
computed or inspected. The 2022--2024 Stage II outputs are known baseline
evidence; they are not used to select the new estimands, specifications,
subgroups or display rules below. Any post-freeze deviation requires a dated
amendment that preserves this version and explains the reason without reference
to the direction or significance of a result.

## Scientific question and evidence boundary

Primary descriptive question: where and under which pre-specified score
definitions do public rank--acreage inversions occur, and is prior rank
descriptively associated with subsequent acreage-share change?

The public data can identify published acreage, yield and accounting-based score
relations. They cannot identify farm objectives, private budgets, rotations,
contracts, expectations, downside-risk limits, copula beliefs, optimal acreage,
causal mechanisms or welfare.

## Source and extension hierarchy

1. Extend the state--crop--year panel backward and, if available, forward using
   the same authoritative USDA source families and consistent definitions for
   planted acreage, yield, marketing-year price, operating cost and total cost.
2. Attempt a county panel only if authoritative county acreage/yield data are
   retrievable without private credentials, reproducible from a stable source,
   legally redistributable, and compatible with all three crop definitions.
3. If either extension fails, preserve a machine-readable blocker record naming
   the missing series, geography/year, access condition and definition conflict;
   continue with the strongest defensible state panel.

No historical draft number, claimed 2005--2022 sample, Iowa-county count,
reversal count, threshold, shortfall or welfare value may enter this analysis.

## Inclusion and harmonization rules

- Crops: corn, soybeans and winter wheat only; wheat categories may not be
  silently substituted for winter wheat.
- Unit: state--crop--year for the main panel; each retained state--year must have
  all three crops with published planted acreage and yield.
- Missing published values, suppression codes and incompatible categories are
  not imputed.
- Economic inputs must be crop--year definitions consistently available for
  all three crops. National prices/costs remain explicit accounting inputs, not
  local realized margins.
- Monetary measures are converted to real dollars using one registered CPI-U
  vintage and base year.
- Time support is the maximal intersection of consistent state production,
  price, cost and CPI series. No year is dropped based on an outcome.
- Source revisions are retained by checksum and retrieval timestamp; raw files
  are immutable.

## Pre-specified score definitions

1. Relative yield: state yield divided by same-year national yield.
2. Standardized revenue: state yield times national same-year price, in real
   dollars per acre.
3. Operating margin: standardized revenue minus national operating cost per
   planted acre.
4. Total-cost margin: standardized revenue minus national total cost per planted
   acre.

Rank direction is descending. Average ranks are used for Kendall/Spearman tie
handling; top-rank disagreement is undefined when all crops tie and separately
flagged when the score leader is non-unique.

## Pre-specified estimands

### Concurrent rank disagreement

- Kendall's tau-b between score and acreage ranks within each state--year, with
  ties retained.
- Spearman rank agreement only when rank variance is positive; invalid/tied
  cases are counted and reported.
- Pairwise inversion intensity: discordant informative pairs divided by three,
  with the tied-pair count retained separately.
- Top-rank disagreement: disjoint score-leader and acreage-leader sets when the
  score leader is informative.
- Leader persistence: probability that score and acreage leader sets remain
  unchanged from `t-1` to `t`.
- Rank-transition disagreement: absolute and signed score-rank change compared
  with acreage-rank change at the crop-transition level.

### Temporal association

For each score definition and crop transition, estimate:

`acreage_share_change[t] ~ prior_score_top[t-1] + prior_acreage_share[t-1] + crop FE + year FE + state FE`

where estimable. A continuous prior rank or standardized prior score is a
pre-specified sensitivity, not a replacement chosen after results. All scores
strictly precede the outcome year; no contemporaneous score enters the primary
temporal model. Report coefficients as percentage-point share changes and label
them descriptive associations.

Cluster-respecting uncertainty uses state-cluster bootstrap with 5,000 draws
and a fixed registered seed. A cluster-robust covariance estimator is a
pre-specified sensitivity when the number of retained states is sufficient.

### Model-linked signatures

- Margin-separation signature: whether wider top-vs-second expected-margin gaps
  correspond descriptively to lower/higher rank--acreage disagreement.
- Allocation-persistence signature: prior acreage leader/share persistence and
  subsequent share change.
- Rank--share inversion signature: concurrent inversion, tau-b and top-rank
  disagreement under each definition.
- Aggregation-instability signature: difference between state summaries and
  national summaries under the same definition.

These are signatures compatible with model mechanisms, not mechanism tests.

## Sensitivity and falsification plan

- Leave one state out and leave one year out.
- Alternative tie handling: retain ties, exclude non-informative all-tie cells,
  and report both denominators.
- Complete-case support by state/year/crop and comparison with the raw published
  support.
- Alternative economic definition: nominal versus registered real-dollar base;
  ranks should be invariant within year, and any deviation is a processing
  failure.
- Top-vs-other contrast and continuous rank specification.
- State-cluster bootstrap seed replay and independent isolated rerun.
- National aggregation as a boundary analysis, never as a preferred benchmark.

## Missingness and measurement audit

Before analysis, produce:

- raw and retained row counts by source, crop, state and year;
- missing/suppressed/incompatible counts by variable and reason;
- earliest/latest consistent year by series;
- complete-case state-year support;
- source vintage, units, revision status and checksum;
- any mismatch between planted and harvested acreage concepts;
- county feasibility and redistribution/access decision.

## Required outputs

- `source_registry.csv`, raw checksums and retrieval log;
- `data_dictionary.csv` and tidy extended panel or exact blocker report;
- `sample_flow.csv`, `coverage.csv` and `missingness.csv`;
- `rank_metrics_state_year.csv` and clustered summaries;
- `leader_transitions.csv`, `rank_share_transitions.csv` and transition summary;
- `temporal_model.csv`, bootstrap draws/summary and sensitivity results;
- `model_linked_signatures.csv` and aggregation-boundary output;
- figure-ready source tables for Figure 6 and Supplementary Figure S5;
- generated-number registry, validation report and `SHA256SUMS.txt`.

Every manuscript number must be generated from these outputs; none may be typed
manually into TeX.

