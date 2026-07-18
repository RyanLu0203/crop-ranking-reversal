# Formal simulation results audit

## Scope and boundary

The governed Issue 6 run executed design `CRR-SIM-FREEZE-2026-07-19` without changing any cell, factor range, seed, scenario count, or falsification rule. The separate run protocol was frozen before formal results to operationalize the previously unspecified risk-frontier endpoints. All results are simulated sensitivity evidence calibrated to the official national panel; they are not empirical evidence.

## Completion and numerical integrity

- 90 cells × five frozen seeds = 450 primary allocations and 4,500,000 generated scenario rows.
- All 450 primary solves and all 450 pairwise optimal-face audits solved successfully.
- A reverse-cell/reverse-seed replay reproduced every scenario hash, reversal class, and audited numeric field: 450/450 passed.
- HiGHS default, dual simplex, and interior point agreed on three representative cells: 9/9 comparisons passed.
- Maximum primal KKT residual was `6.08e-11`; maximum stationarity residual was `4.15e-12`.
- Maximum direct atom-safe loss-CVaR excess was `3.87e-12`, below the frozen `1e-7` tolerance.
- Representative isolated audited solves peaked at 0.2405 GB, below the frozen 0.5 GB cap. The complete run plus replay and ancillary audits took about 281 seconds with four workers.

The first attempted run was stopped before output because dense constraint matrices exceeded the resource cap. Sparse matrices reduced peak memory. A subsequent audit found that NumPy's `higher` quantile was not the RU hinge minimizer when `alpha * S` was non-integer; the direct CVaR evaluator was corrected to use an empirical inverse-CDF RU auxiliary while retaining the conservative displayed VaR. All 105 tests and all formal outputs were then regenerated from scratch.

## Retained outcomes

- 30 of 90 cells produced universal Corn-to-Soybean reversal in all five replications; 60 produced no reversal in all five. Thus 150 of 450 replications reversed. Selected, possible, and universal classifications agreed in every replication, and maximum audited optimal-face width was `5.52e-6`.
- The loss-CVaR constraint bound in 245 replications and was slack in 205. This directly rejects any blanket assertion that CVaR must bind.
- The budget, rotation, and contract constraints bound in 74, 131, and 380 replications respectively; the land constraint bound in all 450.
- The descriptive pseudo-diversification flag occurred in 84 replications. It is not treated as welfare evidence or a sufficient exclusion condition.
- Within each named copula family, mixed-factor ordering by Kendall tau produced multiple disjoint crossing intervals (8 Gaussian, 14 Student-t, 11 Clayton). Because other LHS factors vary, these are conditional sensitivity patterns, not causal thresholds or cross-family dependence orders.
- In the illustrative exact finite-state mechanism audit, value of information was 0 at an uninformative signal, 7.657 at 75% accuracy, and 19.732 under a perfect signal. Nested action-set values were weakly nondecreasing. These are mechanism checks, not empirical estimates.

## Benchmark interpretation

Expected-profit and mean-variance allocations had the same aggregate result at the frozen illustrative penalty and violated the cell-specific CVaR limit in 245 replications. The repaired ranking-proportional policy violated it in 205. The CVaR policy violated it in zero. These policy comparisons demonstrate constraint effects within the design; they do not identify real farmer preferences or constraints.

## Theory assessment

The generated `theory_prediction_assessment.csv` records five supported numerical/mechanism statements, two parameter-dependent statements, and three not-identified statements. CT4, CT6, and CT7 are not promoted because the LHS does not isolate their required controlled comparisons. No theory result is marked refuted, and no unsupported unique-threshold or cross-family scalar-ordering claim is admitted.

## Headline decision

The formal results are **not headline-admissible** because the frozen convergence gate failed. They remain complete, reproducible, and usable as a quarantined sensitivity audit. See `audits/convergence_failure_memo.md`.
