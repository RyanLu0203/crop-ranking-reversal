# Issue #7 acceptance report

## Outcome

PASS. The empirical design was frozen before results; official raw snapshots rebuild deterministically; every output is lineage- and checksum-governed; definition sensitivity and the national null are retained; and mechanism/causal boundaries are explicit.

## Acceptance evidence

- Raw NASS table parser: 345 rows; complete sample: 231 crop rows, 77 state-years, 26 states.
- Exact NASS reconciliation for the 2024 U.S. corn, soybean, and winter-wheat acreage/yield totals.
- Four preregistered ranking definitions, 308 state-year-definition results, 924 crop ranking rows, 12 leave-one-year-out rows, and exact six-permutation benchmark.
- Operating-margin top/strong discordance: 63/77 and 41/77; national rank discordance: 0/9 crop-years.
- Leakage-free 2024 check: 22/25 top discordances, labeled low-powered.
- Two isolated raw-to-analysis runs: 19/19 files byte-identical.
- Empirical validator: 60/60 checks; full repository suite passes 109 tests before the final canonical-manifest rebuild.

## Boundaries

Observed acreage is not an optimum. National-input standardized margins are not state realized profit. Private feasibility, CVaR binding, copula causality, data-vintage robustness, state downside risk, and farm/county inference are not identified. All inherited Draft counts are superseded by the canonical outputs.

## Reproduction

```bash
python scripts/run_empirical_analysis.py
python scripts/verify_empirical_reproducibility.py
python scripts/validate_empirical_analysis.py
```
