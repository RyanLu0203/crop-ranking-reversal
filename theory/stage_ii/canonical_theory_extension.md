# Stage II canonical theory extension

## 1. Scope, baseline and result classes

This document strengthens the positive theoretical contribution without
replacing the teacher's multi-crop stochastic acreage-allocation architecture.
The authoritative sign, feasible-set, CVaR, multiplicity and dependence repairs
remain CT1--CT10 in `theory/repaired/canonical_theorem_set.md`. In particular,

\[
\max_{x\in X}\ \mu^\top x
\quad\text{subject to}\quad
r_\alpha(x):=\operatorname{CVaR}_\alpha[-\Pi(x,\omega)]\leq\kappa,
\]

where

\[
X=\{x:\ell\leq x\leq u,\ \mathbf1^\top x\leq A,\ c^\top x\leq B,\ Gx\leq g\}.
\]

All Stage II statements are tagged as `PROVED`, `PROVED_CONDITIONAL`,
`NUMERICAL_HYPOTHESIS`, `COUNTEREXAMPLE_BOUNDARY`, or
`EMPIRICAL_HYPOTHESIS`. Definitions are not empirical findings. Numerical and
empirical hypotheses are future tests, not current evidence.

## 2. What a ranking identifies

Let \(s\) be a suitability vector and let \(\succeq_s\) be its weak order,
including tie classes. A complete decision primitive is

\[
\vartheta=(\mu,P_\pi,X,\alpha,\kappa),
\]

where \(P_\pi\) is the joint per-acre profit law. Let
\(S(\vartheta)\) be the corresponding optimal solution set and let
\(\mathfrak T\) be a declared class of optimizer selections. A selection may be
set-valued (the identity on the full optimal face) or a deterministic rule used
for a selected numerical comparison.

### Definition S2-D01 — allocation identified set

For an admissible primitive class \(\Theta(s)\) and selection class
\(\mathfrak T\), define

\[
\mathcal I_x(s;\Theta,\mathfrak T)
=\bigcup_{\vartheta\in\Theta(s)}\
  \bigcup_{T\in\mathfrak T} T(S(\vartheta)).
\]

This is the set of allocations compatible with the ranking and every additional
restriction explicitly encoded in \(\Theta\) and \(\mathfrak T\). It makes four
sources of missing information visible:

1. **cardinal margins:** the levels and gaps in \(\mu\), not only an order;
2. **risk law:** marginal distributions, dependence and the loss-CVaR limit;
3. **operational geometry:** land, budget, rotation, contract and crop bounds;
4. **selection:** which point is used when the optimum is a face.

The ranking point-identifies allocation only when this set is a singleton. It
rank-identifies a pair \((i,j)\) only when every element has the same declared
acreage order for that pair.

### Proposition S2-P01 — identified-set contraction (`PROVED`)

If \(\Theta_2(s)\subseteq\Theta_1(s)\) and
\(\mathfrak T_2\subseteq\mathfrak T_1\), then

\[
\mathcal I_x(s;\Theta_2,\mathfrak T_2)
\subseteq
\mathcal I_x(s;\Theta_1,\mathfrak T_1).
\]

Adding valid cardinal, feasibility, distributional or selection information can
shrink the identified set; it cannot enlarge it. The proposition does not say
that any particular added datum is sufficient for singleton identification.

### Proposition S2-P02 — risk-feasible exchange certificate (`PROVED_CONDITIONAL`)

Fix a strict score pair \(s_i>s_j\) and suppose \(\mu_i>\mu_j\). If every
risk-feasible allocation satisfying \(x_j-x_i>\tau_x\) admits a finite
\(t>0\) for which

\[
x+t(e_i-e_j)\in X,
\qquad r_\alpha(x+t(e_i-e_j))\leq\kappa,
\]

then no optimizer reverses the pair. It is enough to establish the risk part by
direct finite-step evaluation, or locally by strict CVaR slack plus continuity,
or at a binding boundary by a strictly negative directional derivative. A zero
directional derivative is not enough.

This is a positive no-reversal condition: a higher-ranked crop also has the
higher cardinal margin, and any reversed allocation can be profitably exchanged
toward it without violating the actual constraints. It does not apply when a
bound, contract, rotation rule, budget or CVaR boundary blocks that exchange.

### Corollary S2-C01 — restricted top-rank preservation (`PROVED_CONDITIONAL`)

Let

\[
X_0=\{x\geq0:\mathbf1^\top x\leq A\},\qquad A>0,
\]

and suppose the CVaR constraint is redundant on \(X_0\). If crop \(k\) is the
unique top score, score order and expected-margin order agree at the top, and

\[
\mu_k>\max\{0,\mu_j:j\ne k\},
\]

then the unique optimizer is \(x^*=Ae_k\). This is a winner-take-all top-rank
anchor, not a theorem that the entire acreage vector must strictly reproduce
all lower score ranks.

## 3. Cardinal margin channel

The margin channel is the vector \(\mu\), measured in currency per acre. A
ranking-equivalent transformation can preserve every score order while changing
\(\mu_i-\mu_j\), the objective opportunity cost of reallocating one acre from
\(i\) to \(j\). Hence ordinal invariance and cardinal decision invariance are
different claims.

With linear returns, acreage need not respond smoothly or monotonically to a
margin gap. A selected LP optimum may remain at the same vertex over an interval,
jump at a basis change, or range over an optimal face at a tie. Accordingly,

> **S2-H01 (`NUMERICAL_HYPOTHESIS`).** Holding score order, scenarios,
> feasibility, risk settings and selection fixed, controlled changes in a
> cardinal margin gap may change selected acreage, optimal-face bounds and
> reversal classification. Null, discontinuous and nonmonotone outcomes are
> admissible and must be retained.

The theoretical contribution is the separation of the cardinal pressure from
the ordinal input, not a universal crop-specific comparative static.

## 4. Complete local mechanism accounting

At an optimizer \(x^*\), select an atom-safe subgradient
\(d\in\partial r_\alpha(x^*)\). Under CT5, for a crop pair \((i,j)\),

\[
\underbrace{\mu_i-\mu_j}_{M_{ij}}
=
\underbrace{\lambda(d_i-d_j)}_{R_{ij}}
+\underbrace{\beta(c_i-c_j)}_{B_{ij}}
+\underbrace{(G^\top\eta)_i-(G^\top\eta)_j}_{O_{ij}}
+\underbrace{-(a_i-a_j)+(b_i-b_j)}_{Q_{ij}}.
\tag{S2.1}
\]

Here \(\lambda,\beta,\eta,a,b\geq0\) are the risk, budget, shared-row,
lower-bound and upper-bound multipliers under the canonical minimization
Lagrangian. Every displayed term has objective-currency-per-acre units. The
common land term cancels because both crops use one acre per acre. If later
models introduce heterogeneous land coefficients, their differential must be
restored.

### Theorem S2-T01 — KKT pressure identity (`PROVED`)

Equation (S2.1), primal feasibility, dual feasibility and complementary
slackness form a complete local optimality-pressure account. The registered
numerical residual is

\[
\varepsilon_{ij}=M_{ij}-(R_{ij}+B_{ij}+O_{ij}+Q_{ij}),
\]

and must be zero analytically and within the frozen solver tolerance
numerically. No undefined `gap_ij` remains.

The terms do **not** add to acreage and cannot be normalized into causal acreage
shares. Opposing pressures can cancel, multiplier values can change at a basis
switch, and the identity does not order \(x_i\) and \(x_j\).

## 5. Operational mechanisms and acreage attribution

### Proposition S2-P03 — operational mechanism trichotomy (`PROVED_CONDITIONAL`)

Relative to a declared pair and tolerance, an operational restriction can have
three logically distinct roles:

1. **direct forcing:** feasible-coordinate ranges satisfy
   \(\sup_Xx_i+\tau_x<\inf_Xx_j\), so reversal holds before optimization;
2. **marginal pressure:** a positive budget/shared-row multiplier creates a
   nonzero differential term \(B_{ij}\) or \(O_{ij}\) in (S2.1);
3. **boundary or selection effect:** lower/upper normals or an optimal face make
   the reported acreage order boundary- or selection-dependent.

The categories can coexist. Binding frequency alone establishes none of the
three: direct forcing requires a feasible-set range audit, marginal pressure
requires certified duals, and selection effects require an optimal-face audit.

### Definition S2-D03 — selected block attribution

Let the frozen blocks be cardinal margins, operational constraints, downside
risk and dependence specification. For each subset \(S\) of blocks, let
\(F(S)\) be the allocation selected by one declared rule from the corresponding
coherent model. For an ordered path \(b_1,\ldots,b_K\),

\[
\delta_k=F(\{b_1,\ldots,b_k\})-F(\{b_1,\ldots,b_{k-1}\}).
\]

Path increments telescope but depend on order. The symmetric selected
attribution for block \(b\) is the vector Shapley value

\[
\Phi_b=\sum_{S\subseteq\mathcal B\setminus\{b\}}
\frac{|S|!(K-|S|-1)!}{K!}\,[F(S\cup\{b\})-F(S)].
\tag{S2.2}
\]

### Proposition S2-P05 — attribution efficiency (`PROVED_CONDITIONAL`)

If every subset is solved with coherent fallback primitives and the same
deterministic selection rule, then

\[
\sum_b\Phi_b=F(\mathcal B)-F(\varnothing).
\]

This is an accounting identity for the **selected model outputs**. It is not an
invariance claim over the full optimal face. GOAL-12 must report alternative
path orders and coordinate/contrast ranges obtained from objective-equivalent
faces; independent envelope endpoints need not themselves form one jointly
attainable Shapley vector.

## 6. Downside risk and dependence

### Proposition S2-P04 — risk-limit contraction (`PROVED`)

For fixed \(X\), profit law and \(\alpha\), if \(\kappa_1\leq\kappa_2\),

\[
R(\kappa_1)=\{x\in X:r_\alpha(x)\leq\kappa_1\}
\subseteq R(\kappa_2).
\]

The optimal expected-profit value is therefore weakly nondecreasing in
\(\kappa\). Tightening the risk limit may leave the full or selected optimum
unchanged (CT4), change it, or make the model infeasible. No individual crop's
acreage is generally monotone in \(\kappa\).

### Proposition S2-P06 — ordered-loss contraction (`PROVED_CONDITIONAL`)

Fix margins, marginals, operations and a named valid dependence family. If a
proved order gives

\[
r_{\alpha,\theta_1}(x)\leq r_{\alpha,\theta_2}(x)
\quad\text{for every }x\in X,
\]

then \(R_{\theta_2}(\kappa)\subseteq R_{\theta_1}(\kappa)\), and the optimal
expected-profit value is weakly lower under \(\theta_2\). This is a risk-set and
value result. Crop-specific acreage, reversal and a unique crossing remain
unproved without further selection and monotonicity structure.

> **S2-H02 (`NUMERICAL_HYPOTHESIS`).** Within a validated named family, the
> selected allocation and reversal region may respond to dependence. GOAL-12
> must hold marginals and operations fixed, use common random numbers only for
> declared paired comparisons, audit active bases/faces, and retain null or
> nonmonotone responses.

Cross-family comparisons are model sensitivity, never an ordering by raw family
parameter or a scalar lower-tail coefficient.

## 7. Diversification and misspecification

For allocation \(x\), define shares \(w_i=x_i/\sum_jx_j\) when acreage is
positive and concentration \(H(x)=\sum_iw_i^2\). Every diversification claim
must name a comparator \(x^0\) and evaluation law \(P\).

### Definition S2-D02 — diversification outcome vector

- **variance diversification:**
  \(\operatorname{Var}_P[\Pi(x)]<\operatorname{Var}_P[\Pi(x^0)]\);
- **tail diversification:**
  \(r_{\alpha,P}(x)<r_{\alpha,P}(x^0)\);
- **allocation diversification:** \(H(x)<H(x^0)\);
- **true-law feasibility violation:**
  \(v_P(x)=[r_{\alpha,P}(x)-\kappa]_+\);
- **true-law objective regret:** when \(x\) is true-law feasible,
  \(\mathcal R_P(x)=V_P^*-\mu_P^\top x\), where \(V_P^*\) is the true-law
  constrained optimum value.

### Proposition S2-P07 — non-equivalence (`COUNTEREXAMPLE_BOUNDARY`)

Lower concentration, lower variance, lower true-law CVaR, true-law feasibility
and lower regret do not imply one another in general. Hence a pairwise
low-correlation/high-tail-dependence flag remains descriptive; it cannot alone
establish optimizer inclusion, exclusion, welfare or decision quality.

### Proposition S2-P08 — regret/violation separation (`PROVED_CONDITIONAL`)

Let \(x^Q\) be chosen under assumed law \(Q\) and evaluated under true law
\(P\). First report \(v_P(x^Q)\). If this is positive, \(x^Q\) is not a
feasible candidate for the true constrained problem and objective regret is not
the only harm. If \(v_P(x^Q)=0\), then

\[
\mathcal R_P(x^Q)=V_P^*-\mu_P^\top x^Q\geq0.
\]

A substantive pseudo-diversification finding requires an assumed-law
improvement in variance or concentration together with a preregistered adverse
true-law tail, violation or regret outcome. Each component is reported
separately.

## 8. Information and flexibility

Let experiment \(q\) generate a signal \(Z_q\) before acreage is chosen. A
policy \(\delta\) maps signals to allocations in \(X(\phi)\). The informed
policy set includes the same ex-ante loss-CVaR restriction as the uninformed
problem:

\[
\mathcal D(q,\phi)=\left\{\delta:
\delta(Z_q)\in X(\phi),\quad
\operatorname{CVaR}_\alpha[-\Pi(\delta(Z_q),\omega)]\leq\kappa\right\}.
\]

Define

\[
I(q,\phi)=\sup_{\delta\in\mathcal D(q,\phi)}E[\Pi(\delta(Z_q),\omega)],
\]

and let \(U(\phi)\) be the same supremum restricted to constant policies.
Operational information value is

\[
\operatorname{VOI}(q,\phi)=I(q,\phi)-U(\phi).
\]

This timing retains the teacher's CVaR architecture and makes the ignore-signal
policy-space inclusion explicit.

### Theorem S2-T02 — actionability and informativeness (`PROVED`)

1. \(\operatorname{VOI}(q,\phi)\geq0\).
2. If an optimal informed policy can be chosen constant almost surely, then
   \(\operatorname{VOI}(q,\phi)=0\).
3. If \(q_2\) can reproduce \(q_1\) by a registered garbling, then
   \(I(q_2,\phi)\geq I(q_1,\phi)\) and thus
   \(\operatorname{VOI}(q_2,\phi)\geq\operatorname{VOI}(q_1,\phi)\).
4. If \(X(\phi_1)\subseteq X(\phi_2)\) and the induced policy spaces preserve
   feasibility, both \(I\) and \(U\) are weakly nondecreasing in flexibility.
   Their difference need not be.

### Theorem S2-T03 — conditional complementarity (`PROVED_CONDITIONAL`)

Let the precision and flexibility sets be lattices \(\mathcal Q\) and
\(\Phi\), let the policy domain be a lattice \(\mathcal Y\), and let
\(\Gamma(q,\phi)\subseteq\mathcal Y\) be a nonempty compact sublattice that is
increasing in the strong set order. Suppose the informed policy payoff
\(W(y,q,\phi)\) is upper semicontinuous and jointly supermodular on
\(\mathcal Y\times\mathcal Q\times\Phi\). Then

\[
I(q,\phi)=\max_{y\in\Gamma(q,\phi)}W(y,q,\phi)
\]

is supermodular in \((q,\phi)\). If the uninformed value \(U(\phi)\) does not
depend on \(q\), \(\operatorname{VOI}(q,\phi)=I(q,\phi)-U(\phi)\) has
increasing differences between information precision and flexibility. Strict
complementarity requires a strict cross-difference; differentiability is not
required.

These hypotheses must be verified for the actual model. In particular, the
multi-crop fixed-land simplex is not closed under componentwise meet and join.
A directly applicable restricted case is a two-crop model parameterized by one
ordered acreage share whose feasible set is an interval, provided the policy
payoff and risk-feasible correspondence satisfy the stated order conditions.

### Boundary S2-B01 (`COUNTEREXAMPLE_BOUNDARY`)

Nested action sets alone do not imply complementarity. Flexibility may add only
dominated actions (zero interaction) or add a common robust action that reduces
the value of conditioning (substitution). A positive GOAL-12 interaction is
therefore promoted as theorem-linked evidence only if S2-T03's structural gate
or a preregistered finite-design cross-difference gate passes.

## 9. Theory-to-evidence boundary

The theory package establishes logical and conditional mechanisms. It contains
no calibrated crop parameter, no prevalence estimate and no empirical welfare
claim. GOAL-12 must test S2-H01 and S2-H02 and quantify selected/face-aware
counterfactuals without tuning for reversal. GOAL-15 may test only observable
predictions with pre-decision timing; it may not infer a farmer CVaR limit,
private contract, optimum or causal information value from acreage alone.
