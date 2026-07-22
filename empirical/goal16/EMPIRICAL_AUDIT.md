# GOAL-16 empirical extension audit

## Decision

The pre-specified state panel was reconstructed for 2016--2024. It contains
744 complete state--crop--year rows, 248 complete state--years and 31 states.
The unit is published planted acreage and state yield for corn, soybeans and
winter wheat. National USDA ERS price and cost series and the registered BLS
CPI-U vintage are accounting inputs; they are not local realized margins.

The 2025 NASS and ERS series were audited but excluded because a complete
12-month 2025 CPI-U value matching the frozen annual real-dollar construction
was unavailable at the freeze. This is a design-based exclusion, not a
result-based exclusion. County reconstruction was not attempted because no
Quick Stats API key was present and the credential-free official all-crops bulk
snapshot was a 1.05-GB untargeted extract. The repository makes no county claim.

## Source and parser checks

- USDA NASS Crop Production annual summaries supply state and national planted
  acreage and yield. Non-overlapping three-year report blocks cover 2016--2018,
  2019--2021 and 2022--2024.
- The new parser reproduces every state, year, crop, acreage and yield value in
  the frozen 2022--2024 Stage II table exactly.
- Raw report checksums, URLs and retrieval timestamps are emitted to
  `outputs/raw_source_checksums.csv` and `outputs/retrieval_log.csv`.
- Missing and suppressed values are not imputed. A state--year is retained only
  when all three registered crops have acreage and yield.

## Estimands and uncertainty

All four ranking definitions were frozen before extended results were viewed.
Concurrent summaries use Kendall's tau-b, Spearman correlation when defined,
pairwise inversion intensity and top-rank disagreement. Uncertainty uses 5,000
state-cluster bootstrap draws. Temporal specifications use only prior-year score
rank/top status and prior acreage share with crop, year and state fixed effects.
They are descriptive associations, not causal estimates.

Across definitions, the mean inversion intensity ranges from 0.296 for
standardized revenue to 0.704 for relative yield. The primary temporal 95%
bootstrap intervals all include zero. These results support descriptive
rank--allocation disagreement and uncertainty, not a claim that public data
identify farm objectives, constraints, beliefs, mechanisms or optimal acreage.

## Reproducibility controls

`scripts/run_goal16_empirical.py` produces all tidy tables, generated-number
registries, lineage, source records, validation metadata and output checksums.
The acceptance test requires two isolated runs to be byte-identical. Tests also
enforce parser equivalence, complete three-crop support, share accounting,
bounded rank statistics, tie behavior, strictly lagged timing and complete
bootstrap output.
