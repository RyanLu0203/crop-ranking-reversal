# Proofs for the Issue #34 canonical theory

## Theorem 1

Write \(z=x_1\) and \(x_2=A-z\).  The expected-profit objective equals
\(\mu_2A+(\mu_1-\mu_2)z\).  Loss-CVaR is convex and continuous in \(z\);
therefore its sublevel set intersected with the compact interval \(I\) is a
compact interval \(K_{\theta,\kappa}\).  Because \(\mu_1-\mu_2>0\), the
objective is strictly increasing in \(z\).  Its unique maximiser over a
non-empty compact interval is the right endpoint
\(\sup K_{\theta,\kappa}\).  Since \(x_1<x_2\) is equivalent to
\(z<A-z\), reversal is equivalent to \(\sup K_{\theta,\kappa}<A/2\).
That inequality is equivalent to the absence of a feasible point in
\([A/2,\overline z]\).

If \(r_\theta\) is non-decreasing on the upper half of \(I\), the minimum risk
on that half is \(r_\theta(A/2)\).  Thus the upper half contains no feasible
point if and only if \(r_\theta(A/2)>\kappa\).  A feasible point below the
halfway mark ensures the problem remains feasible.  Continuity and strict
monotonicity of \(r_\theta(A/2)\) in \(\theta\), together with a crossing of
\(\kappa\), give existence and uniqueness of \(\theta^*\) by the intermediate
value theorem.  Removing either strict monotonicity or the crossing condition
removes the unique-threshold conclusion.

## Theorem 2

Minimise \(-\mu^\top x\) subject to the convex inequalities.  Attach
non-negative multipliers \(\eta,\gamma,\beta,\rho,\chi,\lambda,a,b\) to,
respectively, CVaR, land, budget, rotation, sign-converted contract, shared
capacity, lower-bound, and upper-bound constraints.  The Lagrangian
subgradient in \(x\) is

\[
-\mu+\eta d+\gamma\mathbf1+\beta c+R^\top\rho-K^\top\chi
+G^\top\lambda-a+b.
\]

Setting this expression to zero, together with primal feasibility, dual
feasibility and multiplier-slack products equal to zero, gives the convex KKT
system.  Under a constraint qualification it is necessary and sufficient.
For a bounded finite-scenario LP, LP strong duality supplies the same
necessity and sufficiency without a separate differentiability assumption.

In the Rockafellar-Uryasev LP, stationarity of the free VaR variable forces
the tail-scenario weights to sum to the CVaR multiplier.  Stationarity of each
non-negative excess variable bounds its normalised weight by
\(w_s/(1-\alpha)\).  At atoms, fractional weights satisfy these equations.
Thus the finite-scenario system accounts for every auxiliary variable.

## Proposition 1

CVaR is monotone under convex order for integrable losses.  Hence the assumed
pointwise order gives the risk inequality.  Risk sublevel sets are therefore
nested.  Maximising the same linear objective over nested feasible sets gives
the optimal-value order.  Nothing in set inclusion orders individual
coordinates of possibly different optimisers.

## Proposition 2

The second and third inequalities in Definition 1 state that \(x^{MV}\) has
strictly larger true-law loss-CVaR than a distinct feasible tail-aware
allocation.  Therefore \(x^{MV}\) cannot be tail-risk-optimal.  If its
true-law CVaR also exceeds \(\kappa\), it violates the declared risk ceiling.
The variance inequality explains why the conventional diagnostic can still
recommend it.

## Theorem 3

Any uninformed action defines a constant signal-contingent policy.  When that
policy is admissible, the informed optimisation is over a superset and cannot
have lower value.  If one action is optimal for every posterior, selecting it
after every signal attains the uninformed value, so information value is zero.
If posterior optima are unique, differ on positive-probability signal events,
and yield strict improvement on at least one event, integration gives strict
positive value.  Nested flexibility sets weakly raise each of the informed
and uninformed optimised values.  Their difference need not be monotone
because it is the difference of two weakly increasing functions.

## Proposition 3

Increasing differences and nested lattices imply monotone optimal policies
by standard monotone comparative statics.  If posterior-optimal actions
change on a positive-probability event and the increasing-differences
inequality is strict there, the gain from signal precision is strictly larger
at the higher flexibility level.  This is strict complementarity.

## Proposition 4

At \(\phi=1\), all state margins equal \(\bar\pi\).  Posteriors therefore
induce the same optimisation problem, a common action is optimal, and Theorem
3 gives zero information value.  If information value is positive at
\(\phi=0\) and the value function is continuous in the interpolated margins,
it must decline somewhere along \([0,1]\).  On every interval with negative
increment, shock-buffering flexibility substitutes for information.
