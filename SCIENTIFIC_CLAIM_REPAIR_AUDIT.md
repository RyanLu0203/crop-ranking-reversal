# Scientific claim repair audit — Issue #36

## Baseline and scope

- Scientific baseline: `12fe6b4a3717ef5602b3d31558fd66424287f7d4`.
- Repair branch: `codex/issue-36-scientific-claim-repair`.
- The immutable supervisor Draft was not edited.
- Supervisor TeX SHA-256:
  `e8885aa89be6a6010f0d3e6f8e40b4b8192a91fc90f6ca4fb16ae9b0aa9dd26c`.
- Supervisor PDF SHA-256:
  `52ac1b4ef21c8d406fd6d722c877935a24d2cc6ea68520a6f35470ba8b334b44`.

This is a focused repair. The Issue #34 model, official-data pipeline,
manuscript architecture, reproducibility system and approved palette remain
the scientific frame.

## Repaired taxonomy

- Pairwise: \(s_i>s_j,\ x_i<x_j\).
- Complete rank reversal: the top-score crop receives less than every
  lower-score crop.
- Strong: the supervisor-Draft exclusion definition
  \(s_i>s_j,\ x_i=0<x_j\).
- Possible, universal and selected refer respectively to some point, every
  point and the deterministic selected point on the optimal face.

The primary ordering and zero tolerances are both \(10^{-4}\) normalized land
share. Sensitivity spans \(10^{-8},10^{-6},10^{-4},10^{-3},10^{-2}\).

## Recomputed classifications

All 165 cells are feasible. Selected pairwise reversal occurs in 143 cells,
selected complete rank reversal in 96 and selected true strong reversal in
zero. Optimal-face audits give 143 possible and 143 universal pairwise cells,
96 possible and 96 universal complete cells, and zero possible or universal
strong cells. Two cells contain multiple optima.

At tolerances through \(10^{-3}\), the selected phase counts remain 143
pairwise, 96 complete and zero strong. At \(10^{-2}\), they are 140, 93 and
zero. The primary Kansas allocation is Corn 0.330265, Soybean 0.421904 and
Winter Wheat 0.247831: a selected complete rank reversal, never an exclusion.

## Claim disposition

- Kansas risk-causation claim: rejected. The expected-profit endpoint is
  already inverted; CVaR raises winter-wheat acreage and moderates the result.
- Margin mechanism: retained and relabelled accurately.
- Risk mechanism: supported only by the separate registered controlled path.
- Operational mechanism: supported only by the fixed-law controlled
  rotation-cap path; null constraint-addition stages are retained.
- Diversification failure: supported by the repaired explicit inequalities.
- Shared-CVaR strict-complementarity theorem: not claimed. The theorem is
  restricted and the complete model reports numerical cross-differences.
- 62/64 interval: renamed exact Clopper--Pearson, not percentile bootstrap.

The repaired manuscript is intended for formal supervisor review, not claimed
to be publication-ready.
