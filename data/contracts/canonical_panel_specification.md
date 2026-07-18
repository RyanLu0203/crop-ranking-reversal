# Canonical processed-panel specification

## Frozen scope

- Unit: crop × year.
- Crops: corn, soybeans, wheat.
- Geography: USDA ERS `U.S. total`.
- Window: 1998--2024 inclusive (27 years; 81 rows).
- Monetary base: 2024 dollars using the annual mean of monthly BLS CPI-U series `CUUR0000SA0`.
- Backbone: USDA ERS Commodity Costs and Returns recent-series files released 1 May 2026.

This scope is selected by a reproducible coverage rule: the intersection of complete recent-series national records for the three major field crops that have a common bushel yield/price unit and ERS cost accounts. Wheat's 1998 start fixes the common beginning. The last complete observed year, 2024, fixes the end; ERS 2025 estimates and all forecasts are excluded. No Iowa, county, area, price, cost, budget, or threshold value is inherited from the Teacher Draft.

## Deterministic transformations

For each crop-year, the script selects exactly one `U.S. total` record for yield, harvest price, total operating cost, total listed cost, representative enterprise size, dryland share, and irrigated share. Whitespace in ERS item labels is stripped, but published values are not edited.

The primary nominal margin is

`harvest price × yield − total operating cost`.

This deliberately excludes ERS secondary-product value from the constructed margin. The 2024-real factor is `annual CPI-U in 2024 / annual CPI-U in year t`. Monthly CPI-U must have exactly 12 observations per year. NOAA annual CONUS precipitation and mean temperature are joined by calendar year and repeated across crops; they are contextual national covariates, not crop-specific exposures.

## Join keys and cardinality

| Layer | Key before join | Required cardinality |
|---|---|---|
| ERS crop accounts | crop, year, region, item | one selected value per crop-year-item |
| BLS CPI-U | year, month | twelve months per year |
| NOAA climate | year, parameter | one value per year-parameter |
| Final panel | crop, year | exactly one row |

The NASS 2024 Summary is not joined. It is an external planted/harvested-area benchmark for later reasonableness checks. NCCPI is not joined because it is a spatial, nonirrigated soil interpretation while the canonical panel is national.

## Missingness and exclusions

The frozen panel admits no missing selected value. A missing, duplicate, nonnumeric, or out-of-window record is a hard processing failure. NASS codes `(D)`, `(NA)`, and `(Z)` are documented in the registry; NASS data are not parsed into the canonical panel. The ERS files' regional observations are retained in raw snapshots but excluded from processing.

## Permitted uses

The panel may support descriptive crop-return comparison, marginal fitting, dependence diagnostics, simulation calibration, and sensitivity analysis after Issue #5 freezes the design. It does not identify farm-level causal weather effects, soil effects, farmer preferences, acreage bounds, risk limits, or a representative farm's budget.

## Rebuild

```bash
python scripts/download_official_data.py
python scripts/process_official_data.py
python scripts/validate_official_data.py
```

The first command verifies local raw bytes and performs no network access unless an explicit staging directory is supplied.
