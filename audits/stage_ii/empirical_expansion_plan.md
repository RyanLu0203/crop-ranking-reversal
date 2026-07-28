# GOAL-15 empirical expansion plan

## Purpose and status

This is the Issue #25 redesign blueprint. It does not authorize downloads or
analysis in GOAL-11. The Stage I 2022--2024 complete-case state sample remains a
valid descriptive baseline and must not be overwritten. A Stage II empirical
design requires a new identifier, frozen source registry, estimand registry,
checksum ledger and pre-result analysis plan.

The empirical goal is model-linked validation, not recovery of an unobserved
representative-farmer optimum.

## Evidence layers

Every variable and claim must be assigned to one layer.

1. **Directly observed:** official planted acreage, yield, geography, crop year,
   publication vintage and any other field present in an admitted snapshot.
2. **Constructed accounting:** transformations using geography/time-aligned
   official price and cost inputs; never relabelled realized farm profit.
3. **Operational proxy:** an observed measure with a documented but imperfect
   link to budget, rotation, contract or flexibility; proxy error is explicit.
4. **Model generated:** allocation, CVaR, shadow price, active constraint or
   counterfactual produced by the optimization model.
5. **Unidentified:** private constraints, objectives, beliefs, risk limits,
   contracts or causal mechanisms without admitted measurement/design.

No figure or regression may combine layers without visible labels.

## Data expansion priorities

### P1 — Longer official acreage and yield panel

Retrieve a versioned state-year panel for corn, soybeans and winter wheat from
an authoritative USDA source with stable query/download records. Prefer the
longest common period with consistent definitions and publication vintages.
Store immutable raw responses and record revisions, suppression codes,
geographic coverage and schema changes. County analysis is optional and may
proceed only if coverage and confidentiality/suppression patterns pass a
separate audit.

### P2 — Pre-decision score inputs

Scores must use information available before the acreage decision. Candidate
classes are lagged yield/suitability summaries, official soil/land capability,
weather/climate forecasts with archived issue dates, and lagged or forecast
economic inputs. Contemporaneous realized yield cannot support a predictive or
decision-timing claim.

### P3 — Geography-matched economics

Investigate official state or Farm Resource Region price/cost information and
record whether crops share compatible coverage. If geography-matched inputs are
not jointly available, retain national standardized accounting and treat
geographic mismatch through partial identification/sensitivity rather than
silent downscaling.

### P4 — Operational and flexibility variables

Create a source feasibility matrix before analysis. Potential observables may
include lagged crop shares/rotation exposure, insured or prevented acreage,
credit/input-cost exposure, irrigation or land capability, and policy/program
status when authoritative and correctly timed. They are proxies unless they
directly observe a constraint. Private budgets, contracts and farmer CVaR
limits remain unavailable unless a new validated data source is obtained.

## Primary empirical questions and estimands

### E1 — Ranking-definition robustness

Compare preregistered agronomic, revenue, operating-margin, total-cost and
lagged/pre-decision rankings. Outcomes must include top-rank mismatch, strong
mismatch, pairwise inversions, rank correlation and continuous acreage-share
distance. Report tie handling and denominator for every result.

### E2 — Acreage transitions

Use within-geography crop-share changes as the primary dynamic outcome. Test
whether changes in pre-decision score levels, ranks and cardinal gaps precede
changes in acreage shares. Separate entry/exit, rank crossing and continuous
adjustment. Do not call a slow response irrational without measuring adjustment
costs or constraints.

### E3 — Geographic heterogeneity

Estimate prespecified heterogeneity by region and observable production context
using partial pooling or multiplicity-controlled summaries. Report sample
coverage and uncertainty; do not rank states using cells with materially
different denominators as if precision were equal.

### E4 — Temporal robustness and validation

Use rolling-origin evaluation with fixed training windows, pre-decision vintages
and year-block uncertainty. Include leave-period-out, early-versus-late regime,
and data-vintage checks where multiple official vintages exist. A two-year
training window is retained only as a Stage I baseline, not the Stage II primary
validation.

### E5 — Operational-pattern consistency

Map theory predictions to observable proxies before fitting models. Examples
include slower crop-share adjustment under tighter rotation/inertia proxies or
different score-to-share slopes under observable flexibility. These are
consistency tests unless an exogenous design is available. They cannot identify
the private constraint's shadow price.

### E6 — Risk/dependence-pattern consistency

Using synchronized longer-horizon profit proxies, estimate ordinary and tail
co-movement with uncertainty and test whether model-predicted high-tail-exposure
contexts show different diversification or adjustment patterns. The empirical
analysis must not infer a farmer's CVaR limit, risk aversion or copula causality.

### E7 — Aggregation and external validity

Reconcile farm/county/state/national interpretation wherever those layers are
available. Reproduce the Stage I national null, quantify aggregation sensitivity
and avoid extrapolating complete-case results to omitted states or farms.

## Model-linked prediction registry

Before estimation, GOAL-15 must create a registry with these fields:

`prediction_id`, `theory_result_id`, `simulation_estimand_id`, `observable`,
`timing`, `geography`, `expected_pattern`, `alternative_explanations`,
`identification_status`, `model_specification`, `uncertainty_method`,
`falsification`, `claim_language` and `figure_panel`.

The registry must include negative controls and null predictions. A result that
does not map to this registry can be exploratory only.

## Statistical design

- Freeze inclusion, missingness, tie and revision rules before results.
- Use uncertainty appropriate to repeated observations within geography and
  common crop-year shocks; document clustering or block bootstrap choices.
- Report exact sample sizes, interval definitions and the unit of replication.
- Separate model tuning, specification selection and final temporal/geographic
  holdout periods.
- Control the declared family of heterogeneity and interaction tests.
- Use effect sizes and uncertainty rather than significance-only selection.
- Retain national nulls, contradictory definitions and weak/zero associations.

The combinatorial two-thirds reference may remain a descriptive ordering
benchmark, but it is not a sampling null unless a defensible randomization model
is newly specified.

## Identification ladder

Each empirical statement receives exactly one status:

- `DESCRIPTIVE_IDENTIFIED`: directly observed distribution or transition.
- `ACCOUNTING_IDENTIFIED`: reproducible accounting transform with explicit input
  mismatch.
- `MODEL_CONSISTENT_ASSOCIATION`: observed pattern matches a preregistered model
  prediction but alternatives remain.
- `PARTIALLY_IDENTIFIED`: bounded conclusion under explicit missing inputs.
- `CAUSAL_IDENTIFIED`: requires a separately defended exogenous design; no Stage
  I result has this status.
- `NOT_IDENTIFIED`: mechanism or parameter cannot be recovered from admitted data.

GOAL-15 is successful even if risk, constraint or information mechanisms remain
not identified, provided the observable tests are strong, preregistered and the
boundaries are not hidden.

## Required robustness and negative evidence

- alternative ranking definitions and score scales;
- alternative crop sets and complete-case rules;
- leave-year/leave-period and rolling-origin checks;
- geographic holdouts and aggregation sensitivity;
- price/cost geography and deflator sensitivity;
- data-vintage or revision analysis when possible;
- lag length and adjustment-window sensitivity;
- tie, entry/exit and suppressed-observation sensitivity;
- placebo timing using information unavailable at the true decision date;
- national and low-coverage nulls retained visibly.

## Output and lineage contract

Every result must trace through official snapshot, immutable checksum, processing
code, design configuration, execution record, tidy output, figure/table source
data and claim registry. Required deliverables are:

- data-source feasibility and license matrix;
- immutable raw manifests and query/download commands;
- processed-panel specification and schema;
- prediction/estimand registry;
- sample-flow and missingness outputs;
- transition, heterogeneity, temporal, risk and aggregation outputs;
- robustness and null-result tables;
- two isolated end-to-end replays;
- claim-boundary and model-link audits;
- source-data bundles for Figure 6 and Extended Data.

## Promotion gates

An empirical result may enter the main text only if:

1. its source, timing, geography and units pass governance;
2. its estimand and model prediction were frozen before result inspection;
3. uncertainty matches the sampling/dependence structure;
4. holdout or temporal robustness is adequate for the exact claim;
5. observable, proxy, model-generated and unavailable inputs are distinguished;
6. null and contradictory results are retained;
7. causal, welfare, optimality and CVaR claims do not exceed identification; and
8. the full lineage and independent replay pass.
