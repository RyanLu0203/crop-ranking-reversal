# Proofs and counterexample boundaries for the Stage II extension

## S2-P01 — identified-set contraction

Take any \(x\in\mathcal I_x(s;\Theta_2,\mathfrak T_2)\). By definition there
exist \(\vartheta\in\Theta_2(s)\) and \(T\in\mathfrak T_2\) with
\(x\in T(S(\vartheta))\). The two set inclusions put the same
\(\vartheta\) in \(\Theta_1(s)\) and the same \(T\) in
\(\mathfrak T_1\), so \(x\in\mathcal I_x(s;\Theta_1,\mathfrak T_1)\).
This proves the inclusion. A set-valued object is point identified exactly when
it contains one point; no stronger inference is used.

## S2-P02 — risk-feasible exchange certificate

Suppose, to the contrary, that an optimizer \(x^*\) reverses the pair. By the
premise there is \(t>0\) such that
\(x'=x^*+t(e_i-e_j)\) satisfies both the operational and CVaR constraints.
Its objective difference is

\[
\mu^\top x'-\mu^\top x^*=t(\mu_i-\mu_j)>0,
\]

contradicting optimality. For the local sufficient cases: strict risk slack and
continuity preserve the inequality for sufficiently small \(t\); at a binding
boundary, a strictly negative directional derivative gives
\(r_\alpha(x^*+th)<r_\alpha(x^*)\) for sufficiently small positive \(t\).
Convex directional derivative equal to zero does not ensure a feasible finite
step, which is why the statement does not use a weak derivative condition.

## S2-C01 — restricted winner-take-all top-rank preservation

For any \(x\in X_0\),

\[
\mu^\top x
\leq \mu_k\sum_jx_j
\leq \mu_k A,
\]

where the first inequality is strict whenever any positive acreage is assigned
to a crop other than \(k\), and the second is strict when land is idle because
\(\mu_k>0\). The allocation \(Ae_k\) is feasible, the CVaR restriction is
redundant by assumption, and it attains \(\mu_kA\). It is therefore the unique
optimizer. Dropping redundancy, the unique margin order, positivity, or the
simplex geometry invalidates at least one inequality or feasibility step.

## S2-T01 — complete pairwise KKT pressure identity

The Stage I CT5 Lagrangian for minimization of \(-\mu^\top x\) is

\[
\mathcal L=-\mu^\top x+\lambda(r_\alpha(x)-\kappa)
+\gamma(\mathbf1^\top x-A)+\beta(c^\top x-B)
+\eta^\top(Gx-g)+a^\top(\ell-x)+b^\top(x-u).
\]

Stationarity at \(x^*\), after selecting
\(d\in\partial r_\alpha(x^*)\), gives

\[
0=-\mu+\lambda d+\gamma\mathbf1+\beta c+G^\top\eta-a+b.
\]

Subtract coordinate \(j\) from coordinate \(i\). The two land coefficients are
both one, so \(\gamma-\gamma=0\). Rearranging yields exactly equation (S2.1).
The residual is therefore zero. Each normal is paired with its declared
constraint and complementary-slackness equation under CT5, so no residual
constraint term can be hidden in an undefined symbol.

## S2-P03 — operational mechanism trichotomy

Direct forcing follows from CT3: coordinate-range separation makes the order
hold for every feasible point. Marginal pressure is precisely the nonzero
budget or shared-row differential in S2-T01 and therefore requires a certified
multiplier. Boundary effects are the lower/upper normal terms; selection effects
arise when the optimum contains allocations with different pairwise gaps.
These mechanisms are distinct by construction but not mutually exclusive.
A binding row can have the same coefficient for both crops and hence zero
pairwise pressure, while a nonbinding row has zero multiplier; thus binding
frequency alone does not establish either direct forcing or differential
pressure.

## S2-P04 — risk-limit contraction

If \(x\in R(\kappa_1)\), then
\(r_\alpha(x)\leq\kappa_1\leq\kappa_2\), hence
\(x\in R(\kappa_2)\). Maximizing the same objective over a subset cannot have a
higher value. The statement concerns sets and values only; a change between two
polyhedral faces can move different coordinates in either direction.

## S2-P05 — selected path and Shapley efficiency

For an ordered path, summing consecutive differences cancels every intermediate
term, leaving \(F(\mathcal B)-F(\varnothing)\).

For the Shapley identity, expand the coefficient on each \(F(S)\) after summing
\(\Phi_b\) over blocks. Every nonempty proper subset appears positively when
its last-added member is \(b\in S\) and negatively when a missing member is
added to it. The total positive and negative coefficients are equal and cancel.
The full set appears with coefficient one and the empty set with coefficient
minus one. Thus the sum is the full-minus-baseline selected change. This
combinatorial identity assumes one value \(F(S)\) per subset; changing the
selection rule across subsets changes the game being attributed.

## S2-P06 — ordered-loss contraction

The assumed pointwise risk order immediately gives
\(r_{\alpha,\theta_2}(x)\leq\kappa\Rightarrow
r_{\alpha,\theta_1}(x)\leq\kappa\). Therefore the higher-risk feasible set is
contained in the lower-risk set. The value result again follows by maximizing
the same linear objective over nested sets. Nothing in set inclusion orders
coordinates of different optimizers.

## S2-P07 — diversification non-equivalence

Consider two equal-probability states and two crops. Crop 1 has profit
\((0,0)\); crop 2 has profit \((-100,100)\). The concentrated allocation
\(x^0=(1,0)\) has concentration one, variance zero and loss CVaR zero at
\(\alpha=1/2\). The more allocation-diversified allocation
\(x=(1/2,1/2)\) has concentration one half, positive variance and loss CVaR
50. Thus lower concentration need not lower variance or tail risk.

Conversely, duplicating a payoff across two perfectly comoving crop columns
allows concentration to fall without changing portfolio profit, variance or
CVaR. A safe but lower-mean allocation can lower variance while increasing
objective regret. Finally, an allocation may lower an assumed-law variance or
CVaR while violating the true-law CVaR limit. These witnesses separate the four
constructs and disprove any general equivalence.

## S2-P08 — true-law regret and violation

If \(v_P(x^Q)>0\), then \(x^Q\) violates the true-law risk constraint by
definition and is not in the domain over which \(V_P^*\) is optimized. If
\(v_P(x^Q)=0\), it is true-law feasible. Optimality of the true-law solution
then gives \(V_P^*\geq\mu_P^\top x^Q\), proving nonnegative regret. No scalar
penalty combines infeasibility and regret because doing so would introduce an
unidentified welfare weight.

## S2-T02 — operational information value and informativeness

Constant policies are a subset of informed policies, so a supremum over the
larger set cannot be lower: \(I(q,\phi)\geq U(\phi)\). If an optimal informed
policy is constant, it belongs to the uninformed class and attains the same
value, giving equality.

If \(q_1\) is obtained by garbling \(q_2\), a decision maker observing
\(q_2\) can apply the registered stochastic garbling and then implement any
\(q_1\)-policy. This reproduces the joint distribution of actions and outcomes,
including its ex-ante CVaR, so every feasible \(q_1\)-policy value is attainable
under \(q_2\). The informed value is weakly higher. The prior and constant-policy
problem is the same, hence the VOI inequality follows.

When flexibility nests the operational sets and preserves the same risk
feasibility rule, every policy feasible at \(\phi_1\) remains feasible at
\(\phi_2\). The informed and constant-policy suprema each weakly rise. A
difference of two nondecreasing functions need not be nondecreasing.

## S2-T03 — conditional information--flexibility complementarity

Take two parameter points \(t_1=(q_1,\phi_1)\) and
\(t_2=(q_2,\phi_2)\), and optimizers \(y_1\in\Gamma(t_1)\),
\(y_2\in\Gamma(t_2)\). Strong-set-order monotonicity makes
\(y_1\wedge y_2\) feasible at \(t_1\wedge t_2\) and
\(y_1\vee y_2\) feasible at \(t_1\vee t_2\). Joint supermodularity gives

\[
W(y_1,t_1)+W(y_2,t_2)
\leq W(y_1\wedge y_2,t_1\wedge t_2)
+W(y_1\vee y_2,t_1\vee t_2).
\]

Each term on the right is bounded above by the corresponding optimized value,
so

\[
I(t_1)+I(t_2)\leq I(t_1\wedge t_2)+I(t_1\vee t_2).
\]

Thus \(I\) is supermodular. Subtracting \(U(\phi)\) from both information
levels cancels it in the precision cross-difference, so VOI has increasing
differences. Strict complementarity requires at least one strict inequality and
cannot be inferred from weak hypotheses.

## S2-B01 — no general complementarity

**Zero interaction.** Let one action \(a\) be uniquely best under every signal
and let flexibility add only a dominated action \(b\). Informed and uninformed
policies always choose \(a\), so VOI is zero at both flexibility levels.

**Substitution.** With two equally likely states, at low flexibility offer two
specialized actions with payoffs \((10,0)\) and \((0,10)\). Perfect information
is worth five relative to the best constant action. At high flexibility add a
common action with payoff \((9,9)\). The informed value remains ten while the
uninformed value rises from five to nine, so VOI falls from five to one. Nested
sets alone therefore allow information and flexibility to be substitutes.

**Lattice boundary.** On a fixed-land simplex, the componentwise maximum of two
feasible acreage vectors generally uses more than the available land. The
simplex is therefore not a sublattice under componentwise order. A generic
multi-crop invocation of lattice comparative statics is invalid until a
different closed order/domain is constructed and verified.
