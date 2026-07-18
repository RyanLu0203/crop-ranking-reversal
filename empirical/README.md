# Empirical analysis

The canonical Issue #7 design is frozen in `configs/empirical_design.yaml`. The analysis parses planted acreage and yield for corn, soybeans, and winter wheat directly from the governed NASS 2024 Crop Production Summary, restricts to complete state-years in 2022–2024, and joins only national ERS price/cost and BLS deflator inputs for clearly labeled accounting standardizations.

Run `python scripts/run_empirical_analysis.py` to rebuild the 81-row national panel, parse the 345-row NASS table extract, create the 231-row complete empirical panel, and regenerate every output/checksum. Run `python scripts/verify_empirical_reproducibility.py` for two isolated byte-level replays and `python scripts/validate_empirical_analysis.py` for schema, lineage, reconciliation, and claim-boundary checks.

Observed planted acreage is never treated as an optimizer output. State standardized margins are not local realized profits, and the data do not identify private constraints, CVaR binding, copula causality, or farm-level mechanisms.
