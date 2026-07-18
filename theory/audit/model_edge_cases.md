# Model edge cases

1. **Infeasible lower bounds:** $\mathbf1^T\ell>A$, $c^T\ell>B$, a rotation row violated by $\ell$, or minimum achievable CVaR above $\kappa$.
2. **Unused land:** all positive expansions violate CVaR/budget/rotation, or remaining crops have nonpositive marginal expected profit.
3. **Multiple optima:** identical mean profits or an objective parallel to an active face; reversal can be possible but not universal.
4. **VaR atoms:** finite scenarios make the tail boundary nonunique; conditional-tail derivative shorthand can disagree with correct fractional tail weighting.
5. **Negative CVaR:** a portfolio profitable even in its worst tail has negative loss CVaR; this is not an error.
6. **Zero tail coefficient:** Gaussian copulas with different correlations share $\lambda_L=0$ but imply different portfolio risks.
7. **Constraint-forced reversal:** $u_i<\ell_j$ makes $x_i<x_j$ for every feasible point independent of CVaR.
8. **Tie scores:** $s_i=s_j$ supplies no strict ranking and must not be counted as a reversal.
9. **Threshold interval:** an optimal face can contain both rankings over a parameter range.
10. **No threshold:** CVaR may remain slack, or one crop may dominate for the full dependence domain.
11. **Multiple crossings:** family/path choices and active-set changes can alternate the selected allocation ranking.
12. **Information without actionability:** posterior beliefs differ but a common action remains optimal, giving zero operational value.
13. **Flexibility without strict value:** nested sets can add only dominated actions, so value is flat.
14. **Information and flexibility as substitutes:** flexibility can make a robust action optimal in every signal state, reducing rather than increasing information value.
15. **Pseudo-diversifier extremes:** low correlation cannot rescue very poor mean profit; high tail dependence cannot exclude an otherwise dominant crop under a loose risk limit.
