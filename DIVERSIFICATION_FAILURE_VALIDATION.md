# Diversification failure validation — Issue #36

## Registered objects

- \(x^0\): matched-Gaussian expected-profit allocation.
- \(x^{MV}\): full-investment Gaussian mean--variance frontier point at
  \(\gamma=0.0085\).
- \(x^T\): expected-profit optimum under the matched-Kendall Student-\(t\)
  true-law CVaR ceiling.
- Matched rank dependence: Kendall's \(\tau=0.25\).
- Gaussian asymptotic lower-tail dependence: zero.
- Student-\(t\) lower-tail coefficient: 0.195380.

## Executable inequalities

1. Gaussian variance:
   \[
   5579.213188=\operatorname{Var}_G\Pi(x^{MV})
   <6765.623988=\operatorname{Var}_G\Pi(x^0).
   \]
   The reduction is 17.53%.
2. Allocation difference:
   \(\lVert x^{MV}-x^T\rVert_1=0.053709>0.01\).
3. True-law loss-CVaR:
   \[
   -44.367622=r_T(x^{MV})>-45.733313=r_T(x^T).
   \]
   Larger loss-CVaR is worse.
4. Strong form:
   \(r_T(x^{MV})=-44.367622>\kappa=-45.733313\).

All four conditions pass. The manuscript may therefore claim the strong form
for this registered example. The result is conditional; it does not say that
all mean--variance diversification fails.

The code compares \(x^{MV}\) directly with the declared \(x^0\). It contains
no maximum-over-candidates surrogate. The entire gamma grid is retained as
source data in `reconstruction/issue34/outputs/diversification_failure.csv`.
