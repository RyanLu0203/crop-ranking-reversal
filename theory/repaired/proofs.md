# Complete proof package for the canonical theorem set

## Proof of CT1

Integrability of each per-acre profit implies that $\mu$ is finite and that $L(x)$ is integrable for each fixed $x$. The function

$$
(x,v)\mapsto v+\frac{1}{1-\alpha}E[(L(x)-v)_+]
$$

is jointly convex because $L$ is affine in $x$ and the positive-part function is convex and nondecreasing. Partial minimization over $v$ preserves convexity, so $r_\alpha$ is convex and lower semicontinuous. Therefore $\{x:r_\alpha(x)\le\kappa\}$ is closed and convex. Its intersection with nonempty compact $X$ is compact. If that intersection is nonempty, the continuous linear objective attains a maximum.

For finite scenarios, introduce $q_s\ge L_s(x)-v$ and $q_s\ge0$. At any feasible $(x,v)$ the smallest feasible $q_s$ is $[L_s(x)-v]_+$, giving exactly the RU expression. Every constraint and the objective are linear, hence the representation is an LP.

## Proof of CT2

A ranking supplies only pairwise order relations among the score components. It contains no acreage scale. For two strictly ordered crops, both $(A,0)$ and $(0,A)$, as well as every convex combination, are compatible with the same score order because no allocation rule has been imposed. Adding more crops does not restore cardinal information. Thus ranking alone cannot identify acreage.

## Proof of CT3

For every $x\in X$,

$$
x_i\le\sup_{y\in X}y_i
<\inf_{y\in X}y_j-\tau_x
\le x_j-\tau_x.
$$

Hence $x_j-x_i>\tau_x$ at every feasible point and therefore at every optimizer. Since $x_i\le u_i$ and $x_j\ge\ell_j$, the stated bound condition implies the premise.

## Proof of CT4

Let $v_0=\max_{x\in X}\mu^\top x$. Because $R_\kappa\subseteq X$, the constrained value cannot exceed $v_0$. If $U\cap R_\kappa$ is nonempty, a point in the intersection is constrained-feasible and attains $v_0$, so the values are equal. A constrained optimizer must therefore attain $v_0$ and belongs to $U\cap R_\kappa$. Conversely every point in $U\cap R_\kappa$ is constrained-feasible and attains the constrained value. Thus $S_\kappa=U\cap R_\kappa$. The uniqueness and full-set statements follow immediately.

## Proof of CT5

Write the maximization as minimization of $-\mu^\top x$ with inequalities

$$
r_\alpha(x)-\kappa\le0,\quad
\mathbf1^\top x-A\le0,\quad
c^\top x-B\le0,\quad
Gx-g\le0,\quad
\ell-x\le0,\quad
x-u\le0.
$$

The Lagrangian is

$$
\mathcal L=
-\mu^\top x+\lambda(r_\alpha(x)-\kappa)
+\gamma(\mathbf1^\top x-A)+\beta(c^\top x-B)
+\eta^\top(Gx-g)+a^\top(\ell-x)+b^\top(x-u).
$$

Convex KKT necessity and sufficiency under the stated constraint qualification give primal feasibility, nonnegative multipliers, complementary slackness, and

$$
0\in-\mu+\lambda\partial r_\alpha(x^*)
+\gamma\mathbf1+\beta c+G^\top\eta-a+b.
$$

Selecting $d\in\partial r_\alpha(x^*)$ gives the displayed stationarity equation. Subtracting coordinate $j$ from coordinate $i$ cancels $\gamma$ and yields the exact pairwise identity.

For finite scenarios, let $v^*$ minimize the RU expression at $x^*$. A subgradient of $[L_s(x)-v]_+$ with respect to its scalar argument is zero below zero, one above zero, and any value in $[0,1]$ at zero. After multiplying by $w_s/(1-\alpha)$, denote the resulting coefficient by $\xi_s$. Stationarity in $v$ requires $1-\sum_s\xi_s=0$. The chain rule then gives

$$
d=\sum_s\xi_s\nabla_xL_s(x^*)=-\sum_s\xi_s\pi_s.
$$

These are precisely the stated tail weights. In the finite LP, the same conditions follow from primal-dual strong duality, including degenerate/atomic tails.

## Proof of CT6

Operational feasibility gives $x+th\in X$ for small $t\ge0$. If the risk constraint is slack, continuity of finite CVaR yields $r_\alpha(x+th)<\kappa$ for all sufficiently small $t>0$. If it binds and $r_\alpha'(x;h)<0$, directional differentiability gives

$$
r_\alpha(x+th)=r_\alpha(x)+t r_\alpha'(x;h)+o(t)<\kappa
$$

for every sufficiently small positive $t$. The third case assumes such a feasible positive step directly. Along any of these feasible displacements,

$$
\mu^\top(x+th)-\mu^\top x=t\mu^\top h>0,
$$

so $x$ cannot be optimal. At an optimizer, existence of a genuinely feasible direction with positive objective derivative would produce the same contradiction. For $h=e_j-e_i$, the direction preserves total acreage and transfers acreage from $i$ to $j$. Merely having $r_\alpha'(x;h)=0$ at a binding constraint is insufficient: for example, a local risk boundary shaped like $r(t)=t^2$ at $t=0$ has zero derivative but excludes every positive step when $\kappa=0$.

## Proof of CT7

Convex order means

$$
E[\varphi(L_{\theta_1}(x))]
\le E[\varphi(L_{\theta_2}(x))]
$$

for every convex $\varphi$ for which the expectations exist. For each fixed $v$, $\varphi_v(z)=(z-v)_+$ is convex, hence

$$
v+\frac{1}{1-\alpha}E[(L_{\theta_1}(x)-v)_+]
\le
v+\frac{1}{1-\alpha}E[(L_{\theta_2}(x)-v)_+].
$$

Taking the infimum over $v$ on both sides proves the CVaR order. Pointwise CVaR order implies that every allocation feasible under $\theta_2$ is feasible under $\theta_1$, so the risk-feasible sets are nested. Maximizing the same objective over a subset cannot increase its value. None of these set/value statements orders the coordinates of an optimizer.

## Proof of CT8

Compactness of each nonempty solution set makes the extrema defining $g_{ij}^{+}$ and $g_{ij}^{-}$ well defined. Since a minimum never exceeds a maximum, $g_{ij}^{-}\le g_{ij}^{+}$ and therefore $\mathcal U_{ij}\subseteq\mathcal P_{ij}$. Any selected optimizer has a gap between those extrema, which proves the two selection inclusions.

The definitions impose no connectedness or monotonicity in $\theta$, so the regions and their boundaries may have any of the listed forms. If the optimizer is unique and continuous, its gap is continuous; a sign change gives a zero by the intermediate value theorem. Strict monotonicity permits at most one zero, and endpoint crossing supplies at least one.

## Proof of CT9 and counterexamples to stronger implications

CT9 is a definition and therefore has no optimizer implication. To disprove such an implication, take crop profits

$$
(10,11,9,10)\quad\text{and}\quad(-100,-101,-99,-100).
$$

Their sample correlation is $-1$, yet with loose risk and no minimum for crop 2, every expected-profit optimizer excludes crop 2. Conversely, profits

$$
(1,2,3,4)\quad\text{and}\quad(10,11,12,13)
$$

are perfectly comoving, yet a loose-risk optimizer selects crop 2. Dependence diagnostics therefore imply neither inclusion nor exclusion.

## Proof of CT10

For any fixed $x\in X(\phi)$,

$$
\max_{y\in X(\phi)}m_Z(y)\ge m_Z(x).
$$

Taking expectations and then maximizing the right-hand side over fixed $x$ gives $I(\phi)\ge U(\phi)$.

If $x^c$ is posterior-optimal almost surely, then

$$
I(\phi)=E[m_Z(x^c)]=E[\Pi(x^c,\omega)].
$$

Integrating the posterior optimality inequalities shows that $x^c$ weakly dominates every fixed action ex ante, so it also attains $U(\phi)$ and VOI is zero.

If $X(\phi_1)\subseteq X(\phi_2)$, each posterior maximum weakly increases, so $I(\phi_1)\le I(\phi_2)$. The ex-ante maximum also weakly increases, so $U(\phi_1)\le U(\phi_2)$.

The difference of two nondecreasing functions need not be nondecreasing. For a zero-value witness, let the same action be best under every posterior and let flexibility add only dominated actions; then VOI remains zero, contradicting strict positivity. Flexibility can also introduce a common robust action and reduce the gain from conditioning. Thus no general monotonicity or strict complementarity of VOI follows.

## Counterexample to an acreage-ordering KKT theorem

Maximize $2x_1+x_2$ subject to

$$
0\le x_1\le0.2,\qquad 0.8\le x_2\le1,\qquad x_1+x_2\le1.
$$

The unique optimizer is $(0.2,0.8)$. Crop 1 has the larger objective margin but less acreage because bound normals determine the levels. Thus marginal stationarity cannot be converted into a general if-and-only-if acreage-ordering rule.

## Counterexample from multiple optima

Maximize $x_1+x_2$ on $x_1+x_2\le1$, $x\ge0$. Every point of the optimal segment has objective one. If $s_1>s_2$, $(0,1)$ reverses, $(1,0)$ does not, and $(1/2,1/2)$ ties. A binary reversal theorem without an optimal-set or selection qualifier is not well defined.

## Counterexample to scalar-tail-coefficient identification

For bivariate standard-normal profits with Gaussian copula correlation $\rho\in(-1,1)$, the classical lower-tail coefficient is zero for every nonsingular $\rho$. Yet the variance of the equal-weight sum is $2+2\rho$, and normal CVaR is proportional to its standard deviation. Identical $\lambda_L$ values therefore produce different portfolio CVaR values.
