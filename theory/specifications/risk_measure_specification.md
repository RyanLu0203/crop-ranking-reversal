# Risk-measure specification

The canonical random variable is loss $L=-\Pi$; larger values are worse. For confidence $\alpha\in(0,1)$,

\[
\operatorname{VaR}_\alpha(L)=\inf\{z:P(L\le z)\ge\alpha\},
\]

and the general-distribution CVaR/expected-shortfall representation used for optimization is

\[
\operatorname{CVaR}_\alpha(L)=\min_{v\in\mathbb R}\left(v+\frac{1}{1-\alpha}E[(L-v)_+]\right).
\]

This is the authoritative operational definition for this project. It remains valid for discrete scenario distributions, where quantile-integral and conditional-expectation shorthand require care at atoms.

For continuous portfolio profit, the equivalent lower-profit-tail expression is

\[
-\frac{1}{1-\alpha}\int_0^{1-\alpha}F_\Pi^{-1}(u)\,du.
\]

The teacher draft instead negates the integral over $u\in[\alpha,1]$, which selects high profits and is sign/tail inconsistent.

If $P(L=\operatorname{VaR}_\alpha(L))=0$ and regularity permits differentiation, a marginal component can be written

\[
d_i=-E[\pi_i\mid \Pi\le F_\Pi^{-1}(1-\alpha)].
\]

At atoms, ties, or basis changes, use a CVaR subgradient or the finite-LP dual weights; do not report a unique derivative.

Unit: currency per acre for $\pi_i,d_i$; currency for portfolio CVaR and $\kappa$. Increasing an allocation by one acre changes CVaR by approximately $d_i$ currency, when differentiable.

Primary sources verified from full author text: Rockafellar and Uryasev (2000), `https://sites.math.washington.edu/~rtr/papers/rtr179-CVaR1.pdf`; Rockafellar and Uryasev (2002), `https://sites.math.washington.edu/~rtr/papers/rtr187-CVaR2.pdf`.
