# Diversification-frontier validation

## Policy construction

- \(x^0\) is the solver-generated expected-profit allocation under the matched
  Gaussian law and full-investment operational set.
- Each \(x^{MV}(\gamma)\) is solved on a 301-point Gaussian mean--variance
  frontier, \(\gamma=0,0.0001,\ldots,0.0300\).
- \(x^T\) is the solver-generated expected-profit optimum under the common
  Student-\(t\) evaluation-law loss-CVaR ceiling.
- All policies use the same land normalization and operational constraints.
  Every frontier status is optimal; maximum feasibility and full-investment
  residuals are below \(10^{-7}\).

## Selection rule and focal result

The focal mean--variance policy is the smallest \(\gamma\) achieving at least
15% Gaussian variance reduction relative to \(x^0\). This rule does not use
the Student-\(t\) outcome. It selects \(\gamma=0.0082\), not the previous
single point 0.0085, and is interior to the frontier.

1. Gaussian variance:
   \[
   5733.463687=\operatorname{Var}_G\Pi(x^{MV})
   <6765.623988=\operatorname{Var}_G\Pi(x^0),
   \]
   a 15.25595% reduction.
2. Allocation difference:
   \[
   \lVert x^{MV}-x^T\rVert_1=0.089674>\varepsilon_x=0.01.
   \]
3. Student-\(t\) evaluation-law tail inferiority:
   \[
   -43.369109=r_T(x^{MV})
   >-45.733313=r_T(x^T)+\varepsilon_r.
   \]
4. Operationally strong failure:
   \[
   -43.369109=r_T(x^{MV})
   >\kappa+\varepsilon_r,\qquad \kappa=-45.733313.
   \]

Because \(x^T\) binds the common ceiling to numerical precision, Conditions 3
and 4 coincide numerically. They are one tail-risk gap, not independent
confirmations.

Both weak and strong criteria hold for
\(\gamma\in[0.0068,0.0088]\) on the evaluated grid. The focal point passes the
strong criterion.

## One-factor sensitivity

The analysis varies scenario count, seed, Kendall's \(\tau\), Student-\(t\)
copula degrees of freedom, CVaR confidence level, risk-ceiling location,
evaluation-law marginal specification and the 10/15/20% selection target.
Seventeen of 18 cases pass both weak and strong selected-policy criteria. The
20% variance-target case selects \(\gamma=0.0089\), immediately beyond the
reported strong-failure interval; its tail gap is positive but below the
declared \(\varepsilon_r\). This retained null prevents a universal robustness
claim.

Complete policy, frontier and sensitivity rows are in:

- `reconstruction/issue34/outputs/diversification_failure.csv`
- `reconstruction/issue34/outputs/diversification_sensitivity.csv`
