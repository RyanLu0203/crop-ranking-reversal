# Numerical experiment design freeze

## Freeze declaration

Design `CRR-SIM-FREEZE-2026-07-19` is frozen on the Issue #5 branch before any formal experiment. This commit contains design code, unit/oracle tests, and three 64-scenario smoke cells only. Issue #6 is the first issue authorized to produce formal cell outputs. A later scientific change requires a new design version, rationale, checksum, and supersession note; it may not overwrite this freeze.

## Empirical calibration boundary

Margins, sample standard deviations, Pearson/Kendall dependence summaries, and 2024 real operating costs come only from `data/processed/canonical_crop_year_panel.csv`. Candidate marginals are Gaussian, Student-t(5), and empirical inverse-CDF resampling. Candidate copulas are Gaussian, Student-t(4), and Clayton. Rolling-origin log score followed by parsimony is the frozen selection rule, but every family remains in sensitivity analysis. ERS survey-base indicators and leave-period-out checks address measurement regimes. The 27-year sample requires bootstrap and Monte Carlo intervals.

No Draft Iowa, 500-acre, budget, cost, tail-mixture, seed, risk-limit, or reversal-number value remains in the canonical configuration. Land is normalized to one. Budget ratios, rotation caps, contract minima, alpha, risk-frontier quantiles, scenario counts, and seeds are design choices, not observed farmer parameters.

## Cell construction

The design has 90 cells: 24 stratified Latin-hypercube cells within each of three copula families (72) plus 18 preregistered anchors. Continuous ranges are Kendall tau 0--0.60, alpha 0.90--0.99, risk-frontier quantile 0.10--0.90, budget/max-cost ratio 0.70--1.10, dominant-crop cap 0.35--1.00, and contract minimum 0--0.15. Marginal families are balanced within the LHS. Anchors cover three dependence levels, three alpha levels, four operational regimes, and three risk regimes without selecting cases from outcomes.

Each formal cell has five fixed seeds and 10,000 scenarios. The separate five-point convergence grid and ten replications follow `simulation/contracts/randomness_protocol.md`.

## Metrics fixed before results

- Expected profit and loss-CVaR.
- Selected, possible, and universal reversal from the objective-equivalent optimal face.
- All crossing intervals and disjoint reversal regions; a unique threshold is not presumed.
- Active land, budget, risk, bound, rotation, and contract constraints with duals.
- KKT primal, dual, stationarity, complementarity, and tail-weight diagnostics.
- Expected-profit, repaired ranking-proportional, mean-variance, and CVaR benchmarks.
- Pseudo-diversification as a descriptive flag only.
- Exact finite-state value of information, policy actionability, and nested-flexibility value.

## Falsification and nonadaptation

The ten falsification rules in the YAML are hard gates. In particular: sign/KKT failures, an unaudited universal reversal, missed multiple crossings, a cross-family scalar tail order, negative VOI with an ignore-signal policy, declining value under nested flexibility, convergence failure, or sole reliance on an illustrative factor blocks the corresponding claim. No result-contingent range, seed, family, metric, or tolerance change is permitted. The imported post-result regime search is disabled in code.

## Resource budget

The formal plan is 450 primary solves plus 50 convergence solves and 4.5 million scenario rows. Peak memory is budgeted at 0.5 GB per solve, at most four parallel workers, and roughly 1--4 single-machine wall-clock hours. These are planning estimates to be recorded against observed Issue #6 resources; they are not permission to expand the grid automatically.
