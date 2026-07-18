# Canonical teacher-model specification

## Scope and status

This file reconstructs the model in the immutable teacher draft. It is an audit specification, not a manuscript replacement and not an empirical result. All monetary quantities must use one declared real-dollar base year before estimation.

## Primitives

On a probability space $(\Omega,\mathcal F,P)$, for crops $i=1,\ldots,n$, let $x_i$ be planted acres; $p_i(\omega)$ price per output unit; $y_i(\omega)$ output per acre; $c_i$ deterministic cost per acre; and $\pi_i(\omega)=p_i(\omega)y_i(\omega)-c_i$ profit per acre. Portfolio profit and loss are

\[
\Pi(x,\omega)=\sum_i x_i\pi_i(\omega),\qquad L(x,\omega)=-\Pi(x,\omega).
\]

Price and yield may be jointly stochastic within and across crops; their joint law belongs to the scenario/dependence model. Profit may be negative. The baseline assumes homogeneous acres, constant per-acre returns, deterministic variable costs, no fixed setup costs, no acreage interaction terms, and no endogenous market-price feedback. Relaxing these assumptions requires a separately approved nonlinear or mixed-integer extension. Idle land has zero modeled profit and zero modeled variable cost.

Let $\mu_i=E[\pi_i]$, $A$ be available acres, $B$ the cost budget, $\ell,u$ crop bounds, and $Hx\le h$ collect rotation or other shared linear restrictions. The canonical feasible set is

\[
X=\{x\in\mathbb R^n:\ell\le x\le u,\;\mathbf 1^Tx\le A,\;c^Tx\le B,\;Hx\le h\}.
\]

The audited optimization problem is

\[
\max_{x\in X}\ \mu^Tx\quad\text{s.t.}\quad \operatorname{CVaR}_\alpha(L(x,\omega))\le\kappa.
\]

The land restriction is an inequality. Full land use is a conclusion only under additional dominance/feasibility conditions; it is not a primitive.

## Finite-scenario LP

For scenarios $s=1,\ldots,S$, probabilities $w_s>0$ with $\sum_s w_s=1$, and profits $\pi_{is}$, introduce a free scalar $v$ and $q_s\ge0$:

\[
\begin{aligned}
\max_{x,v,q}\quad &\mu^Tx\\
\text{s.t.}\quad &v+\frac{1}{1-\alpha}\sum_s w_sq_s\le\kappa,\\
&-\sum_i\pi_{is}x_i-v\le q_s\quad(s=1,\ldots,S),\\
&q_s\ge0,\quad x\in X.
\end{aligned}
\]

Equal-weight simulation uses $w_s=1/S$. The objective must not perturb $v,q$; they are feasibility auxiliaries. If a solver requires a tie-breaker, it must be documented and checked not to alter the primary optimum.

## Existence, convexity, and optimality

- If $X$ is nonempty and compact (for example, $0\le x$ and $A<\infty$), and profits are integrable, an optimum exists.
- CVaR of affine loss is convex in $x$, hence the feasible region is convex. With finite scenarios, the problem is a linear program.
- Let $d\in\partial\operatorname{CVaR}_\alpha(L(x^*))$. Under a constraint qualification (or finite-LP strong duality), KKT stationarity is

\[
0\in-\mu+\lambda d+\gamma\mathbf1+H^T\eta+\beta c+u^+-u^-,
\]

with nonnegative multipliers and complementary slackness for the CVaR, land, shared, budget, upper-bound, and lower-bound constraints. For two crops, land's common multiplier cancels, but budget, rotation, and bound terms generally do not. This stationarity relation does not by itself order acreage levels.

## Ranking concepts

A suitability score $s_i$ induces a weak order; it has no cardinal acreage content. For a selected optimizer $x^*$, pairwise reversal is $s_i>s_j$ and $x_i^*<x_j^*$. Because the LP can have multiple optima, every reported reversal must be tagged:

The teacher's proportional heuristic is $r_i=A s_i/\sum_j s_j$. It is defined only for nonnegative, non-all-zero, cardinal ratio-scale scores and need not satisfy crop bounds, budget, or rotation constraints. The winner-take-all heuristic assigns land to a highest-score crop; ties require a declared split/selection rule, and the result can also be operationally infeasible. The canonical comparison therefore treats these as benchmark mappings $R(s)$, or more generally a declared class of score-monotone recommendation maps, never as feasible optima by definition.

- `POSSIBLE`: at least one optimizer reverses;
- `UNIVERSAL`: every optimizer reverses;
- `SELECTED`: only the documented deterministic tie-break solution reverses.

Tolerance $\tau_x$ defines strict numerical comparisons: $x_j-x_i>\tau_x$. Strong reversal additionally requires $x_i\le\tau_x$ and $x_j>\tau_x$.
Top-rank reversal occurs when a crop in the highest suitability tie class receives less acreage than a lower-ranked crop; it inherits the same possible/universal/selected qualifier.

## Decision timing for information

Let signal $Z$ be observed before the recourse allocation $x(Z)$ is chosen. A coherent operational value is

\[
V(\phi)=E_Z\left[\max_{x\in X(\phi)}E[\Pi(x,\omega)\mid Z]\right]-\max_{x\in X(\phi)}E[\Pi(x,\omega)].
\]

Both terms use the same information timing and unconditional outer expectation. If an optimal policy can be chosen constant across all signal realizations, operational value is zero. Strict complementarity with flexibility is not implied without stronger lattice/increasing-differences assumptions.

## Explicit exclusions

The teacher draft's numerical parameters, allocations, thresholds, percentage improvements, and out-of-sample statements are illustrative only. This specification does not admit them as findings.
