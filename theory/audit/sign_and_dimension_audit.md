# Sign and dimension audit

| Item | Teacher form | Finding | Canonical repair |
|---|---|---|---|
| Portfolio loss | implicit | CVaR alternates between profit and loss conventions | Define $L=-\Pi$ once |
| Continuous CVaR | negative upper profit quantiles | Wrong tail: rewards best profits | Negative average of lower $1-\alpha$ profit tail, or RU loss formula |
| Scenario excess | $-\pi_s^Tx-v\le q_s$ | Correct for $q_s\ge L_s-v$ | Retain and connect to loss definition |
| Marginal CVaR | cutoff $F_\Pi^{-1}(\alpha)$ | Wrong cutoff for loss confidence | cutoff $F_\Pi^{-1}(1-\alpha)$; subgradient at atoms |
| KKT objective | maximize expected profit | Teacher signs are not tied to a canonical Lagrangian | Minimize $-\mu^Tx$ and use $0\in-\mu+$ constraint normals |
| Bound multipliers | $-\delta_i+\nu_i$ | Bound identity/sign not declared | $+u_i^+-u_i^-$ for upper/lower inequalities |
| Shared constraints | absent | Budget and rotation terms missing | Add $\beta c+H^T\eta$ |
| Suitability | $s_i=\mu_i$ | Score units and currency/acre are incompatible | Require only identical rank ordering |
| Profit | $p_i y_i-c_i$ | Consistent if price and yield units match | Store units and dollar base year |
| Expected objective | $x_i\mu_i$ | currency | Retain |
| CVaR limit | $\kappa$ | must be currency; can be negative | Record sign convention and units |
| Tail coefficient | $\lambda_L$ | dimensionless; confused visually with KKT multiplier $\lambda$ | Always use subscript L for dependence |
| Rotation | $\rho A$ | acres if $\rho$ dimensionless | Retain; specify crop group rows |
| VOI | expected max minus random profit expression | RHS terms do not share expectation/timing | Use outer expectation in both values |

Numerical validation must fail on nonfinite values, $\alpha\notin(0,1)$, scenario weights not summing to one, incompatible monetary bases, and any report that labels profit-tail averages as loss CVaR.
