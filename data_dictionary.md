# Issue #34 data dictionary with Issue #36 scientific repair

## Evidence classes

- `OFFICIAL_DATA_CALIBRATED_STRUCTURAL_STRESS_TEST`: official aggregate inputs
  calibrate a controlled decision model; the model is not a farm-level estimate.
- `AGGREGATE_DESCRIPTIVE_NOT_CVAR_CAUSALITY`: state observations describe
  score--acreage disagreement and do not identify the model mechanism.
- `REGISTERED_STRESS_PATH_NOT_FARM_LEVEL_ESTIMATE`: a dependence or constraint
  value is a pre-specified sensitivity path.
- `REGISTERED_CONTROLLED_STRUCTURAL_STRESS_TEST`: a mean-preserving downside
  path isolates risk while retaining the official score and mean-margin order.
- `REGISTERED_CONTROLLED_OPERATIONAL_STRESS_TEST`: a fixed-law constraint path
  isolates operational displacement; it is not an observed private constraint.

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
| `selected_pairwise_reversal` | Boolean | Some pair with \(s_i>s_j\) has \(x_i<x_j\) at the selected optimum |
| `selected_complete_rank_reversal` | Boolean | The top-score crop receives less than every lower-score crop at the selected optimum |
| `selected_strong_reversal` | Boolean | Supervisor-Draft exclusion: some \(s_i>s_j\) has \(x_i=0<x_j\) within the registered zero tolerance |
| `possible_*` / `universal_*` | Boolean | Repaired reversal property holds at some / every point on the objective-equivalent optimal face |
| `multiple_optima` | Boolean | At least one crop coordinate has a non-degenerate optimal-face range at tolerance |
| `value_of_information` | 2024 US$/acre | Optimized informed value minus no-information value |
| `flexibility_level` | [0,1] | Adjustable acreage or state-shock buffering share |
| `signal_accuracy` | [0.5,1] | Probability the binary signal reports the realized state |
| `discrete_cross_difference` | 2024 US$/acre | Adjacent-grid \([V(q_2,\phi_2)-V(q_1,\phi_2)]-[V(q_2,\phi_1)-V(q_1,\phi_1)]\) |
| `cross_difference_classification` | category | Positive, negative, zero/boundary, or zero information |
| `exact_binomial_95_low/high` | proportion | Exact Clopper--Pearson interval for a binary frequency across registered resamples |
| `percentile_95_low/high` | output unit | Historical-resample percentile interval for a continuous output only |
| `benchmark_gaussian_variance` | (2024 US$/acre)\(^2\) | Gaussian variance of the declared \(x^0\), not the maximum across candidates |
| `strong_diversification_failure_identified` | Boolean | Variance reduction, material allocation difference, worse true-law CVaR and true-law ceiling violation all pass |
| `top_rank_reversal_rate` | proportion | State-years where score and acreage leaders differ |

## Sample sizes

- Kansas calibration: 24 crop-years, 8 years, 3 crops.
- Primary optimization: 512 scenarios; scenarios are not empirical observations.
- Phase diagram: 165 deterministic model cells.
- Historical uncertainty: 64 bootstrap replications.
- Risk-isolation path: 4,096 structural scenarios and 9 registered risk ceilings.
- Operational path: 4,096 fixed structural scenarios, 7 constraint-addition
  stages and 12 rotation-cap levels.
- External panel: 744 crop-state-years = 248 complete state-years in 31 states.
- Leakage-free transition model: 651 crop-transition rows.
