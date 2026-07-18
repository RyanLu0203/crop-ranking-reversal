# Dependence-model specification

Let $F_i$ denote marginal profit distributions. A copula $C_\vartheta$ creates the joint distribution

\[
F_\vartheta(z_1,\ldots,z_n)=C_\vartheta(F_1(z_1),\ldots,F_n(z_n)).
\]

For $n>2$, $C_\vartheta$ must be a valid $n$-copula. Pairwise lower-tail coefficients may be stored as a matrix, but they need not determine the multivariate copula or simultaneous crop-loss tail. There is no canonical single multivariate $\lambda_L$ in this audit; any proposed aggregation must be defined and validated separately.

The audit separates three objects that the teacher draft conflates:

1. a family parameter $\vartheta$;
2. an ordering of entire copulas (for example lower-orthant order);
3. a scalar lower-tail coefficient $\lambda_L=\lim_{u\downarrow0}C(u,u)/u$, when the limit exists.

The scalar $\lambda_L$ does not identify a copula and does not order all conditional tail expectations. In particular, all nonsingular Gaussian copulas have asymptotic lower-tail coefficient zero while portfolio tail risks vary with correlation. Therefore no global monotonicity of marginal CVaR, acreage, or ranking reversal follows from $\lambda_L$ alone.

A permissible dependence comparative static must specify: fixed marginals; named copula family; parameter domain; mapping $\vartheta\mapsto\lambda_L$; which whole-distribution order, if any, is proved; continuity; and whether the CVaR active set and optimizer are unique. Otherwise label the response `NUMERICAL_CONJECTURE_ONLY`.

For future simulation, compare Gaussian, Student-t, Clayton, Gumbel/survival variants only after documenting which profit tail corresponds to joint loss. Include Kendall's tau or another concordance control alongside $\lambda_L$, because dependence parameters are not comparable across families by raw scale.

Verified open full text used for the ordering caution: Ansari and Rockel (2024), *Dependence properties of bivariate copula families*, DOI `10.1515/demo-2024-0002`. The paper shows that useful monotonicity statements require a stated order and family-specific conditions.
