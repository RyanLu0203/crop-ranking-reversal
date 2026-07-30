# Strong-reversal lower-bound sensitivity

Strong reversal uses the exclusion definition
\(s_i>s_j,\ x_i=0<x_j\). The ordering tolerance and near-zero tolerance are
separate declared numerical quantities.

## Principal specification

The principal crop lower bounds are 0.05, 0.10 and 0.05 for corn, soybean and
winter wheat. Strong exclusion is therefore structurally inadmissible. A zero
principal strong count is a feasibility implication, not an empirical or
computational discovery.

## Admissible-exclusion specifications

Two complete phase reruns retain every other scientific component:

1. all three crop lower bounds equal zero;
2. only the highest-ranked crop, winter wheat, has a zero lower bound.

Each specification resolves all 165 family-by-dependence-by-risk cells and
audits the complete optimal face. Selected, possible and universal pairwise,
complete and strong classifications, multiple optima and infeasibility are
reported at near-zero tolerances \(10^{-8},10^{-6},10^{-4},10^{-3},10^{-2}\).

At the primary \(10^{-4}\) tolerance, both relaxed specifications retain 143
selected/possible/universal pairwise cells, two multiple-optimum cells and no
infeasible cells. The all-zero specification has 95
selected/possible/universal complete cells; the top-crop-zero specification
has 96, matching the principal complete count because the original
winter-wheat lower bound is not active at the affected optima. Selected,
possible and universal strong counts are all zero. No first strong boundary,
excluded crop or active constraint at exclusion exists on the evaluated grid.
This is a genuine conditional null result.

Evidence:

- `reconstruction/issue34/outputs/strong_reversal_lower_bound_phase.csv`
- `reconstruction/issue34/outputs/strong_reversal_lower_bound_summary.csv`
- `figures/issue34/SupplementaryFigure1.*`
- `tests/test_issue40_final_consistency.py`
