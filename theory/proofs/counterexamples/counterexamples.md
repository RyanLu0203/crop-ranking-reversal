# Counterexamples to general claims

## CE1. KKT margin does not order acreage

Maximize $2x_1+x_2$ subject to $0\le x_1\le0.2$, $0.8\le x_2\le1$, and $x_1+x_2\le1$. The unique optimum is $(0.2,0.8)$: crop 1 has higher objective margin but less acreage. Bound normals, not a pairwise CVaR-gap inequality, determine the levels. This also exhibits feasibility-forced reversal.

## CE2. Multiple optima make reversal selection-dependent

Maximize $x_1+x_2$ subject to $x_1+x_2\le1$, $x\ge0$. Every point on the segment $x_1+x_2=1$ is optimal. For $s_1>s_2$, $(0,1)$ reverses, $(1,0)$ does not, and $(0.5,0.5)$ ties. There is no optimizer-independent binary conclusion.

## CE3. Lower-tail coefficient does not identify CVaR

Take bivariate standard-normal per-acre profits with Gaussian copula correlation $\rho\in(-1,1)$. Every nonsingular Gaussian copula has asymptotic lower-tail coefficient zero. For allocation $(1,1)$, however, portfolio standard deviation is $\sqrt{2+2\rho}$; normal expected shortfall is proportional to that standard deviation. Thus identical $\lambda_L=0$ produces different CVaR.

## CE4. A unique threshold need not exist

If the CVaR limit is slack for every dependence parameter, the expected-profit optimizer is constant and no threshold exists. If two crops have identical objective/constraint columns over an interval, both rankings can occur on the optimal face throughout that interval. Parametric LP active-set changes can also produce repeated crossings when the relevant risk coefficients are nonmonotone. Existence, point uniqueness, and monotone direction therefore require separate hypotheses.

## CE5. Pseudo-diversification implications fail both ways

Let crop 2 be perfectly negatively correlated with crop 1 but have profit near $-100$ in every state while crop 1 has profit near $10$. With no minimum crop-2 acreage, the expected-profit/loose-CVaR optimum excludes crop 2 despite negative Pearson correlation. Conversely, two perfectly comoving crops can have tail dependence one, yet a crop with uniformly ten units higher profit is selected under a loose risk limit. Correlation/tail labels alone determine neither inclusion nor exclusion.

## CE6. Strict information-flexibility complementarity fails

Let every signal posterior rank action $a$ above all alternatives. Add flexibility only by making dominated action $b$ feasible. Both informed and uninformed decision makers choose $a$; information value and its change with flexibility are zero, contradicting strict positivity. More generally, added flexibility can create a common robust action and reduce the usefulness of conditioning on the signal.
