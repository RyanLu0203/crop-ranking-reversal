# GOAL-14 bounded methodological-source verification

Verification date: 2026-07-21

## Scope and search route

The search was limited to mathematical foundations needed by the Stage II
extension. It was not a new literature review. The academic-search MCP endpoints
were unavailable, so the documented fallback was used: exact-title/DOI web
discovery followed by author, publisher or institutional full-text inspection.
Search snippets and the teacher bibliography were not used as evidence.

Current exact-title/identifier queries covered:

- `Optimization of Conditional Value-at-Risk Rockafellar Uryasev full text`;
- `Conditional Value-at-Risk for General Loss Distributions full text`;
- `10.1515/demo-2024-0002 Dependence properties bivariate copula families`;
- `The Value of Information Given Decision Flexibility full text`;
- `Equivalent Comparisons of Experiments 10.1214/aoms/1177729032`.

The Blackwell record was used only to check terminology. S2-T02 is proved
directly from reproducible garbling/policy-space inclusion and does not depend
on an inaccessible theorem excerpt.

## Sources actually used

### LIT-THEORY-001 — Rockafellar and Uryasev (2000)

- Registry DOI: `10.21314/JOR.2000.038`.
- Full text: author-hosted 26-page PDF,
  https://sites.math.washington.edu/~rtr/papers/rtr179-CVaR1.pdf
- Rechecked content: loss is the primitive; the threshold-plus-positive-excess
  representation is convex; affine finite-scenario losses admit a linear
  programming representation.
- Stage II role: retained loss sign, LP and convex/KKT foundation only.

### LIT-THEORY-002 — Rockafellar and Uryasev (2002)

- Registry DOI: `10.1016/S0378-4266(02)00271-6`.
- Full text: author-hosted 34-page PDF,
  https://sites.math.washington.edu/~rtr/papers/rtr187-CVaR2.pdf
- Rechecked content: the fundamental minimization formula persists for general
  loss distributions; finite scenario atoms are fractionally represented; CVaR
  remains convex for affine/convex loss.
- Stage II role: atom-safe subgradient/tail-weight discipline.

### LIT-THEORY-003 — Ansari and Rockel (2024)

- Registry DOI: `10.1515/demo-2024-0002`.
- Publisher full text:
  https://www.degruyterbrill.com/document/doi/10.1515/demo-2024-0002/html
- Rechecked content: lower-orthant, conditional-distribution and concordance
  order properties are family- and parameter-specific.
- Stage II role: scope boundary for named-family dependence statements. The
  article is bivariate and does not prove the n-crop loss order assumed in
  S2-P06.

### LIT-VOI-002 — Merkhofer technical report (1975)

- Registry DOI: `10.21236/ADA016836`.
- Full technical report inspected through the DTIC accession mirror recorded in
  the registry; the final journal metadata was rechecked at INFORMS as M. W.
  Merkhofer (1977), *Management Science* 23(7), 716--727, DOI
  `10.1287/mnsc.23.7.716`.
- Rechecked content: the value of information depends on available decision
  flexibility and admits upper-bound/sensitivity analysis.
- Stage II role: historical context only. It does not prove general strict
  complementarity; S2-T02 and S2-T03 have self-contained proofs.

## Source boundary

- No Topkis citation is used as a substitute for assumptions. S2-T03 states and
  proves its lattice, strong-set-order and joint-supermodularity conditions.
- No Nelsen or teacher-draft citation supports a dependence theorem.
- No external source supplies crop parameters, results, thresholds or empirical
  conclusions.
- Every source named above was already recorded as full-text verified in
  `evidence_registry/literature_registry.csv`; no unregistered source is needed
  to prove the Stage II results.
