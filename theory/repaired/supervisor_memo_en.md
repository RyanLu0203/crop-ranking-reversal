# Supervisor memo: repaired theorem package

## Recommendation

Approve the repaired package as the paper's canonical theory contract, subject to the five explicit confirmations below. It preserves the teacher Draft's substantive question and multi-crop stochastic program, but it does not preserve claims that the audit proved false.

## What remains unchanged

The decision is a multi-crop acreage vector. Per-hectare profits are stochastic price times stochastic yield minus cost; total profit is linear in acreage. Land, budget, crop bounds, rotations and other shared constraints remain in one operational feasible set. Dependence is represented by registered marginal profit laws plus a valid copula. The planner maximizes expected profit subject to a loss-CVaR limit. Suitability benchmarks, ranking reversal, dependence stress, pseudo-diversification, and information/flexibility remain the paper's organizing topics.

The immutable teacher TeX and PDF remain the provenance baseline. This package changes no baseline file.

## Necessary corrections

1. CVaR is defined on portfolio loss. The Draft's negative upper-profit-tail integral selected the best profit tail and was false.
2. The finite-scenario formulation declares the VaR auxiliary free and uses normalized scenario weights.
3. CVaR marginal terms use atom-safe subgradients or LP dual tail weights, with the profit cutoff at the lower \(1-\alpha\) tail.
4. KKT stationarity contains the land, budget, all shared-constraint, lower-bound, upper-bound, and risk multipliers.
5. An acreage reversal is solution-set aware: possible, universal, or selected. Pairwise, top-rank, and strong reversals are distinct.
6. A marginal KKT inequality is not an if-and-only-if theorem for acreage levels. It is replaced by full optimality conditions, a feasibility-forced result, and a genuinely feasible displacement certificate.
7. Tail dependence claims are conditional on a named family and a verified stochastic order; a scalar lower-tail coefficient cannot order general copulas.
8. Unique thresholds and strict information-flexibility complementarity are not general results. The defensible objects are crossing sets, information actionability, and weak value monotonicity under nested action sets.

## Decisions requested

1. **Confirm solution-set-aware reversal as the primary definition.** Recommended: yes. A solver-selected point alone cannot support a universal claim when the LP has multiple optima.
2. **Confirm crossing sets rather than a unique threshold.** Recommended: yes. Uniqueness may be reported only after a preregistered numerical audit establishes it in a restricted model.
3. **Confirm conditional dependence language.** Recommended: yes. The paper may state a convex-order result for a named family/domain and treat broader monotonicity as a simulation hypothesis.
4. **Confirm “pseudo-diversifier” as a diagnostic label.** Recommended: yes. Low Pearson correlation plus high lower-tail dependence does not imply exclusion, higher portfolio CVaR, or welfare loss.
5. **Confirm actionability and weak flexibility monotonicity as the main information results.** Recommended: yes. Strict complementarity may appear only as a restricted extension after its lattice and increasing-differences assumptions are separately proved.

## Downstream consequences

The simulation freeze must operationalize every theorem through theory_to_simulation_map.csv, including explicit falsification criteria and active-set/optimal-face checks. The empirical workflow must follow theory_to_empirical_map.csv: observed reversal is descriptive unless the risk limit, feasible set, joint law, and optimizer selection are identified. The manuscript must not restore rejected statements through narrative wording.

Every audited Draft result R01–R31 has exactly one disposition in theorem_transition_registry.csv; no claim was silently deleted.
