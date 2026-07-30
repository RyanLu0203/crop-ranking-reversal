# GOAL-12 confirmatory simulation redesign

## Purpose and status

This is a prospective design specification for Issue #22, not authorization to
run the experiment in GOAL-11. Stage I remains a pilot/software-validation
dataset. The new design must receive a new identifier, frozen configuration,
checksum and supersession note before any confirmatory result is inspected.

The confirmatory simulation must answer mechanism questions, not estimate a
representative farmer or recreate the teacher Draft's values.

## Why the Stage I design cannot simply be enlarged

The 90-cell Stage I design is balanced across family labels but jointly varies
Kendall dependence, CVaR confidence, risk-frontier quantile, budget tightness,
dominant-crop cap, contract minimum and marginal family. It is a useful global
sensitivity pilot. It does not isolate CT4, CT6 or CT7, and its crossing sets are
explicitly mixed-factor. Five replications per cell do not estimate binary
probabilities precisely, and zero of five convergence rows passed. Adding seeds
without changing the estimand structure would increase computation without
creating mechanism identification.

## Confirmatory estimands

Each estimand must be defined before cell generation.

| ID | Estimand | Unit | Primary contrast | Required uncertainty | Claim boundary |
|---|---|---|---|---|---|
| S01 | Selected, possible and universal reversal | binary/set class | treatment versus matched control | Wilson or simultaneous multinomial interval plus face tolerance | Simulation design only |
| S02 | Allocation displacement | land share | L1 and crop-specific difference between nested models | independent-replication interval | Selection and face range reported |
| S03 | Expected-profit opportunity cost | real calibrated units per normalized acre | richer model minus reference | interval across independent scenario draws | Not welfare |
| S04 | True-law loss-CVaR change | real calibrated units per normalized acre | policy evaluated under declared data-generating law | interval and Monte Carlo error | Not farmer realized risk |
| S05 | Local KKT pressure vector | matching marginal-profit units | risk, budget, shared and bound terms | residual tolerance plus replication interval | Not additive acreage causality |
| S06 | Counterfactual block attribution | land share and risk units | M0--M4 additions across declared orders | order/selection interval | Model-dependent attribution |
| S07 | Dependence misspecification regret | profit and true-law CVaR units | assumed-law policy versus true-law optimum | paired interval with common evaluation draws | Conditional on chosen laws |
| S08 | Information value and interaction | profit units | signal precision by action-set contrast | simultaneous interaction interval | Not empirical forecast value |

## Nested model ladder

Every replication must solve the same scenario draw through a nested ladder.

- **M0 — ordinal recommendation:** declared score mapping with feasibility repair
  reported separately from the original recommendation.
- **M1 — cardinal margins:** expected-profit optimization with land and only the
  minimal domain bounds needed for well-posedness.
- **M2 — operational feasibility:** M1 plus budget, rotation, contract and crop
  bounds in controlled combinations.
- **M3 — downside risk:** M2 plus the loss-CVaR constraint.
- **M4 — dependence specification:** M3 evaluated under the named true and
  assumed dependence models, with cross-family results treated as sensitivity.

The ladder supports transparent block contrasts. Because block order can affect
attribution, the primary order above must be justified by the scientific
question and a secondary all-permutation or prespecified-order sensitivity must
be reported. If model stages have multiple optima, both the deterministic
selection and the range over objective-equivalent faces are required.

## Experiment families

### E1 — Ordinal versus cardinal margin information

Hold the score order, scenarios and feasible set fixed. Vary the cardinal gap
and monotone score transformation without changing rank. Compare M0 and M1.
Include equal-margin, near-tie, strict-gap and dominance anchors. The experiment
passes only if it recovers ordinal non-identification and the GOAL-14 positive
rank-preservation cases.

### E2 — Operational constraint mechanisms

Use one-at-a-time budget, rotation, contract, lower-bound and upper-bound
tightness sweeps, followed by a small prespecified factorial interaction design.
For each transition record allocation, face range, active set, slack, dual,
local KKT pressure and direct feasibility-forced status. Do not infer a
constraint's contribution from binding frequency alone.

### E3 — CVaR mechanism

With margins, dependence and operational constraints fixed, compare M2 and M3
over prespecified confidence and risk-limit grids. Include slack, just-binding,
strongly binding and infeasible anchors established analytically or by a
pre-result feasibility search that cannot use reversal outcomes. Retain
nonmonotone and zero allocation effects.

### E4 — Dependence and crossing sets

Within each named family, hold marginals, all constraints, alpha and risk limit
fixed while varying the family parameter on a sufficiently dense grid. Use
common random numbers only for paired comparisons within that family. Track
active-basis changes, selected allocation and possible/universal face ranges.
Cross-family comparisons must match rank correlation and marginals and are
labelled model sensitivity, never a scalar tail-dependence ordering.

### E5 — Diversification and misspecification

Construct risk--return frontiers under the true law and under each assumed law.
Report ordinary variance, loss-CVaR, tail co-exceedance, marginal tail-loss
contribution, support/concentration and true-law regret. Include cases where
variance and tail diversification agree, disagree and are both absent. The
pseudo-diversification flag remains descriptive.

### E6 — Information and flexibility

Cross signal precision with nested feasible action sets. Decision timing must
be signal, posterior, then action. For every cell report the uninformed policy,
state-contingent policy, actionability, information value, flexibility value and
difference-in-differences interaction. Include uninformative signals, common
optimal policies, added dominated actions and substitution counterexamples. A
strict complementarity claim is eligible only if GOAL-14 supplies sufficient
conditions and the simulated instance satisfies them.

### E7 — Global robustness layer

After E1--E6 are frozen, a global sensitivity design may vary empirically
estimated nuisance inputs and illustrative operational parameters. It cannot
replace controlled mechanism experiments. Its role is boundary discovery,
external stress and failure-case retention.

## Calibration and parameter governance

Every input receives one of four labels:

- `DATA_ESTIMATED`: point estimate plus bootstrap/posterior uncertainty from an
  admitted authoritative panel.
- `DATA_BOUNDED`: supported interval but no defensible point estimate.
- `DESIGN_CONTROL`: normalized mechanism setting chosen for identification.
- `ILLUSTRATIVE_STRESS`: no empirical interpretation and ineligible as sole
  support for a substantive claim.

Costs, margins and dependence may be calibrated from the longer official panel
created for GOAL-15 if its timing permits; the confirmatory design must otherwise
use the existing national panel and say so. Farm budgets, contracts, risk limits
and rotation rules remain design controls or illustrative stresses until an
authoritative source is admitted.

## Replication and precision protocol

GOAL-12 must calculate sample size before results. The protocol must:

1. Define the smallest scientifically meaningful allocation, CVaR, regret and
   interaction effects.
2. Use blinded/pilot variance inputs or conservative bounds, never Stage II
   outcome-selected variances.
3. Set family-wise primary coverage and a maximum binary interval width.
4. Use independent replication batches and a confidence-controlled stopping
   rule with a prespecified minimum, maximum and check schedule.
5. Require stability of both continuous estimands and reversal classification.
6. Treat reaching the maximum without precision as an adverse result, not an
   invitation to change tolerances or outcomes.

The Stage I ten-replication convergence design is explicitly insufficient. No
fixed replacement count is authorized by this blueprint; it must follow the
prospective precision calculation.

## Computation, replay and failure handling

- Fixed root seeds generate independently named replication streams.
- Scenario hashes and task-order-independent replay are mandatory.
- Sparse matrices and bounded worker counts preserve the existing resource gate.
- At least two solver methods are compared on all boundary anchors and a
  prespecified sample of interior cells.
- Direct atom-safe CVaR, tail weights, primal/dual/stationarity/complementarity
  residuals and optimal-face ranges are mandatory.
- The existing mean-variance failed benchmark row must be diagnosed before that
  benchmark enters the confirmatory design; failure may be retained as a result
  but cannot be silently counted as an optimum.
- Missing, infeasible and failed policy rows remain in tidy outputs with reason
  codes and are excluded only by prespecified rules.

## Output contract

The new package must contain:

- frozen YAML designs and their checksums;
- a cell/estimand registry;
- raw replication-level tidy outputs;
- nested-model and KKT-pressure outputs;
- crossing/face outputs;
- precision and stopping logs;
- replay and solver-sensitivity outputs;
- source-data extracts for every eligible figure panel;
- a claim assessment table with `SUPPORTED`, `REFUTED`, `PARAMETER_DEPENDENT`,
  `NOT_IDENTIFIED` and `PRECISION_FAILED` states;
- an immutable checksum ledger and observed resource audit.

## Promotion gates

A result is eligible for a main figure or manuscript claim only if:

1. its theory result or preregistered hypothesis exists;
2. the controlled contrast changes only declared factors;
3. numerical, replay, solver and optimal-face checks pass;
4. prospective precision and stopping rules pass;
5. the result is not supported solely by an illustrative stress;
6. null, adverse and contradictory cases are retained;
7. source data, code, configuration and execution records are complete; and
8. language stays within named-family, model and calibration boundaries.

Failure of any gate yields supplementary, diagnostic or inadmissible status; it
does not authorize a post hoc redesign under the same design identifier.
