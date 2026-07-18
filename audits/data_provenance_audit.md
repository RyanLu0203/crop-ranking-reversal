# Official-data provenance audit

## Admission result

Issue #4 admits nine immutable raw snapshots from four federal statistical agencies into the repository and registers one additional NRCS spatial source for a future extension. The canonical processor produces 81 complete crop-year rows for three crops over 1998--2024. Raw bytes, request methods and POST bodies, access time, release context, checksums, units, missing codes, revision policies, and access conditions are recorded in `data/raw_manifest.csv` and `evidence_registry/data_source_registry.csv`.

The source chain is:

1. USDA ERS recent Commodity Costs and Returns CSVs for national crop yield, harvest price, costs, representative enterprise size, and practice shares.
2. NOAA NCEI Climate at a Glance CSVs for national annual precipitation and temperature context.
3. BLS CPI-U API snapshots for a transparent 2024-dollar normalization.
4. USDA NASS Crop Production 2024 Summary as a separate official acreage benchmark.
5. USDA NRCS NCCPI v3 registered, but excluded from the national panel because it is spatial and nonirrigated.

## Selection and noninheritance

The crop set and period follow a source-compatibility rule, not the Teacher Draft. The Draft's Iowa setting and its area, budget, price, cost, risk-threshold, and farmer-constraint values remain inadmissible. The panel uses no hand-entered observations and no manual raw/processed CSV edits. Its only constructed outcome is the scripted price-times-yield-minus-operating-cost margin.

## Immutable snapshot control

`scripts/download_official_data.py` verifies canonical bytes locally. Network requests require an explicit staging directory outside `data/raw`. Endpoint drift returns a review-required status; canonical files are never overwritten. Because agency endpoints may revise historical data and BLS responses include request metadata, a changed live hash is evidence of a new release or response—not permission to replace the frozen evidence silently.

## Parameter audit

The governed empirical parameters are the crop universe, 1998--2024 window, and 2024 CPI base. A land budget of one is only a share normalization. CVaR confidence, loss limit, scenario count, seed, marginal family, dependence family, and farmer-specific constraints are not officially observed. They are marked `ILLUSTRATIVE_ONLY` or `DATA_DERIVED_PENDING_ISSUE_5`; Issue #5 must freeze and sensitivity-test them before any numerical claim is admissible.

## Known risks

- ERS accounts are national/regional sector averages derived from periodic ARMS base surveys and annual updating; non-survey-year reliability depends on technical and structural change.
- NOAA CONUS annual climate is not crop-area weighted and cannot identify farm-level weather response.
- CPI-U is a general consumer-price normalization, not a farm-input cost index.
- NASS summary estimates may be revised and are not a long-window panel here.
- National aggregation prevents a valid NCCPI merge without new spatial work.
- A 27-year annual sample limits tail estimation; Issue #5 must use finite-sample diagnostics, uncertainty intervals, and restrained claims.

## Prohibited claims

The repository may not describe any selected row as a representative farmer's realized profit, identify the national weather series as a crop-specific shock, call CPI-U a farm-cost index, or state that a CVaR limit or crop bound is empirically observed. It may not report a national aggregate as Iowa/county evidence.
