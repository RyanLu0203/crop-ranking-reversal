# Canonical repaired theorem set

## 1. Model retained from the teacher Draft

Let $(\Omega,\mathcal F,P)$ be a probability space and let $i=1,\ldots,n$, with $n\ge2$, index crops. Acreage is $x\in\mathbb R^n$. Random per-acre profit is

$$
\widetilde\pi_i(\omega)=\widetilde p_i(\omega)\widetilde y_i(\omega)-c_i,
\qquad
\Pi(x,\omega)=\sum_i x_i\widetilde\pi_i(\omega),
\qquad
L(x,\omega)=-\Pi(x,\omega).
$$

Price and yield may be dependent within and across crops. Costs are deterministic in the baseline; profits may be negative. Acres are homogeneous and returns are linear in acreage. The model excludes fixed setup costs, crop-interaction terms, and endogenous price feedback unless a later extension states otherwise.

The operational feasible set is the nonempty polytope

$$
X=\{x\in\mathbb R^n:\ell\le x\le u,\ \mathbf1^\top x\le A,\ c^\top x\le B,\ Gx\le g\}.
$$

Rows of $Gx\le g$ represent rotation, contractual, agronomic, and other shared operational restrictions. The land inequality allows idling; full land use is a derived result only under an admissible profitable expansion.

For confidence $\alpha\in(0,1)$, define loss CVaR by

$$
r_\alpha(x)=\operatorname{CVaR}_\alpha(L(x))
=\min_{v\in\mathbb R}\left\{v+\frac{1}{1-\alpha}E[(L(x)-v)_+]\right\}.
$$

The canonical optimization problem is

$$
(P_\kappa)\qquad
\max_{x\in X}\ \mu^\top x
\quad\text{subject to}\quad r_\alpha(x)\le\kappa,
\qquad \mu_i=E[\widetilde\pi_i].
$$

For finite scenarios $s=1,\ldots,S$ with probabilities $w_s>0$, $\sum_s w_s=1$, and profit vectors $\pi_s$, $(P_\kappa)$ is the LP

$$
\begin{aligned}
\max_{x,v,q}\quad &\mu^\top x\\
\text{s.t.}\quad
&v+\frac{1}{1-\alpha}\sum_s w_sq_s\le\kappa,\\
&-\pi_s^\top x-v\le q_s &&(s=1,\ldots,S),\\
&q_s\ge0 &&(s=1,\ldots,S),\\
&x\in X,\quad v\in\mathbb R.
\end{aligned}
$$

The auxiliary variables $v,q$ have zero objective coefficients.

## 2. Dependence scope

Marginal profit CDFs $F_i$ and a valid $n$-copula $C_\theta$ define

$$
P(\widetilde\pi_1\le z_1,\ldots,\widetilde\pi_n\le z_n)
=C_\theta(F_1(z_1),\ldots,F_n(z_n)).
$$

Pairwise lower-tail coefficients are

$$
\lambda_{L,ij}=\lim_{u\downarrow0}\frac{C_{ij}(u,u)}{u},
$$

when the limit exists. A coefficient does not identify or globally order copulas, conditional tail means, CVaR contributions, or optimal allocations. Any dependence comparative static must fix the marginals and a named valid family and must verify an order of the relevant portfolio-loss distributions.

## 3. Suitability and reversal definitions

A suitability vector $s$ induces a weak order. Ties form equivalence classes. Proportional and winner-take-all allocations are benchmark recommendation mappings, not feasible optima by definition.

Let

$$
S_\kappa=\arg\max\{\mu^\top x:x\in X,\ r_\alpha(x)\le\kappa\}
$$

and let $\tau_x\ge0$ be a declared acreage tolerance. For a strict suitability pair $s_i>s_j$:

- pairwise reversal at $x$: $x_j-x_i>\tau_x$;
- possible reversal: at least one $x\in S_\kappa$ reverses;
- universal reversal: every $x\in S_\kappa$ reverses;
- selected reversal: a declared deterministic selection $T(S_\kappa)$ reverses;
- strong reversal: $x_i\le\tau_x$ and $x_j>\tau_x$;
- top-rank reversal: some crop in the highest suitability tie class receives at least $\tau_x$ less acreage than a lower-ranked crop.

Every possible, universal, strong, or top-rank claim states whether it concerns the whole optimal set or a selected solution.

## 4. Structural results

### Theorem CT1 — Existence, convexity, and finite-scenario linearity

Assume $X$ is nonempty and compact and every $\widetilde\pi_i$ is integrable. Then $(P_\kappa)$ has an optimizer whenever its risk-feasible set is nonempty. The risk-feasible set is convex. For a finite scenario distribution, $(P_\kappa)$ has the LP representation above.

### Proposition CT2 — Ordinal ranking information is insufficient

A weak or strict suitability ranking alone does not identify a cardinal acreage allocation. In particular, no monotone score ordering implies an acreage ordering without a recommendation mapping, objective, feasible set, and optimizer-selection rule.

### Proposition CT3 — Feasibility-forced universal reversal

If $s_i>s_j$ and

$$
\sup_{x\in X}x_i+\tau_x<\inf_{x\in X}x_j,
$$

then every feasible allocation, hence every optimizer, has a universal pairwise reversal from $i$ to $j$. The easily checked condition $u_i+\tau_x<\ell_j$ is sufficient.

### Proposition CT4 — Exact risk-slack invariance

Let $U=\arg\max_{x\in X}\mu^\top x$ and $R_\kappa=\{x\in X:r_\alpha(x)\le\kappa\}$. If $U\cap R_\kappa\ne\varnothing$, the constrained optimum value equals the unconstrained value and

$$
S_\kappa=U\cap R_\kappa.
$$

Consequently, a unique risk-feasible unconstrained optimizer is unchanged. Equality of the full solution sets requires $U\subseteq R_\kappa$; observing one slack optimum is not sufficient when $U$ is multiple.

### Theorem CT5 — Complete subgradient KKT characterization

Suppose $(P_\kappa)$ is feasible and either a convex constraint qualification holds or the finite-scenario LP is feasible and bounded. A feasible $x^*$ is optimal if and only if there exist

$$
\lambda,\gamma,\beta\ge0,\quad \eta\ge0,\quad a\ge0,\quad b\ge0,
\quad d\in\partial r_\alpha(x^*)
$$

such that

$$
0=-\mu+\lambda d+\gamma\mathbf1+\beta c+G^\top\eta-a+b,
$$

together with

$$
\begin{aligned}
&\lambda(r_\alpha(x^*)-\kappa)=0,\qquad
\gamma(\mathbf1^\top x^*-A)=0,\qquad
\beta(c^\top x^*-B)=0,\\
&\eta_k((Gx^*)_k-g_k)=0,\qquad
a_i(\ell_i-x_i^*)=0,\qquad
b_i(x_i^*-u_i)=0.
\end{aligned}
$$

For crops $i,j$, the exact pairwise stationarity identity is

$$
\mu_i-\mu_j
=\lambda(d_i-d_j)+\beta(c_i-c_j)
+(G^\top\eta)_i-(G^\top\eta)_j
-(a_i-a_j)+(b_i-b_j).
$$

The common land multiplier cancels. There is no undefined residual term. This identity characterizes marginal optimality; it does not by itself order acreage levels.

For a finite scenario optimizer $(x^*,v^*)$, one may select tail weights $\xi_s$ satisfying

$$
\xi_s=
\begin{cases}
0,&L_s(x^*)<v^*,\\
w_s/(1-\alpha),&L_s(x^*)>v^*,\\
[0,w_s/(1-\alpha)],&L_s(x^*)=v^*,
\end{cases}
\qquad \sum_s\xi_s=1,
$$

and then

$$
d=-\sum_s\xi_s\pi_s\in\partial r_\alpha(x^*).
$$

### Proposition CT6 — Risk-adjusted feasible-displacement certificate

Let $x$ be feasible and let $h$ be a nonzero operationally feasible direction: $x+th\in X$ for every sufficiently small $t\in[0,\epsilon]$. Suppose $\mu^\top h>0$ and at least one of the following holds:

1. the CVaR constraint is slack at $x$;
2. it binds and $r_\alpha'(x;h)<0$; or
3. direct evaluation establishes $r_\alpha(x+th)\le\kappa$ for some sufficiently small $t>0$.

Then $x$ is not optimal for $(P_\kappa)$. For a pairwise displacement $h=e_j-e_i$, these conditions give a rigorous sufficient certificate for shifting acreage from higher-ranked $i$ toward lower-ranked $j$. They do not imply that the final optimizer has $x_j>x_i$. The strict inequality in case 2 is essential: a zero derivative at an active nonlinear boundary need not yield a feasible step.

Conversely, at an optimum $x^*$ every direction in the tangent cone that is first-order risk-feasible satisfies $\mu^\top h\le0$.

### Theorem CT7 — Restricted dependence ordering

Fix the marginal profit distributions and a named copula family indexed by $\theta$. Suppose that for $\theta_1\preceq\theta_2$ and every $x$ in a declared domain $D\subseteq X$,

$$
L_{\theta_1}(x)\preceq_{\mathrm{cx}}L_{\theta_2}(x),
$$

where $\preceq_{\mathrm{cx}}$ denotes convex order. Then

$$
r_{\alpha,\theta_1}(x)\le r_{\alpha,\theta_2}(x)
\qquad(x\in D).
$$

If $D=X$, the risk-feasible sets are nested:

$$
R_\kappa(\theta_2)\subseteq R_\kappa(\theta_1),
$$

and the optimal expected-profit value is weakly nonincreasing in this order. No monotone crop-specific acreage or reversal conclusion follows without uniqueness/selection and additional structure. The assumption must be proved for the selected family; it cannot be replaced by monotonicity of $\lambda_L$ alone.

### Proposition CT8 — Reversal regions and crossing sets

For parameter $\theta$, define

$$
g_{ij}^{+}(\theta)=\max_{x\in S(\theta)}(x_j-x_i),\qquad
g_{ij}^{-}(\theta)=\min_{x\in S(\theta)}(x_j-x_i).
$$

The possible and universal reversal regions are

$$
\mathcal P_{ij}=\{\theta:g_{ij}^{+}(\theta)>\tau_x\},\qquad
\mathcal U_{ij}=\{\theta:g_{ij}^{-}(\theta)>\tau_x\}.
$$

For any selection $x^T(\theta)\in S(\theta)$,

$$
\mathcal U_{ij}\subseteq
\{\theta:x_j^T(\theta)-x_i^T(\theta)>\tau_x\}
\subseteq\mathcal P_{ij}.
$$

The boundaries of these sets are crossing sets and may be empty, disconnected, multiple, or interval-valued. If the optimizer is unique and continuous and its pairwise gap changes sign, a crossing exists. A unique point threshold additionally requires strict monotonicity and an endpoint crossing.

### Definition CT9 — Pseudo-diversification diagnostic

Given preregistered thresholds $\rho_0$ and $\lambda_0$, a pair is dependence-discordant when

$$
\rho_{ij}\le\rho_0
\quad\text{and}\quad
\lambda_{L,ij}\ge\lambda_0.
$$

The label pseudo-diversification is descriptive. Any mean-variance inclusion, CVaR exclusion, or risk comparison is a separate reported outcome. The diagnostic alone implies none of them.

### Theorem CT10 — Information actionability and weak flexibility monotonicity

Let $Z$ be observed before acreage is chosen and let $X(\phi_1)\subseteq X(\phi_2)$ for $\phi_1\le\phi_2$. Define posterior payoff $m_z(x)=E[\Pi(x,\omega)\mid Z=z]$,

$$
I(\phi)=E_Z\left[\max_{x\in X(\phi)}m_Z(x)\right],\qquad
U(\phi)=\max_{x\in X(\phi)}E_Z[m_Z(x)],
$$

and $\operatorname{VOI}(\phi)=I(\phi)-U(\phi)$. Then:

1. $\operatorname{VOI}(\phi)\ge0$.
2. If one common action $x^c\in X(\phi)$ is posterior-optimal almost surely, then $\operatorname{VOI}(\phi)=0$.
3. Both $I(\phi)$ and $U(\phi)$ are weakly nondecreasing under feasible-set expansion.
4. $\operatorname{VOI}(\phi)$ need not be monotone, strictly positive, differentiable, or supermodular in information and flexibility.

Strict information–flexibility complementarity is therefore a restricted extension or simulation hypothesis unless lattice, increasing-differences, and monotone-selection conditions are independently established.

## 5. Status of the teacher Draft's headline claims

- Ranking-reversal if-and-only-if theorem: replaced by CT5, CT6, and CT3.
- Profit-suitability corollary: retained only as ranking equivalence; it gives no acreage theorem.
- Tail-dependence monotonicity: replaced by conditional convex-order theorem CT7.
- Unique threshold: replaced by reversal regions/crossing sets CT8.
- Pseudo-diversification proposition: replaced by diagnostic CT9 and explicit counterexamples.
- Information–flexibility complementarity: replaced by actionability and weak monotonicity CT10; strict complementarity is not a general theorem.

## 6. Evidence boundary

All numerical values in the teacher Draft remain illustrative. The results above are mathematical statements or definitions only. Their simulation and empirical implications are frozen separately in the two mapping registries in this directory.
