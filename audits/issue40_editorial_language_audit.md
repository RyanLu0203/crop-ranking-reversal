# Editorial and scholarly-language audit

Date: 2026-07-30

## Scope and outcome

The main manuscript and Supplementary Information were revised line by line for
logical sequence, scientific precision, academic tone, terminology
consistency, claim–evidence alignment, redundancy and readability. The revision
changed exposition, notation labels and figure text only. It did not alter the
scientific model, datasets, experiment design or validated numerical results.

The final abstract contains 236 words (TeXcount). The conclusion contains 587
words. The compiled main manuscript has 21 pages and the Supplementary
Information has 8 pages.

## Major language and logic changes

- The abstract now follows a single sequence: research problem, stochastic
  model, theoretical result, Kansas complete rank reversal, three mechanisms,
  diversification failure, information–flexibility boundary, descriptive
  external evidence and implication.
- The Introduction now progresses from the external performance index to
  expected margins, joint downside risk, operational feasibility, optimized
  allocation, reversal classification, diversification, information–
  flexibility interaction and external descriptive evidence.
- Theory paragraphs state the assumptions before the result and distinguish
  the theorem’s domain from the discrete shared-risk classification.
- Numerical paragraphs state the design, comparison, result, mechanism and
  limitation in that order. Margin-induced, risk-induced and operationally
  induced reversal are reported separately.
- External evidence distinguishes the estimand, panel construction, estimate,
  uncertainty and identification boundary. Population-frequency and causal
  interpretations were removed.
- The Conclusion was rewritten around the research answer, theoretical
  contribution, three mechanisms, diversification, information–flexibility,
  empirical boundary and future research.
- Figure and table captions were shortened and made self-contained. Figure
  legends now use academic descriptions such as “optimized allocations” and
  “displayed bootstrap draws.”
- The literature matrix now defines central, conditional and absent coverage
  explicitly and states that the selected comparison is not exhaustive.

## Terminology dictionary

| Concept | Canonical wording |
|---|---|
| External crop measure | historical relative-yield performance index |
| Heavy-tailed marginal or copula family | Student-\(t\) |
| Elliptical dependence benchmark | Gaussian copula |
| Archimedean dependence family | Clayton copula |
| Downside-risk measure | loss-CVaR |
| Mean–variance comparison | selected Gaussian mean–variance policy |
| Unconstrained comparison | expected-profit benchmark |
| Heavy-tail comparison | tail-aware policy |
| Two-crop order disagreement | pairwise reversal |
| Highest-ranked crop below all others | complete rank reversal |
| Exclusion of a higher-ranked crop | strong exclusion reversal |
| Risk-ceiling mechanism | risk-induced reversal |
| Expected-margin mechanism | margin-induced reversal |
| Feasible-set mechanism | operationally induced reversal |
| Information and action-set relation | information–flexibility interaction |
| Discrete interaction statistic | cross-difference |

Common crop names are lowercase in running prose. Table and figure labels use
capitalization only where formatting requires it.

## Notation changes

- \(\rho\) is reserved for the normalized risk-tolerance index.
- The rotation multiplier formerly sharing \(\rho\) is now \(\nu^R\).
- Operational multipliers are \(\nu^A,\nu^B,\nu^R,\nu^K,\nu^G,\nu^\ell\)
  and \(\nu^u\) in the main KKT statement, finite-scenario KKT system, proofs
  and notation table.
- \(\gamma\) is reserved for the Gaussian mean–variance penalty; the former
  land multiplier is now \(\nu^A\).
- Signal accuracy is \(\xi\), leaving \(q_m\) exclusively for finite-scenario
  excess variables.
- Closed intervals use commas between endpoints. The reported failure interval
  is \(\gamma\in[0.0068,0.0088]\).

## Removed process-language categories

The academic text was cleared of software-development metadata, revision
history, internal-review language, implementation defensiveness, file-oriented
claims and result-retention language. Computational terms that remain in
Methods or Supplementary Methods—HiGHS, SLSQP, scenario counts, numerical
tolerances and resampling procedures—describe conventional scientific
methodology.

## Repeated-claim reductions

- The eight-year calibration limitation appears with the relevant uncertainty
  result, in the complete Limitations section and once in the Conclusion.
- The aggregate-state-panel identification boundary is developed in the
  external-evidence section, listed once in Limitations and summarized once in
  the Conclusion.
- Structural stress status is stated in calibration or mechanism-specific
  passages rather than repeated across sections.
- Detailed phase counts and parameter values were removed from the abstract and
  Conclusion.
- The contribution sequence is stated once in the Introduction and synthesized,
  rather than repeated, in the Conclusion.

## Final checks

- Prohibited workflow-term scan of TeX sources and extracted PDF text: PASS,
  zero matches.
- Revision-history and defensive-language semantic scan: PASS, zero matches.
- Terminology and capitalization scan: PASS.
- Symbol-uniqueness review: PASS.
- Abstract-to-results and conclusion-to-evidence review: PASS.
- Complete numerical reconstruction and output SHA-256 verification: PASS.
- Deterministic two-build comparison: PASS; byte-identical PDFs.
- LaTeX log review: PASS; no overfull or underfull boxes, unresolved references
  or unresolved citations.
- Page-by-page visual inspection: PASS for all 21 main-manuscript pages and all
  8 Supplementary Information pages.
- Automated figure geometry review: PASS; zero boundary failures and zero title
  collisions.

Final PDF SHA-256 values:

- `main_manuscript.pdf`:
  `320e37c61a3f4706bc7afe33dc19a6594635eeaf17cdecf698ccd8f536508aa8`
- `supplementary_information.pdf`:
  `1c80baeff1afba167dcd61625610774bcb56b26a8682fd1e863f80af75d85cc7`
