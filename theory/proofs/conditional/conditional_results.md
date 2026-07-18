# Conditional results

## C1. CVaR marginal identity

If profits are integrable, portfolio profit has no atom at its lower $1-\alpha$ quantile, and differentiation under the tail expectation is valid, then a CVaR subgradient component is

\[
d_i=-E[\pi_i\mid\Pi\le F_\Pi^{-1}(1-\alpha)].
\]

Without those conditions, replace $d_i$ by the convex subdifferential or finite-LP dual tail weights.

## C2. Full KKT characterization

If the canonical convex problem is feasible and a constraint qualification holds (or finite-LP strong duality applies), $x^*$ is optimal exactly when primal feasibility, dual feasibility, complementary slackness, and

\[
0\in-\mu+\lambda\partial\mathrm{CVaR}_\alpha(L(x^*))+\gamma\mathbf1+H^T\eta+\beta c+u^+-u^-
\]

hold. This is a global optimality statement, not an acreage-ranking equivalence.

## C3. Risk-slack invariance

Let $U=\arg\max_{x\in X}\mu^Tx$ and let $R$ be the CVaR-feasible subset. If $U\cap R\ne\varnothing$, the constrained optimum value equals the unconstrained value and its optimizer set is $U\cap R$. Therefore one unique unconstrained optimizer that is risk-feasible remains unchanged. Full solution-set invariance requires $U\subseteq R$.

## C4. Unique crossing lemma

For a scalar, continuous comparison function $g(t)$, if $g(0)g(1)<0$ and $g$ is strictly monotone, there is exactly one zero. Applying this to acreage requires a single-valued continuous optimizer or a declared continuous selection. These conditions are not supplied by a generic parametric LP.

## C5. Family-specific dependence comparative statics

A monotonic dependence conclusion is permissible only after fixing marginals and a copula family and proving that its parameter orders the relevant loss functionals. Monotonicity of a family parameter, Kendall's tau, or $\lambda_L$ alone is not sufficient. Ansari and Rockel (2024) is used only to document the need for explicit copula order and family conditions.

## C6. Information-flexibility complementarity

Nested feasible sets prove weak value monotonicity. Increasing differences between information quality and flexibility additionally require an ordered/lattice action domain, appropriate supermodularity/increasing differences of the state-contingent objective, and a monotone optimizer selection. No strict derivative conclusion follows at kinks or flat regions.
