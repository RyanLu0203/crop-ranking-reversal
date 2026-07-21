# Diversification, pseudo-diversification and true-law regret

## Comparator discipline

“Diversification” is not a property of an allocation in isolation. Every claim
must specify:

- the allocation and comparator;
- the probability law used for evaluation;
- whether margins and constraints are held fixed;
- the metric and direction;
- whether the policy is feasible under that law.

## Four non-equivalent outcome families

1. **Allocation concentration:** acreage shares and HHI or effective crop count.
2. **Variance diversification:** variance of portfolio profit under the named law.
3. **Tail diversification:** loss VaR/CVaR and marginal tail contributions under
   the named law.
4. **Decision quality:** true-law feasibility violation and, conditional on
   feasibility, true-law expected-profit regret.

The same crop count can hide very different weights. Lower HHI can coexist with
higher CVaR. Lower variance can coexist with catastrophic lower-tail exposure.
A policy can be attractive under an assumed law yet infeasible under the true
law. These are theorem-backed boundaries, not rare numerical exceptions.

## Pseudo-diversification definition

A comparison is labeled `PSEUDO_DIVERSIFICATION_CANDIDATE` only when all of the
following are reported:

1. the assumed-law policy has lower concentration, lower assumed variance, or
   lower assumed tail risk than its preregistered comparator;
2. the true-law evaluation has a preregistered adverse outcome—no tail-risk
   improvement, positive CVaR violation, or positive feasible regret;
3. margins, feasible actions, risk convention and paired evaluation draws are
   held fixed;
4. estimator uncertainty and dependence-family uncertainty are reported.

The older low-Pearson/high-lower-tail-dependence flag remains a descriptive
screening variable. It is neither necessary nor sufficient for this decision
outcome and cannot by itself support exclusion or welfare language.

## True-law evaluation order

For a policy \(x^Q\) selected under assumed law \(Q\):

1. evaluate \(r_{\alpha,P}(x^Q)\) on independent or paired registered draws
   from the declared true law \(P\);
2. report \([r_{\alpha,P}(x^Q)-\kappa]_+\);
3. only if feasible, report
   \(V_P^*-\mu_P^\top x^Q\geq0\);
4. report variance, concentration and crop inclusion separately;
5. compare with the true-law optimum and each frozen benchmark.

No arbitrary penalty combines risk infeasibility and objective regret.

## GOAL-12 falsification patterns

- HHI falls but true-law CVaR also falls: allocation and tail diversification
  agree; no pseudo-diversification finding.
- HHI falls but true-law CVaR rises: concentration is not tail diversification.
- assumed-law CVaR falls but true-law violation is positive: dependence
  misspecification has operational consequences in that cell.
- assumed-law policy is true-law feasible with zero regret: misspecification is
  decision-irrelevant for the frozen design.
- results reverse across plausible named families: model sensitivity, not a
  universal mechanism.
