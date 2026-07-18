# Verified results

## V1. Finite-scenario CVaR is an LP

For affine scenario loss $L_s(x)=-\pi_s^Tx$, the RU epigraph has objective/constraint expression $v+(1-\alpha)^{-1}\sum_sw_sq_s$ with linear inequalities $q_s\ge L_s(x)-v$, $q_s\ge0$. Adding linear physical constraints preserves linearity. Thus the finite problem is an LP.

## V2. Ordinal ranking does not identify cardinal allocation

Fix any strict ranking $s_1>s_2$. Both allocations $(A,0)$ and $(0,A)$, and every split between them, are logically compatible with that ranking because the definition imposes no mapping from score levels to acreage. Therefore ranking alone cannot identify acreage.

## V3. Feasibility-forced universal reversal

If $s_i>s_j$ and $\sup_{x\in X}x_i<\inf_{x\in X}x_j$, then $x_i<x_j$ for every feasible $x$, hence for every optimizer. The checkable sufficient condition $u_i<\ell_j$ implies the premise directly.

## V4. Zero operational information value under a common optimal policy

Let $x^c$ be feasible and posterior-optimal for almost every signal $Z=z$. Then

\[
E_Z[\max_xE(\Pi(x)|Z=z)]=E_Z[E(\Pi(x^c)|Z=z)]=E[\Pi(x^c)].
\]

Because $x^c$ is also prior-optimal (integrating the posterior inequalities proves it weakly dominates every constant action), subtracting the prior optimum gives zero.

## V5. Weak value of feasible-set expansion

If $X(\phi_1)\subseteq X(\phi_2)$, then the maximum of the same objective over $X(\phi_2)$ cannot be lower. The inequality need not be strict because added actions can be dominated.

## V6. Loss-tail orientation witness

For profits $(-100,10,20,30)$ with equal probabilities and $\alpha=0.75$, loss CVaR is 100 (the worst loss). Negating the teacher's upper-profit-tail average gives $-30$. Hence the two definitions are not equivalent.

Method foundation: Rockafellar and Uryasev (2000, 2002), full author PDFs verified 2026-07-18.
