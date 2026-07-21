# Stage II scientific gap audit

## Executive judgment

Stage I is a credible theory-repair and reproducibility foundation, not yet a
mechanism paper. It establishes that ordinal rankings do not identify cardinal
allocations, repairs the loss-CVaR programme, distinguishes properties of the
optimal set, reproduces a descriptive state-level discordance pattern, and
prevents unsupported causal interpretation. Those are necessary achievements.
They do not yet demonstrate which mechanism generates reversal, how much each
mechanism changes acreage and downside risk, when diversification fails, or when
information becomes actionable.

The Stage II paper should therefore move from the defensible Stage I statement

> ranking--acreage disagreement exists, but its optimizing mechanism is not
> identified

to the bounded positive statement

> rankings are incomplete decision objects; controlled theory and simulation
> identify when cardinal margins, operational feasibility, downside risk and
> dependence alter allocation, while expanded observational evidence tests the
> corresponding empirical patterns without treating acreage as revealed optimum.

This target preserves the supervisor Draft's scientific vision and rejects its
unsupported thresholds, percentages and welfare claims.

## Authoritative Stage I evidence inspected

The audit reads the complete modular manuscript; the repaired theorem set and
transition registry; all theory-to-simulation and theory-to-empirical maps; the
frozen simulation design, 450 formal optimization rows, convergence audit and
mechanism outputs; the frozen empirical design and all result/robustness tables;
the figure registry, source-data lineage and rendered figures; the claim,
number, figure and asset registries; and the final compiled review package.

Key facts that constrain reconstruction are:

- The main text contains two figures: a conceptual boundary diagram and a
  descriptive state-by-definition analysis. It contains no main quantitative
  mechanism figure.
- The formal simulation solved and replayed 450 primary problems, but zero of
  five convergence rows passed. Five seeds per cell yield wide binary intervals.
- The 90-cell Latin-hypercube design changes dependence, risk tolerance, budget,
  bounds and contracts together. Its own theory assessment marks CT4, CT6 and
  CT7 not identified and CT8--CT9 parameter dependent.
- The empirical analysis contains 77 complete state-years in 26 states over
  2022--2024. National prices and costs create accounting scores, not local
  realized margins. Five central mechanism domains remain not identified.
- Of 31 audited Draft results, six are false in general, five require
  reformulation, five require additional assumptions and three are numerical
  conjectures only. The canonical transition registry repairs or replaces them,
  but the draft-oriented proof-gap registry still labels 18 gaps open; Stage II
  must distinguish historical gaps from new research obligations.

## Current weakness analysis

| Dimension | Stage I strength | Evidence that remains missing | Scientific consequence | Stage II owner |
|---|---|---|---|---|
| Core contribution | Exact boundary between ordinal rank and cardinal allocation | Positive characterization of when a ranking does predict allocation | The paper can be read as a cautionary note rather than a new decision principle | GOAL-14 |
| Margin mechanism | Expected profit is defined and benchmark policies exist | Controlled variation in cardinal margin gaps holding feasibility and risk fixed | No estimate of how cardinalization alone changes allocation | GOAL-14 + GOAL-12 |
| Operational mechanism | Full feasible set and KKT multipliers are correct | One-at-a-time and interaction counterfactuals for budget, rotation, contract and bounds | Binding frequencies cannot attribute acreage reversal to a constraint | GOAL-12 |
| Risk mechanism | Loss-CVaR sign, subgradient and LP implementation are validated | Controlled M2-to-M3 comparison across risk limits and confidence levels | A binding/slack count does not measure the allocation or tail-loss effect of CVaR | GOAL-12 |
| Dependence mechanism | Cross-family scalar-ordering overclaim is blocked | Fixed-marginal, fixed-constraint within-family sweeps and misspecification counterfactuals | Mixed-factor crossing sets are not causal regime maps | GOAL-14 + GOAL-12 |
| Optimal-set multiplicity | Possible, universal and selected reversal are distinguished | Mechanism attribution robust to an optimal face and selection rule | A selected vertex may conceal set-valued mechanism uncertainty | GOAL-14 + GOAL-12 |
| Diversification | Pseudo-diversification is a bounded diagnostic | Separate variance, tail, concentration and true-law regret outcomes | The supervisor Draft's diversification claim has no positive replacement | GOAL-14 + GOAL-12 |
| Information and flexibility | Nonnegative information value and weak action-set monotonicity are proved | Conditional complementarity theorem and signal-precision by flexibility experiment | Seven illustrative finite-state rows do not establish interaction | GOAL-14 + GOAL-12 |
| Simulation precision | Every primary solve, replay and numerical diagnostic passes | Prospective interval/power calculation, sequential independent replications and controlled estimands | Formal patterns remain nonheadline | GOAL-12 |
| Empirical time support | Official, checksum-governed state data and four definitions | Longer pre-decision panel, rolling validation, transition outcomes and vintage checks | Three years cannot establish temporal robustness or downside exposure | GOAL-15 |
| Empirical mechanism link | Discordance, heterogeneity and national null are reproducible | Observable proxies/predictions explicitly paired with model mechanisms | Observed discordance remains a phenomenon without model-linked validation | GOAL-15 |
| Geographic/economic alignment | National input standardization is transparent | Geography-matched prices, costs, constraints or explicit partial-identification treatment | Accounting margins cannot be interpreted as local profit | GOAL-15 |
| Visualization | Editable, accessible, source-backed Stage I figures | Geometry, nested-model, regime, diversification and information-value evidence | The visual story emphasizes boundaries rather than discovery | GOAL-13 |
| Manuscript architecture | Claim discipline and a clean 4,134-word compilation | Evidence ladder from framework to mechanism to validation | Results are fragmented and the central positive contribution is absent | Final rebuild |

## Theory gap analysis

Stage I correctly removes false universal statements. Stage II must add positive
results without smuggling those statements back in. The required mathematical
move is to define an identification region over admissible cardinalizations,
feasible sets and optimizer selections, then state sufficient conditions that
collapse or order this region. It is not enough to restate ordinal insufficiency.

The KKT pairwise equation should be retained as a decomposition of local
optimality pressure, not relabelled as an additive causal decomposition of
acreage. Quantitative acreage attribution requires controlled counterfactual
models and a declared selection rule; when the optimum is set-valued, the output
must be an attribution interval over the optimal face. These safeguards are
encoded in `theory_gap_matrix.csv`.

The positive theoretical package should contain four layers:

1. **Identification:** necessary inputs and sufficient restricted conditions for
   rank-preserving allocation, plus an identified set when they are absent.
2. **Mechanism accounting:** full margin, CVaR, budget, shared-constraint and
   bound pressure terms, paired with selection-robust counterfactual attribution.
3. **Risk and diversification:** named-family dependence results, tail-risk
   concentration and decision regret under misspecification.
4. **Information:** general actionability results plus clearly stated sufficient
   conditions for information--flexibility complementarity; otherwise label the
   interaction a numerical hypothesis.

Every result must be tagged `PROVED`, `PROVED_CONDITIONAL`,
`NUMERICAL_HYPOTHESIS`, `COUNTEREXAMPLE_BOUNDARY` or `EMPIRICAL_HYPOTHESIS`.

## Simulation gap analysis

The Stage I simulation is valuable as a pilot and software audit. It cannot be
promoted by simply adding seeds to the same 90-cell design. Its factors are
jointly varied, its binary cell estimates use five replications, its convergence
rule was structurally unattainable with ten convergence replications in the
unanimous case, and one mean-variance benchmark row is recorded as failed even
though all primary CVaR solves passed.

GOAL-12 must create a new versioned confirmatory design. The design must separate
nested model stages M0--M4, use fixed-factor mechanism experiments before a global
sensitivity layer, calculate replication requirements prospectively, use common
random numbers only within a declared controlled comparison, and retain null and
adverse results. Details and stop rules are in `simulation_redesign_plan.md`.

## Empirical gap analysis

The current empirical result is real but narrow: top-rank discordance varies from
0.623 to 0.870 across four score definitions in a selected three-year sample, and
the national comparison is a complete null. This supports existence and
definition sensitivity, not mechanism.

GOAL-15 should prioritize temporal depth and decision timing over adding another
cross-sectional ranking. It needs a versioned official-data panel, pre-decision
score construction, observed acreage-share transitions, rolling and geographic
holdouts, aggregation checks, and model-linked hypotheses. Operational variables
must be labelled observed, proxy or unavailable. Farm-level CVaR, private
contracts and causal information value remain unidentified unless genuinely new
data or a credible design is admitted. Details are in
`empirical_expansion_plan.md`.

## Figure gap analysis

The current visual system passes technical QA, but the scientific hierarchy is
Stage I hierarchy: Figure 1 explains boundaries and Figure 2 documents the
phenomenon; all numerical patterns are supplementary and nonheadline. Stage II
needs six main figure groups that progress from system definition to geometry,
controlled mechanism evidence, regime maps, diversification and empirical
validation. A figure cannot be commissioned until its evidence gate passes.

The current Nature guidance checked on 2026-07-21 requires 89 mm or 183 mm figure
widths, maximum 170 mm height, 5--7 pt editable standard-font text, accessible
colour, labelled axes with units and editable vector layers. Nature describes
five to six modest display items as typical for an eight-page Article. The
blueprint therefore treats six main groups as a ceiling to be defended, not an
invitation to build a dashboard. Official guidance:

- https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/
- https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/
- https://www.nature.com/nature/for-authors/initial-submission

## Reconstruction thesis and claim ladder

The manuscript should be rebuilt only after later phases produce evidence for
this ladder:

1. Rankings do not identify allocations without cardinal, feasibility and
   selection information (proved).
2. Under declared sufficient conditions, ranking and allocation are aligned;
   relaxing each condition creates a measurable mechanism channel (theory plus
   controlled simulation).
3. Operational and risk channels have distinct shadow-pressure, acreage and
   tail-loss signatures (controlled simulation).
4. Dependence misspecification can make nominal diversification conceal true-tail
   concentration and regret (conditional theory plus controlled simulation).
5. Information creates operational value only when the signal changes a feasible
   action, with complementarity asserted only under proved conditions or as a
   bounded numerical result (theory plus controlled simulation).
6. Longer-horizon observational patterns are consistent or inconsistent with
   named model predictions, while optimality and causality remain separately
   labelled (empirical validation).

## Non-negotiable boundaries carried forward

- Historical thresholds, prevalence rates, welfare losses and out-of-sample
  claims remain inadmissible.
- Stage I outputs are immutable evidence; a Stage II design supersedes rather
  than overwrites them.
- Observed acreage is not automatically an optimizer solution.
- Cross-family copula comparisons are model sensitivity, not a scalar
  tail-dependence ordering.
- A KKT pressure term is not by itself a causal acreage contribution.
- A figure cannot precede validated source data.
- The manuscript cannot be reconstructed until GOAL-14, GOAL-12, GOAL-13 and
  GOAL-15 have each passed their own evidence gates.
