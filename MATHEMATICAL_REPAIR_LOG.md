# Mathematical repair log

| Original problem | Why invalid or incomplete | Repair | Verification |
|---|---|---|---|
| Undefined “risk-adjusted margin gap” used as an iff acreage condition | A marginal value does not determine acreage without feasible geometry and uniqueness | Two-crop theorem: reversal iff the right endpoint of the risk-feasible share interval lies below one-half | `theory/issue34/proofs.md`; executable theory tests |
| KKT omitted operational rows and finite-scenario auxiliary variables | Missing multipliers can misattribute stationarity residuals to risk | Full KKT for land, budget, rotation, contracts, shared capacity, bounds, VaR and excess variables | solver residuals and `tests/test_kkt_oracles.py` |
| Scalar lower-tail dependence globally ordered portfolio CVaR and crop shares | A scalar coefficient is not a cross-family stochastic order | Named-family convex-order proposition and family-specific phase diagram | 165-cell registered experiment |
| Universal unique dependence threshold | Continuity, strict monotonicity and crossing were not stated | Unique threshold only under explicit conditions; otherwise report the reversal set, including disconnected regions | Clayton \(\tau=0.30\) disconnected witness |
| Complete top-crop inversion labelled “strong reversal” | The supervisor Draft defines strong reversal by exclusion: \(s_i>s_j,\ x_i=0<x_j\) | Separate selected pairwise, complete and exclusion-based strong reversal, with near-zero and acreage-order tolerances | principal case is complete but not strong; all 165 strong counts are zero |
| Pseudo-diversification proposition | The implementation did not declare its Gaussian benchmark, did not verify strict variance reduction and mixed benchmark and true-law risk | Full-investment Gaussian mean--variance benchmark; explicit \(x_0,x_{\rm MV},x_T\); strict variance reduction, allocation separation and true-law CVaR ceiling failure | \(6765.624>5579.213\), \(\lVert x_{\rm MV}-x_T\rVert_1=0.0537\), and \(-44.368>-45.733\) under the true law |
| Unconditional strict information--flexibility complementarity | The theorem and numerical model did not share a defensible universal ordering, and information can be worthless or substitute for flexibility | Restrict the theorem to its stated deterministic feasible-set assumptions; classify a separate shared ex-ante-CVaR experiment by discrete cross-differences | 72 cells: 32 positive, 17 negative, 18 zero-information and 5 zero/boundary |
| One solver point treated as the optimum | Multiple optima can change a pairwise or exclusion classification | Possible, universal and selected pairwise/complete/strong reversal plus deterministic selection and full face audit | two multiple-optimum phase cells retained |

The rebuilt theory does not claim monotonic crop shares under feasible-set
contraction and does not use a stationarity equation as a global acreage
decomposition.
