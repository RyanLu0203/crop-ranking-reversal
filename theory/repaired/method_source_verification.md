# Full-text method-source verification

Verification date: 2026-07-19

## Scope

External literature is used only for foundational method facts. It supplies no crop, geography, parameter, simulation, or empirical result. The paper-specific theorems are proved in proofs.md.

## LIT-THEORY-001

Rockafellar and Uryasev, “Optimization of Conditional Value-at-Risk,” Journal of Risk (2000), DOI 10.21314/JOR.2000.038.

- Full text: author-hosted 26-page PDF, https://sites.math.washington.edu/~rtr/papers/rtr179-CVaR1.pdf
- Verified content: loss is the primitive risk outcome; the auxiliary function is a threshold plus scaled expected positive excess loss; minimization over the threshold yields CVaR; linear losses under finitely sampled scenarios reduce to linear programming.
- Use here: CT1's loss convention, auxiliary representation, convexity, and LP architecture.
- Boundary: the early tail-expectation presentation imposes continuity; atoms are handled through LIT-THEORY-002 and the finite LP dual.

## LIT-THEORY-002

Rockafellar and Uryasev, “Conditional Value-at-Risk for General Loss Distributions,” Journal of Banking & Finance (2002), DOI 10.1016/S0378-4266(02)00271-6.

- Full text: author-hosted 34-page PDF, https://sites.math.washington.edu/~rtr/papers/rtr187-CVaR2.pdf
- Verified content: the optimization representation extends to general loss distributions, including discontinuities and probability mass at VaR.
- Use here: atom-safe CT1 and CT5 statements; no unsupported conditional-mean derivative is used at a VaR atom.

## LIT-THEORY-003

Ansari and Rockel, “Dependence properties of bivariate copula families,” Dependence Modeling (2024), DOI 10.1515/demo-2024-0002.

- Full text: publisher HTML, https://www.degruyterbrill.com/document/doi/10.1515/demo-2024-0002/html
- Verified content: dependence properties and orderings are family-specific; scalar summaries are not interchangeable with a full stochastic ordering.
- Use here: scope discipline for CT7. CT7 itself assumes and does not infer portfolio-loss convex order.
- Boundary: bivariate family results do not establish the required n-crop portfolio-loss ordering. That premise must be verified for the chosen simulation family and domain.

## Governance conclusion

All three records are full_text_verified=YES and citation_status=THEORY_FOUNDATION_ONLY in the literature registry. No abstract-only source and no Google Scholar snippet supports a theorem.
