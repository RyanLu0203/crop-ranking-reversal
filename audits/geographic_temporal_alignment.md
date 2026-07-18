# Geographic and temporal alignment audit

## Geographic alignment

| Layer | Published geography | Canonical role | Alignment decision | Residual risk |
|---|---|---|---|---|
| ERS costs and returns | U.S. total plus Farm Resource Regions | panel backbone | select U.S. total only | national averages do not represent individual farms |
| NOAA Climate at a Glance | contiguous United States | contextual covariates | join by year to every crop | excludes Alaska/Hawaii and is not acreage-weighted or crop-specific |
| BLS CPI-U | U.S. city average | monetary normalization | use national annual mean only | consumer prices differ from farm-input inflation |
| NASS annual summary | U.S. and states | external acreage benchmark | no panel join | only a 2023--2024 release and estimates are revisable |
| NRCS NCCPI | soil component/map unit | future spatial extension | not joined | national aggregation would require explicit area weights and irrigation treatment |

No regional series is downscaled to a state or county. No state/county observation is upscaled and presented as a farm. The Teacher Draft's Iowa geography is not adopted.

## Temporal alignment

The final key is the published integer year. ERS accounts follow annual commodity cost/return reporting; NOAA fields are January--December climate summaries; CPI-U is averaged over twelve calendar months. Same-year joining is therefore a transparent descriptive alignment, not proof that calendar weather causes the published ERS account. Issue #6 must not make causal or crop-exposure claims from these national covariates.

ERS survey-base regimes change within the panel:

- Corn: 1996 base for 1998--2000; 2001 for 2001--2004; 2005 for 2005--2009; 2010 for 2010--2015; 2016 for 2016--2020; 2021 for 2021--2024.
- Soybeans: 1997 base for 1998--2001; 2002 for 2002--2005; 2006 for 2006--2011; 2012 for 2012--2017; 2018 for 2018--2022; 2023 for 2023--2024.
- Wheat: 1998 base for 1998--2003; 2004 for 2004--2008; 2009 for 2009--2016; 2017 for 2017--2021; 2022 for 2022--2024.

These regimes are retained row-by-row. Later modeling must test regime indicators or split-window sensitivity; it may not treat all 27 observations as identically measured without qualification.

## Frozen exclusions

- 2025 ERS estimates and all 2026--2027 forecasts.
- ERS regional rows, because common regional availability differs by crop.
- Farm-specific constraints, because no selected aggregate source observes them.
- Soil/NCCPI joins, because spatial weighting is outside the first national panel.
