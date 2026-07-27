# Experiment reliability audit

## Design control

- Frozen design:
  `simulation/configs/issue34_full_model_design.yaml`
- Design SHA-256:
  `57e0689e388b533c59adc711c16ddfdb54e7df4f8e5ad9c00dbe7406b118c784`
- Design frozen before Issue #34 results were inspected.
- Primary seed: `202607270034`.
- Primary optimization scenarios: 512.
- Historical bootstrap replications: 64.

## Same-model check

Theory and the principal experiment both maximize expected profit subject to a
loss-CVaR ceiling and the full operational set. Pure risk minimization is used
only to construct the minimum-CVaR endpoint.

## Principal numerical certificate

- Allocation: corn 0.330265, soybean 0.421904, winter wheat 0.247831.
- Active set: land and loss-CVaR.
- Expected profit: 198.483846 real 2024 US$/normalized acre.
- Loss-CVaR: -46.985013, equal to the ceiling within tolerance.
- Maximum primal residual: \(1.42\times10^{-14}\).
- Maximum stationarity residual: \(2.84\times10^{-14}\).
- Maximum complementarity residual: \(5.06\times10^{-14}\).

## Reliability layers

1. Every policy is evaluated from scenario-level profit and resource use.
2. Heuristic score policies are repaired to operational feasibility before
   comparison and are labelled as repaired.
3. The optimal face is audited by pairwise minimum and maximum problems.
4. Null, nonmonotone, multiple-optimum and disconnected cells are retained.
5. One-at-a-time robustness covers alpha, constraints, dependence family and
   parameter, marginals, sample window, scenario count, seed and solver.
6. Historical resampling reconstructs the score, margin calibration, scenarios
   and optimization rather than resampling solver outputs.
7. Simulated scenarios are never counted as empirical observations.

## Results that remain conditional

The 165-cell phase diagram and bootstrap intervals are conditional on the
registered Kansas stress design. The eight-year calibration cannot estimate
extreme-tail dependence or private farm risk preferences. The numerical
experiment identifies mechanisms inside the model, not their causal prevalence
among farms.

## Validation

The complete suite passes 151 tests. Registered output checksums verify, both
TeX documents compile, and all 26 PDF pages were rendered and visually
inspected.
