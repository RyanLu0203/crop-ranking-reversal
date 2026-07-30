# Experiment reliability audit

## Design control

- Frozen design:
  `simulation/configs/issue34_full_model_design.yaml`
- Design SHA-256:
  `23b19bacf6c38b6765865357e3b8b8876b947df31ac8a5e3b7576ebc62924173`
- The Issue #34 design was frozen before its results were inspected. Issue
  #36 records a narrow repair overlay for definitions, mechanism controls,
  benchmark specification and exact uncertainty; it does not relabel that
  overlay as prospective preregistration.
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
- Reversal classification: selected complete top-crop inversion, not
  exclusion-based strong reversal.

## Mechanism-isolation certificates

- Margin: the primary Kansas inversion is margin-induced because the
  first-ranked wheat mean margin is below both lower-ranked crops.
- Risk: a registered mean-preserving soybean downside-shock path preserves
  \(s_{\rm soy}>s_{\rm corn}\) and
  \(\mu_{\rm soy}>\mu_{\rm corn}\), and crosses to
  \(x_{\rm soy}=0.180654<x_{\rm corn}=0.219346\) at zero dependence.
- Operations: the registered full constraint sequence has no soybean--corn
  crossing.  Holding the scenario law and CVaR ceiling fixed, the controlled
  soybean rotation-cap path first crosses at cap \(0.35\).
- Diversification: the declared Gaussian policy strictly reduces variance
  from 6765.624 to 5579.213, differs from the true-law policy by L1 distance
  0.0537 and violates the true-law CVaR ceiling
  (\(-44.368>-45.733\)).

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

The complete suite passes 159 tests. Registered output checksums verify, both
TeX documents compile, and all 27 PDF pages were rendered and visually
inspected.  Every legacy repository validator passes; the canonical manifest
contains 970 assets and its checksum ledger 971 entries, with zero failures.
A forced second build reproduced byte-identical main and supplementary PDFs,
all figure and visual-QA exports, manifests and release archive.  The
deterministic release contains 179 files and its adjacent SHA-256 verifies.
