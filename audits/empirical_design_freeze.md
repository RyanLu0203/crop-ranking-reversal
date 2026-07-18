# Empirical design freeze

Design `CRR-EMP-FREEZE-2026-07-19` was frozen before the Issue #7 pipeline exposed any ranking-discordance result.

The official NASS snapshot defines the state-year acreage/yield layer for 2022–2024. Admission requires complete planted acreage and yield for corn, soybeans, and winter wheat; there is no imputation. The national ERS/BLS panel contributes same-year national harvest price, operating/total cost, and CPI normalization. Combining state yield with national price/cost is an accounting standardization, never a state profit observation.

Four rankings were preregistered: crop-relative yield, standardized revenue, operating margin, and total-cost margin. Outcomes are three-pair inversion count, normalized inversion distance, top-rank discordance, strong discordance, and accounting value comparisons. Robustness includes ranking definition, cost convention, leave-one-year-out summaries, an exact six-permutation combinatorial reference, and a leakage-free 2024 check using only 2022–2023 relative yields.

Observed acreage is an aggregate outcome. Private feasibility, optimality, farmer risk limits, CVaR binding, dependence causality, and state downside distributions are outside the identified set.
