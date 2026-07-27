# Teacher draft alignment audit

## Bottom line

The Goal-17 manuscript did not wholly abandon the supervisor's topic, but it
did materially shift the paper's dominant identity. Its title and central
claim became “why crop rankings do not determine land allocation.” That is a
valid caution, yet it turns the original mechanism paper into an
ordinal-non-identification paper. The shift weakened the requested emphasis on
conditional ranking reversal, lower-tail dependence, diversification failure,
operational inflexibility and agricultural information--flexibility.

The reconstructed manuscript corrects that divergence. The title, abstract,
theory, full-model experiment, six figures, discussion and conclusion all
center the question of when the highest-ranked crop receives less optimal land.
Ordinal insufficiency remains only a foundational boundary.

## Immutable baseline

- Supervisor TeX SHA-256:
  `e8885aa89be6a6010f0d3e6f8e40b4b8192a91fc90f6ca4fb16ae9b0aa9dd26c`
- Supervisor PDF SHA-256:
  `52ac1b4ef21c8d406fd6d722c877935a24d2cc6ea68520a6f35470ba8b334b44`
- Neither file was edited.

## Item-by-item alignment

| Supervisor-draft element | Goal-17 status | Reconstruction |
|---|---|---|
| Ranking reversal is the central phenomenon | Partially retained but subordinated to non-identification | Restored as title, research question and primary result |
| Agronomic score differs from margin and acreage | Retained | Retained with a genuine pre-decision relative-yield score |
| Uncertain price, yield and cost | Margin scenarios used, construction less prominent | Explicit stochastic margin model and official-data calibration |
| Land, bounds, budget, rotation and contracts | Mostly retained | Jointly solved in the principal model |
| Shared labour/equipment | Missing | Added to solver, KKT, tests and primary design |
| Expected-profit objective under loss-CVaR ceiling | Retained | Retained as the same theory and experiment model |
| Conditional reversal theorem/frontier | Weakened to identification warnings and certificates | Exact restricted necessary-and-sufficient frontier, with pairwise, complete and exclusion-based strong reversal kept distinct |
| Lower-tail dependence | Present but not a headline result | Restored through named-family phase diagram |
| Diversification failure | Diagnostic, not a central verified finding | Declared Gaussian mean--variance benchmark with strict variance reduction and a separate true-law CVaR failure |
| Agricultural information--flexibility | Abstract payoff archetypes | Restricted theorem plus shared ex-ante CVaR numerical cross-differences for agricultural signal, acreage recourse and shock buffering |
| Theory--simulation--empirical--implication sequence | Fragmented and missing standalone model/literature/implications | Restored explicitly |
| Formal first-manuscript identity | Internal corrective language remained | Clean title page and 20-page research manuscript |

## Preserved scientific components

The reconstruction preserves the supervisor's research object, multi-crop
acreage decision, stochastic profit foundation, loss-CVaR ceiling, operational
constraint logic, three reversal mechanisms, diversification-failure concept,
information--flexibility extension and managerial motivation.

## Changes required by validity

The draft's numerical values, empirical claims and references were not reused
without verification. Invalid unrestricted equivalences and monotonicity
claims were replaced, not silently deleted. The new results are narrower where
mathematics requires scope conditions, but stronger where an exact conditional
frontier can be proved.

## Issue #36 scientific-identity check

The repair does not manufacture the supervisor Draft's strongest label.  Under
the Draft's exclusion rule, strong reversal requires a higher-ranked crop to
receive zero acreage while a lower-ranked crop receives positive acreage.  The
registered principal solution is instead a complete top-crop inversion:
winter wheat is ranked first but receives less acreage than both soybean and
corn, while still receiving positive acreage.  Across all 165 frontier cells,
selected, possible and universal strong-reversal counts are all zero.  This
null result is retained.

The Kansas principal inversion is margin-induced, not risk-induced: the
official-data mean margin of wheat is lower than those of the lower-ranked
crops.  A separate registered, mean-preserving downside-shock experiment
establishes a genuine risk-induced soybean--corn crossing while preserving
both score and mean order.  A fixed-risk controlled rotation-cap path
identifies the operational crossing; the corresponding registered full
constraint sequence yields a null operational crossing and is reported as
such.

## Remaining supervisor confirmation

Scientific alignment is suitable for supervisor review, not yet claimed to be
publication-ready. Before external submission, the supervisor
should confirm author order, final affiliation wording, whether the structural
stress-test framing is appropriate for the intended journal, and whether the
single-period model is sufficient for the first manuscript.
