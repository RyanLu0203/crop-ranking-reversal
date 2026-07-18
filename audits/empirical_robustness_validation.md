# Empirical robustness and validation report

## Reconciliation and reproducibility

Published 2024 U.S. NASS totals reconcile exactly: corn 90.594 million planted acres and 179.3 bushels/acre; soybeans 87.050 million and 50.7; winter wheat 33.390 million and 51.7. The national ERS/BLS panel rebuilds to 81 rows with zero validation failures. Two isolated complete pipeline runs reproduce all 16 output artifacts and three processed panels byte-for-byte (19 comparisons).

The admitted state sample covers about 72–73% of national corn acres, 78–79% of soybean acres, and 75–77% of winter-wheat acres, depending on year. These are coverage diagnostics, not expansion weights.

## Ranking-definition sensitivity

Top-rank discordance rates are 0.870 (relative yield), 0.623 (standardized revenue), 0.818 (operating margin), and 0.844 (total-cost margin). Strong-discordance rates range from 0.039 for revenue to 0.818 for relative yield. This spread makes the ranking definition a substantive result condition, not a cosmetic robustness choice.

The exact six-permutation reference has 1.5 expected inversions and 2/3 top discordance. It is a combinatorial benchmark only; clustered state-years are not treated as independent draws from a random-permutation null.

## Temporal sensitivity

Operating-margin top discordance is 0.731 in 2022, 0.885 in 2023, and 0.840 in 2024. Leave-one-year-out rates remain between 0.784 and 0.863. Relative-yield, standardized-revenue, and total-cost definitions likewise retain their qualitative definition-specific patterns.

The leakage-free 2024 check uses mean 2022–2023 relative yield and finds 22/25 top discordances. With only two training years, it is a limited validation and not a predictive-performance claim.

## Unavailable robustness

Data-vintage robustness is unavailable because only the frozen January 2025 NASS summary is admitted. Optimizer-selection robustness is not applicable because observed acreage is not modeled as an optimizer output. State price/cost windows, private constraint repair, near-optimal faces, and realized CVaR remain not identified rather than being filled with inherited or fabricated values.
