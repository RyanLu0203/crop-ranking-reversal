# Source access, citation, and reuse notes

All admitted sources are U.S. federal agency products accessed from `.gov` endpoints. Public access does not remove the obligation to cite the producing agency, preserve release context, and disclose revisions.

- USDA ERS: cite *Commodity Costs and Returns data*. The frozen CSVs are the 1 May 2026 recent-series releases. ERS updates this product twice yearly and warns that national/regional averages do not represent every farm or production condition.
- NOAA NCEI: cite *Climate at a Glance*. The service notes that recent values may be preliminary and that adjusted climate records may change after quality control.
- BLS: cite CPI-U series `CUUR0000SA0`. The unregistered API v1 requests are split into windows within its published query limit. Response metadata such as `responseTime` can change even when observations do not, so live responses are staged for review rather than overwriting raw snapshots.
- USDA NASS: cite *Crop Production 2024 Summary*, January 2025. The report's suppression and availability codes remain authoritative. Later releases may revise estimates.
- USDA NRCS: NCCPI v3 and Soil Data Access are public federal services. NCCPI applies to inherent productivity for nonirrigated commodity crops. It is registered but not used in this national panel.

No Kaggle file, blog, search snippet, hand-entered observation, or Draft value is an admitted data source.
