# Final supervisor-Draft alignment note

This note is external to the main manuscript and Supplementary Information.
It compares the final paper with the immutable supervisor Draft as a research
and model-architecture baseline. The Draft's citations, data, parameters,
figures, numerical claims and conclusions are not treated as verified
evidence.

The immutable baseline remains unchanged:

- TeX SHA-256:
  `e8885aa89be6a6010f0d3e6f8e40b4b8192a91fc90f6ca4fb16ae9b0aa9dd26c`
- PDF SHA-256:
  `52ac1b4ef21c8d406fd6d722c877935a24d2cc6ea68520a6f35470ba8b334b44`

## Item-by-item classification

| Item | Relationship | Alignment assessment |
|---|---|---|
| 1. Central research question | preserved | The paper continues to ask when an externally ranked crop receives less optimal acreage than a lower-ranked crop under economic, risk and operational considerations. Ranking reversal remains the title-level and model-level phenomenon; ordinal information limits are a boundary rather than the paper's main identity. |
| 2. Crop-ranking reversal definition | preserved with mathematical repair | Pairwise and complete rank reversal remain explicit. The Draft's strong reversal is retained as an exclusion condition, \(s_i>s_j\) and \(x_i=0<x_j\), and is kept distinct from a complete rank reversal in which every crop remains positively allocated. |
| 3. Multi-crop stochastic-profit model | preserved with mathematical repair | The acreage decision, uncertain price-yield-cost margins and expected-profit objective are preserved. The feasible set now states land, crop bounds, budget, rotation, contract, labour and equipment restrictions explicitly, and the finite-scenario KKT system is complete. |
| 4. Loss-CVaR framework | preserved with mathematical repair | Expected profit remains the objective and downside risk remains an explicit loss-CVaR ceiling. The loss sign convention, free VaR threshold, scenario excess variables and ex-ante risk treatment are stated consistently. |
| 5. Margin heterogeneity | preserved | Separation between an external performance score and expected economic margins remains a primary mechanism. In the Kansas calibration, winter wheat ranks first by the historical relative-yield index but has the lowest calibrated mean margin. |
| 6. Lower-tail dependence | preserved as a conditional mechanism | Gaussian, Student-\(t\) and Clayton dependence paths remain central to the risk analysis. Family-specific phase results and a controlled downside-stress crossing replace any claim that one scalar tail-dependence measure universally orders crop shares across families. |
| 7. Diversification failure | preserved with mathematical repair | The paper retains the Draft's warning that conventional diversification can fail under joint downside risk. The final test uses a specified expected-profit benchmark, a selected Gaussian mean-variance policy with verified variance reduction, and a Student-\(t\) evaluation-law loss-CVaR comparison against a tail-aware policy. |
| 8. Operational inflexibility | preserved as a conditional mechanism | Rotation, contract, budget and shared-capacity restrictions remain part of the common operational model. A controlled soybean rotation-cap path demonstrates an operationally induced crossing, while the baseline calibrated constraint sequence is reported as non-crossing. |
| 9. Information-flexibility interaction | preserved as a conditional mechanism | The Draft's information-flexibility question remains. Complementarity is proved only for posterior-separable or nonbinding-risk conditions; the shared ex-ante loss-CVaR model is classified numerically by signed cross-differences and also permits substitution under shock buffering. |
| 10. Managerial and policy implications | preserved | The final paper continues to connect rankings with advisory systems, downside-risk governance, operational flexibility and the value of climate information. Each implication is conditional on the declared score, margin model, joint law and feasible action set. |
| 11. Manuscript section order | preserved | The paper follows the Draft's model-to-theory-to-evidence innovation chain through Introduction, literature, model, theoretical results, numerical experiments, implications and conclusion. Methods and external descriptive evidence are separated for transparency. |
| 12. Data and score construction | remaining proxy-level deviation | The final score is a pre-decision historical relative-yield performance index based on state yield relative to same-year national yield. It is transparent and reproducible but is not a pure soil-climate suitability score. Kansas margins combine state yields with national prices and costs rather than farm-level expected profits. |
| 13. Empirical strength | replaced with independently verified evidence | The illustrative Iowa/county calibration and claimed out-of-sample validation are not retained. Official USDA and BLS data support the Kansas calibration and a 31-state descriptive panel, whose disagreement frequencies and lagged association are reported with explicit identification boundaries. |
| 14. Theoretical claims removed or conditioned | not supported and therefore removed | Universal tail-dependence monotonicity, a universal unique reversal threshold and unconditional strict information-flexibility complementarity are not retained. The final paper states exact restricted results, family-specific or potentially disconnected regions, and conditional complementarity or substitution. |
| 15. Unsupported Draft results not retained | not supported and therefore removed | The Draft's welfare-loss percentages, illustrative crop budgets, unverified reversal thresholds, seasonal information values and other unverified numerical claims are not used. They are replaced only where independently reproduced evidence exists. |

## Alignment conclusion

The final paper preserves the supervisor Draft's research problem,
stochastic-profit and loss-CVaR model foundation, and innovation chain linking
margin heterogeneity, joint downside risk, diversification, operational
constraints and information value. It does not revert to an
ordinal-insufficiency paper.

Mathematical and evidential boundaries change the strength of several Draft
claims. Universal tail-dependence monotonicity, a universal unique threshold
and unconditional strict information-flexibility complementarity are not
retained. The original welfare-loss percentages and other unverified numerical
claims are also excluded.

The historical relative-yield performance index is a transparent proxy, not a
pure soil-climate suitability score. After lower-bound relaxation makes crop
exit admissible, strong exclusion reversal remains absent over the evaluated
grid. This is a substantive null result. The remaining differences from the
Draft are therefore evidence-led mathematical and empirical repairs rather
than a change in research topic.
