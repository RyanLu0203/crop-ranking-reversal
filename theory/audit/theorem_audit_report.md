# Teacher-model theorem audit

## Executive judgment

The teacher draft contains a coherent convex acreage-allocation core, and its finite-scenario CVaR inequalities are structurally usable after the loss convention is made explicit. The headline theory is not currently publishable as theorem-level mathematics. The KKT statement is incomplete; the ranking-reversal “if and only if” does not follow from stationarity; lower-tail dependence is treated as if one scalar ordered full joint distributions; threshold existence and uniqueness are assumed; and information-flexibility complementarity invokes monotone-comparative-statics logic without its hypotheses.

No numerical claim in the teacher draft was admitted. The baseline TeX and PDF remain immutable.

## Result-by-result conclusions

### CVaR and optimization

The continuous CVaR equation selects the upper profit tail and negates it. For a loss confidence level $\alpha$, the relevant profit outcomes are the lower $1-\alpha$ tail. The finite-scenario inequalities nevertheless encode $q_s\ge-\pi_s^Tx-v$, which is the correct loss epigraph. The minimal repair is therefore local but essential: declare $L=-\Pi$, adopt the RU loss definition, and treat the scenario LP as its operational form.

The marginal expression needs two repairs. Its cutoff is $F_\Pi^{-1}(1-\alpha)$, not $F_\Pi^{-1}(\alpha)$, and a unique derivative is unavailable when probability mass lies at VaR. Because the project's simulations are finite, subgradient/LP-dual language should be primary.

### KKT and ranking reversal

The displayed stationarity omits budget and rotation/shared-constraint multipliers. Even when repaired, KKT equates marginal objective benefit with shadow costs. It does not state that a crop with a larger risk-adjusted margin receives more acres: levels are determined by the entire feasible geometry, active bounds, and possibly an optimal face. The undefined `gap_ij` cannot conceal these terms and cannot convert stationarity into an acreage-ordering equivalence.

The headline theorem is therefore `FALSE_IN_GENERAL`. Its defensible replacement is two-part: a full KKT/subgradient optimality characterization, and a simple universal feasibility-forced reversal proposition such as $u_i<\ell_j$. Any economic reversal beyond this must be measured from the complete optimal set or a declared tie-breaker.

The profit-based corollary also fails as written. Suitability scores and expected profit have different units; the usable assumption is only that they induce the same ranking.

### Dependence and thresholds

The lower-tail coefficient is one limiting diagonal feature of a copula. It neither identifies a joint law nor globally orders marginal CVaR contributions. The proposition claiming monotonicity from means, variances, and $\lambda_L$ is false. A clean witness is the Gaussian family: all nonsingular correlations have zero asymptotic tail-dependence coefficient, while the loss distribution of a sum and hence its CVaR varies with correlation.

Threshold existence needs an endpoint crossing; uniqueness needs strict monotonicity; allocation statements additionally need a unique optimizer or selection rule. None is supplied. LP active-set changes make discontinuous or set-valued acreage responses natural. The unique-threshold theorem is false in general. A future restricted proposition may assert a crossing only for one fixed family, fixed marginals, a documented selection rule, and verified regularity. Until then, threshold signs are numerical conjectures.

### Pseudo-diversification

Low Pearson correlation does not force a crop into a mean-variance optimum, because mean returns and constraints matter. High tail dependence does not force exclusion from a CVaR optimum, particularly when the crop has strong margins or the risk limit is slack. Moreover, a lower expected-profit objective value does not imply a higher CVaR value. The current definition may survive only as a descriptive diagnostic with explicit thresholds; the proposition is false in general.

### Information and flexibility

The teacher value expression mixes a posterior expectation with a random payoff and leaves decision timing unclear. The canonical repair gives the informed and uninformed problems the same outer expectation and lets the signal precede the recourse allocation.

Zero value under a singleton feasible set is valid, and the stronger actionable version is also valid: if a common allocation is optimal for every signal realization, operational information value is zero. Nested feasible sets support weak nondecrease in the value of flexibility, not strict increase. Supermodular information-flexibility complementarity requires explicit lattice, increasing-differences, and monotone-selection hypotheses; without them the claim is false in general.

## Safe conclusions retained

- Ordinal suitability cannot identify cardinal acreage.
- Explicit feasible bounds can force universal reversal.
- A unique unconstrained optimizer that strictly satisfies the CVaR limit remains optimal after adding it; solution-set equality under multiplicity needs all unconstrained optima feasible.
- Full subgradient KKT conditions characterize the convex problem under duality regularity.
- Dependence effects can be claimed only inside a specified, verified family/order.
- Information has zero operational value when signal-contingent optimal policies coincide.

## Evidence boundary

Only three methodological sources enter the literature registry as theory foundations: the two full author-text Rockafellar–Uryasev papers and the open full-text Ansari–Rockel dependence-ordering article. The teacher bibliography is not automatically admitted. Topkis and Nelsen records were located but not used as verified proof foundations because full authoritative text was not inspected in this audit.

The definitive per-result classifications are in `theorem_inventory.csv`; proof gaps and executable witnesses are linked there.
