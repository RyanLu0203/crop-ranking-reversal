# Issue #4 acceptance report

## Outcome

PASS. The official-data boundary is frozen, raw snapshots are checksum-pinned and immutable, the canonical panel is reproducible, unsupported farm/risk parameters are quarantined from empirical status, and the repository-wide validation suite passes.

## Acceptance evidence

- Eight source-registry entries: seven frozen data products plus one registered-only NRCS spatial extension.
- Nine immutable raw snapshots totaling 3,486,661 bytes.
- Three USDA ERS crop files with complete U.S.-total values for every selected item in 1998--2024.
- Two NOAA NCEI annual climate files, three BLS CPI-U API snapshots, and one NASS annual-summary benchmark.
- Deterministic 81-row processed panel with no missing selected values and a unique crop-year key.
- Source owner, URL, documentation, access date, release, coverage, observation unit, geography, period, variables, units, missing codes, revision policy, access/reuse note, local path, checksum, status, and limitations recorded.
- Eleven governed parameter rows. All unobserved CVaR, numerical-design, and farmer-constraint quantities are explicitly nonempirical.
- Geographic, temporal, survey-vintage, revision, licensing/access, and claim-boundary audits completed.
- Canonical manifest validation passed with 149 assets and 150 checksum entries; the full suite passed 82 tests.

## Commands

```bash
python scripts/download_official_data.py
python scripts/process_official_data.py
python scripts/validate_official_data.py
pytest tests/test_official_data.py
```

## Hard boundaries carried forward

Issue #5 must freeze simulation choices before numerical claims. Issue #6 must respect the 27-year finite sample, ERS base-survey changes, and national aggregation. No Iowa/county inference, farm-specific constraint, causal weather effect, or empirically observed CVaR threshold is established here.
