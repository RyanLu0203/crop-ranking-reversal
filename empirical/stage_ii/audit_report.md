# GOAL-15 empirical audit

## Scope and outcome

The strengthened analysis uses the admitted official panel only: 231 crop rows,
77 complete three-crop state-years, 26 states and 2022–2024. It adds four
definition-specific inversion-intensity families, 51 state-year transitions per
definition, rolling-origin lagged rankings, state and year heterogeneity,
leave-one-state-out robustness, definition agreement, national aggregation and
a prior-acreage inertia association. Every uncertainty interval is a
deterministic 95% percentile interval from 5,000 state-cluster bootstrap draws.

## Positive descriptive findings and retained nulls

Concurrent operating-margin inversion intensity is 0.597 (95% state-cluster
interval 0.494–0.697), but the level varies materially across definitions. The
top acreage crop changes in only 5 of 51 admitted transitions. Conversely, the
registered prior-score-top versus other-crop mean share-change contrast includes
zero for every definition. This null family is retained in full and prevents a
claim that lagged score leadership predicts aggregate share gains.

At national scale, operating-margin and standardized-revenue rankings show no
top reversal in any of the three years. Total-cost rankings differ in two of
three years, while national relative yield is tied across all crops by
construction. The aggregation conclusion is therefore definition-dependent,
not a universal national null.

## Model linkage and identification

Prior acreage share is used only as an observed inertia/exposure proxy. It is
not a budget, rotation, contract, equipment or capacity measure. E2 operational
allocations and KKT pressures and E6 information values remain model-generated
evidence. The admitted data do not identify a private feasible set, objective,
CVaR limit, dependence belief, causal mechanism or welfare effect. County
analysis is not performed because no governed county snapshot is admitted.

## Reproducibility

`python scripts/run_stage_ii_empirical.py` produces the complete result family.
`python scripts/verify_stage_ii_empirical_reproducibility.py` reproduced 19
artifacts byte-for-byte in two isolated executions. The fail-closed validator
checks 87 design, timing, cardinality, uncertainty, null-retention, aggregation,
lineage and identification conditions.
