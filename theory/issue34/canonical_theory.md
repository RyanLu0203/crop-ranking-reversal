# Issue #34 canonical theory

This record preserves the supervisor Draft's intended mechanism while replacing
its invalid unrestricted equivalences and monotonicity claims.  Full proofs are
in `proofs.md`; executable witnesses are in
`theory/proofs/computational_checks/test_issue34_theory.py`.

## 1. Model

There are \(n\) crops.  Acreage \(x\in\mathbb R_+^n\) is chosen before
stochastic price and yield are realised.  Per-acre margin and total profit are

\[
\widetilde\pi_i=\widetilde P_i\widetilde Y_i-C_i,\qquad
\Pi(x)=\widetilde\pi^\top x,\qquad L(x)=-\Pi(x).
\]

The operational set is

\[
X=\{x:\mathbf 1^\top x\le A,\ c^\top x\le B,\ R x\le r,\
Kx\ge k,\ Gx\le h,\ \ell\le x\le u\}.
\]

Rows of \(R\) encode rotation limits, rows of \(K\) encode contractual
minimums, and rows of \(G\) encode labour, equipment, irrigation, storage, or
other shared capacities.  Idle land is \(A-\mathbf1^\top x\) and is therefore
explicit even when no separate variable is introduced.

For confidence level \(\alpha\), loss-CVaR is

\[
r_\alpha(x)=\min_{v\in\mathbb R}
\left[v+\frac{1}{1-\alpha}\mathbb E(L(x)-v)_+\right].
\]

The decision problem is

\[
\max_{x\in X}\ \mu^\top x
\quad\text{s.t.}\quad r_\alpha(x)\le\kappa .
\]

The suitability score \(s\) is external to this objective.  It may measure
soil or climate suitability, historical yield potential, predicted yield, or
another recommendation target, but it is not silently identified with
expected margin.

## 2. Definitions

For \(s_i>s_j\), an allocation has a pairwise reversal when \(x_i<x_j\).
The reversal is strong when the highest-ranked crop receives strictly less
acreage than every lower-ranked crop.  Let \(S_\kappa\) denote the optimal set.

- possible reversal: some \(x\in S_\kappa\) reverses the pair;
- universal reversal: every \(x\in S_\kappa\) reverses the pair;
- selected reversal: a declared deterministic selector \(\sigma(S_\kappa)\)
  reverses the pair.

These definitions prevent a solver's arbitrary point on an optimal face from
being mistaken for a universal result.

## 3. Exact two-crop reversal frontier

**Theorem 1 (restricted necessary-and-sufficient reversal
characterisation).**  Consider two crops with \(s_1>s_2\), fixed total planted
land \(x_1+x_2=A\), and a non-empty compact operational interval
\(I=[\underline z,\overline z]\) for \(z=x_1\).  Let
\(r_\theta(z)=\operatorname{CVaR}_\alpha[-z\widetilde\pi_1
-(A-z)\widetilde\pi_2]\) under a declared joint-law path \(\theta\), and

\[
K_{\theta,\kappa}=\{z\in I:r_\theta(z)\le\kappa\}.
\]

If \(\mu_1>\mu_2\), the unique optimal share is
\(z^*(\theta,\kappa)=\sup K_{\theta,\kappa}\).  Consequently,

\[
x_1^*<x_2^*
\quad\Longleftrightarrow\quad
\sup K_{\theta,\kappa}<A/2
\quad\Longleftrightarrow\quad
K_{\theta,\kappa}\cap[A/2,\overline z]=\varnothing .
\]

If \(r_\theta\) is non-decreasing on
\([A/2,\overline z]\), reversal is equivalent to
\(r_\theta(A/2)>\kappa\), provided a risk-feasible point below \(A/2\)
exists.  If \(r_\theta(A/2)\) is continuous and strictly increasing in
\(\theta\) on a named family path and crosses \(\kappa\), the unique family-
specific frontier is the solution of
\(r_{\theta^*}(A/2)=\kappa\).  Without those monotonicity and crossing
assumptions, the correct object is the set
\(\{\theta:\sup K_{\theta,\kappa}<A/2\}\), which may be disconnected.

This theorem is the primary analytical repair of the Draft's informal
``risk-adjusted margin gap'' equivalence.  It characterises the acreage level
directly and does not infer it from marginal stationarity.

## 4. Full KKT and active-set interpretation

**Theorem 2 (complete KKT system).**  Under a convex constraint
qualification, or for the bounded feasible finite-scenario LP, a feasible
solution is optimal if and only if there are non-negative multipliers for
loss-CVaR, land, budget, every rotation row, every contract row after sign
conversion, every shared-capacity row, and every crop bound, together with
scenario-excess and free-VaR dual conditions, satisfying primal feasibility,
dual feasibility, stationarity, and complementarity.

For a CVaR subgradient \(d\in\partial r_\alpha(x^*)\), acreage stationarity is

\[
-\mu+\eta d+\gamma\mathbf1+\beta c+R^\top\rho-K^\top\chi
+G^\top\lambda-a+b=0.
\]

Pairwise subtraction yields a marginal-value comparison.  It does not yield
an acreage ranking unless combined with the active set, feasibility geometry,
uniqueness, and selection rule.  The finite-scenario implementation verifies
the stationarity of \(x\), the free VaR threshold, and every excess variable.

## 5. Dependence path and reversal sets

**Proposition 1 (named-family feasible-set ordering).**  Fix crop marginals.
If, for every \(x\) in a declared domain,
\(L_{\theta_1}(x)\preceq_{\rm cx}L_{\theta_2}(x)\), then
\(r_{\alpha,\theta_1}(x)\le r_{\alpha,\theta_2}(x)\).  If the domain is all of
\(X\), the risk-feasible set under \(\theta_2\) is contained in that under
\(\theta_1\), and optimal expected profit cannot increase.  Individual crop
shares need not be monotone.

Gaussian, Student-\(t\), and Clayton paths in the numerical analysis are
therefore reported family by family.  A scalar lower-tail coefficient is not
used as a cross-family sufficient statistic.  The empirical object is a phase
diagram containing reversal, non-reversal, active-set, infeasible, and
multiple-optimum cells.

## 6. Diversification failure

Let \(x^{MV}\) be the allocation selected using a variance or matched-Gaussian
criterion and \(x^{T}\) the expected-profit optimum under the true-law
loss-CVaR ceiling.

**Definition 1 (executable diversification failure).**  Diversification
failure occurs when

\[
\operatorname{Var}_G(\Pi(x^{MV}))
\le \operatorname{Var}_G(\Pi(x^{0})),\qquad
r_{\alpha,T}(x^{MV})>r_{\alpha,T}(x^{T}),\qquad
x^{MV}\ne x^{T},
\]

where \(G\) is the conventional Gaussian or linear-correlation assessment,
\(T\) is the declared tail-aware law, and \(x^0\) is the registered comparison
policy.  A stronger operational failure occurs when
\(r_{\alpha,T}(x^{MV})>\kappa\).

**Proposition 2.**  If \(x^{MV}\) is selected by the conventional criterion,
\(x^T\) is feasible for the true-law problem, and the three inequalities in
Definition 1 hold, then conventional diversification advice is not
tail-risk-optimal.  Under the stronger inequality it is also risk-infeasible.
This criterion separates variance, Gaussian, lower-tail, CVaR, and allocation
notions of diversification without claiming that one scalar dependence
measure orders all of them.

## 7. Information and flexibility

Nature draws a crop-yield state, generates a noisy pre-plant signal, and leaves
some acreage committed.  The producer observes the signal and chooses a
contingent allocation from a flexibility-indexed action set.  Profit is then
realised.  The ex-ante CVaR constraint is applied to the combined
state-signal-contingent loss distribution.

**Theorem 3 (value, strictness, and zero interaction).**  If ignoring the
signal is admissible, information value is non-negative.  It is zero when one
common action is optimal for every posterior.  If posterior optima are unique
and differ on signal events with positive probability, and the contingent
policy is strictly better on at least one such event, information value is
strictly positive.  Under nested acreage-recourse sets, the informed value and
uninformed value are each weakly increasing, but their difference need not be
monotone without increasing differences.

**Proposition 3 (conditional complementarity).**  If the state-action payoff
has increasing differences in signal precision and flexibility, action sets
are nested, and posterior-optimal actions change on events of positive
probability, information and flexibility are strictly complementary.

**Proposition 4 (substitution by shock buffering).**  Let flexibility
\(\phi\) contract state-dependent margins toward a common margin vector:
\(\pi_\omega(\phi)=(1-\phi)\pi_\omega+\phi\bar\pi\).  At \(\phi=1\), the
signal has zero value.  Whenever information has positive value at
\(\phi=0\), continuity implies a region in which increased shock-buffering
flexibility reduces information value.  Information and flexibility are
substitutes there.  This does not contradict Proposition 3 because payoff
differences, rather than only the feasible action set, change with \(\phi\).

The registered agricultural experiment reports all three regions: zero value
at no actionability or no informativeness, strict complementarity under
post-signal acreage reallocation, and substitution when irrigation/input-
switching recourse buffers the state that the signal predicts.
