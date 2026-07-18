# Data

Issue #4 establishes the paper's official-data boundary. The canonical empirical input is a U.S.-total crop-year panel for corn, soybeans, and wheat, 1998--2024. It is built from frozen USDA ERS, NOAA NCEI, and BLS snapshots. A frozen USDA NASS annual summary is retained as an external acreage benchmark; USDA NRCS NCCPI is registered only for a future spatial extension.

Canonical raw files are immutable. `python scripts/download_official_data.py` verifies their bytes. Passing `--stage <directory>` downloads current agency responses outside `data/raw/` and reports revision drift; it never overwrites the frozen snapshots. `python scripts/process_official_data.py` rebuilds `data/processed/canonical_crop_year_panel.csv`.

The panel is not farm microdata and supplies no observed farmer-specific bounds, budgets, or CVaR limit. Any such values remain `ILLUSTRATIVE_ONLY` until separately justified.
