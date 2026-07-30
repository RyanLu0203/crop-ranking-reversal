# Heuristic-policy projection validation

For a raw heuristic \(x^h\), the principal comparison policy is the unique
Euclidean projection

\[
\widehat x_2^h=\arg\min_{x\in\mathcal X_P}
\tfrac12\lVert x-x^h\rVert_2^2.
\]

The comparison set \(\mathcal X_P\) requires full investment and includes crop
bounds, operating budget, corn rotation, soybean contract, planting-labour and
harvest-equipment constraints. Idle land is not allowed. The loss-CVaR ceiling
does not enter the projection and is evaluated after projection. SLSQP uses
objective tolerance \(10^{-10}\), followed by a feasibility check at
\(10^{-8}\).

The sensitivity rule minimizes unweighted \(L^1\) distance over the same set
with HiGHS. A second linear programme minimizes crop-order weights (1,2,3) on
the \(L^1\)-optimal face within \(10^{-10}\), providing a deterministic
lexicographic selection.

Score-proportional and equal-share policies are already feasible and are
unchanged. Raw winner take all is \((0,0,1)\):

- Euclidean projection: \((0.2,0.2,0.6)\), distance
  \(\sqrt{0.24}=0.489898\), no reversal;
- lexicographic \(L^1\) projection: \((0.3,0.1,0.6)\), distance 0.8,
  soybean--corn pairwise reversal.

Both projected winner policies are operationally feasible and are evaluated
as risk-feasible under the principal comparison law. The benchmark reversal
claim is therefore projection-sensitive and is reported as such.

Evidence:

- `reconstruction/issue34/outputs/heuristic_projection_sensitivity.csv`
- `optimization/src/crop_optimization/benchmark_policies.py`
- `tests/test_issue40_final_consistency.py`
