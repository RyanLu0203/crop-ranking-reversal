# Issue #34 data dictionary

## Evidence classes

- `OFFICIAL_DATA_CALIBRATED_STRUCTURAL_STRESS_TEST`: official aggregate inputs
  calibrate a controlled decision model; the model is not a farm-level estimate.
- `AGGREGATE_DESCRIPTIVE_NOT_CVAR_CAUSALITY`: state observations describe
  score--acreage disagreement and do not identify the model mechanism.
- `REGISTERED_STRESS_PATH_NOT_FARM_LEVEL_ESTIMATE`: a dependence or constraint
  value is a pre-specified sensitivity path.

## Core variables

| Variable | Unit | Definition |
|---|---|---|
| `crop` | category | Corn, Soybean or Winter Wheat |
| `year` | calendar year | Source observation year |
| `state` | USPS/state name | State geography |
| `planted_acres` | acres | NASS planted acreage; suppressed values not imputed |
| `yield` | bushels per acre | NASS state or national yield |
| `historical_yield_potential_score` | ratio | Mean Kansas yield / same-year national yield, 2016--2023 |
| `mean_margin_real_2024_usd_per_acre` | 2024 US$/acre | State yield × national price − national operating cost |
| `allocation_<crop>` / `acres_<crop>` | share | Optimized or benchmark share of normalized land |
| `expected_profit` | 2024 US$/normalized acre | Scenario-mean portfolio profit |
| `cvar_loss` | 2024 US$/normalized acre | 95% loss-CVaR; larger is worse |
| `cvar_limit` | same | Registered loss-CVaR ceiling |
| `risk_tolerance` | [0,1] | Interpolation from minimum-CVaR to expected-profit endpoint |
| `kendall_tau` | [-1,1] | Matched rank-dependence parameter |
| `lower_tail_dependence` | [0,1] | Theoretical family-specific coefficient |
| `selected_reversal` | Boolean | Declared selected optimum reverses at least one ranked pair |
| `strong_reversal` | Boolean | Top-ranked crop receives less than every lower-ranked crop |
| `multiple_optima` | Boolean | Optimal-face pairwise range is non-degenerate at tolerance |
| `value_of_information` | 2024 US$/acre | Optimized informed value minus no-information value |
| `flexibility_level` | [0,1] | Adjustable acreage or state-shock buffering share |
| `signal_accuracy` | [0.5,1] | Probability the binary signal reports the realized state |
| `top_rank_reversal_rate` | proportion | State-years where score and acreage leaders differ |

## Sample sizes

- Kansas calibration: 24 crop-years, 8 years, 3 crops.
- Primary optimization: 512 scenarios; scenarios are not empirical observations.
- Phase diagram: 165 deterministic model cells.
- Historical uncertainty: 64 bootstrap replications.
- External panel: 744 crop-state-years = 248 complete state-years in 31 states.
- Leakage-free transition model: 651 crop-transition rows.
