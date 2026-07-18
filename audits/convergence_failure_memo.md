# Frozen convergence-gate failure memo

## Decision

FAIL for headline use; retain all results and do not tune, reseed, or enlarge the formal run post hoc.

## Observed convergence

The preregistered representative cell was solved at 1,000, 2,500, 5,000, 10,000, and 25,000 scenarios for ten independent convergence seeds. Relative to each seed's 25,000-scenario reference, the fractions satisfying the allocation, CVaR, and objective tolerances were 0.0, 0.2, 0.1, 0.0, and 1.0. The frozen rule requires at least 0.8 and therefore fails at every non-reference count, including the formal 10,000 count.

The reversal state was unanimously false at every count. Nevertheless, the two-sided 95% Wilson interval for zero successes in ten trials is `[0, 0.2775]`, width 0.2775, above the frozen maximum width 0.10. Consequently, the interval-width rule is structurally unattainable with ten replications even under unanimous outcomes.

## Governance consequence

- `headline_admissible=false` is propagated to the formal summary and every Issue 6 acceptance document.
- The 90-cell results may describe the tested design only and must carry the convergence qualification.
- No single threshold, general dependence ordering, or stable reversal probability is claimed.
- A future confirmatory design would need a separately versioned replication count and power/precision calculation. That redesign is outside Issue 6 and cannot retroactively validate this run.
