# Mathematical repair log

| Original problem | Why invalid or incomplete | Repair | Verification |
|---|---|---|---|
| Undefined “risk-adjusted margin gap” used as an iff acreage condition | A marginal value does not determine acreage without feasible geometry and uniqueness | Two-crop theorem: reversal iff the right endpoint of the risk-feasible share interval lies below one-half | `theory/issue34/proofs.md`; executable theory tests |
| KKT omitted operational rows and finite-scenario auxiliary variables | Missing multipliers can misattribute stationarity residuals to risk | Full KKT for land, budget, rotation, contracts, shared capacity, bounds, VaR and excess variables | solver residuals and `tests/test_kkt_oracles.py` |
| Scalar lower-tail dependence globally ordered portfolio CVaR and crop shares | A scalar coefficient is not a cross-family stochastic order | Named-family convex-order proposition and family-specific phase diagram | 165-cell registered experiment |
| Universal unique dependence threshold | Continuity, strict monotonicity and crossing were not stated | Unique threshold only under explicit conditions; otherwise report the reversal set, including disconnected regions | Clayton \(\tau=0.30\) disconnected witness |
| Pseudo-diversification proposition | Variance, Gaussian dependence, tail risk and allocation were conflated | Executable three-part criterion and strong risk-infeasibility condition | matched-Kendall Student-\(t\) witness |
| Unconditional strict information--flexibility complementarity | Information can be zero or flexibility can substitute for it | Nonnegative/strict/zero theorem; increasing-differences complementarity; shock-buffering substitution | 72-cell agricultural two-stage experiment |
| One solver point treated as the optimum | Multiple optima can change a pairwise ranking | Possible, universal and selected reversal plus deterministic selection and face audit | two multiple-optimum phase cells retained |

The rebuilt theory does not claim monotonic crop shares under feasible-set
contraction and does not use a stationarity equation as a global acreage
decomposition.
