# Final manuscript restructuring roadmap

## Status

This is an argument plan, not a manuscript rewrite. No Stage I section should be
replaced under GOAL-11. The final restructuring starts only after GOAL-14,
GOAL-12, GOAL-13 and GOAL-15 have passed and their claim registries are frozen.

## One-sentence target argument

In multi-crop land planning, we show that ordinal rankings become actionable
only through cardinal payoffs, downside-risk and operational feasibility;
controlled theory and simulation distinguish the resulting reversal,
diversification and information channels, while longer-horizon official data
test their observable implications without treating acreage as revealed
optimum.

This sentence is a target claim scaffold. Each clause remains blocked until the
corresponding evidence gate passes.

## Evidence ladder

The final Results narrative must progress in this order:

`decision object → positive theory → controlled mechanisms → risk/dependence
regimes → diversification/information consequences → empirical validation →
meaning and boundaries`

Limitations remain explicit, but they follow the strongest supported positive
result rather than replacing it.

## Target structure

### 1. Introduction

**Job:** establish why rank-based recommendations and cardinal land decisions
are different, why that difference matters under risk and operational
constraints, and what the paper demonstrates.

- Keep the prediction-to-prescription and crop-planning context.
- Compress the separate related-literature section into a problem-driven funnel.
- End with three or four evidence-backed contributions, not a list of audits.
- Do not mention a numerical effect until its final claim gate passes.

**Evidence gate:** final claim-evidence matrix, verified literature update and
main-figure availability.

### 2. Conceptual framework

**Job:** define rank, cardinalization, feasible action, optimal set, selection,
reversal and the five mechanism questions in plain scientific language.

- Use Figure 1 to establish the shared visual vocabulary.
- State observable, assumed and latent inputs.
- Explain possible, universal and selected reversal without leading with solver
  implementation details.

**Evidence gate:** GOAL-14 definitions and theorem classification accepted.

### 3. Stochastic optimization model

**Job:** present the retained multi-crop stochastic profit model, operational
polytope, loss-CVaR programme, dependence law and finite-scenario form.

- Preserve the Stage I sign, units, atom-safe risk and full-constraint repairs.
- Move proof detail, numerical tolerances and implementation diagnostics to
  Methods/Extended Data/Supplementary.
- Introduce the local KKT pressure terms that are used in Figure 3.

**Evidence gate:** GOAL-14 canonical theorem/proof package and notation validator.

### 4. Ranking reversal mechanisms

**Job:** deliver the central positive theoretical contribution.

- Conditions for ranking sufficiency and the identified set when absent.
- Margin, operational, risk and boundary/selection mechanisms.
- Geometry and optimal-face interpretation (Figure 2).
- Diversification taxonomy and information-actionability results.
- Clearly tag proved, conditional and numerical statements.

**Evidence gate:** GOAL-14 proof audit passes; Figure 2 analytic/numerical anchors
recover the theorems.

### 5. Numerical experiments

**Job:** test each mechanism under controlled, preregistered contrasts.

- Begin with estimands, nested models and precision/stopping design.
- Present the M0--M4 decomposition (Figure 3).
- Present controlled risk/dependence and actionability regimes (Figure 4).
- Present diversification/misspecification results (Figure 5).
- Retain null, nonmonotone, multiple-crossing and adverse outcomes.

**Evidence gate:** every promoted result passes the GOAL-12 theory, isolation,
precision, solver, replay, face and lineage gates.

### 6. Empirical validation

**Job:** test whether observed transitions and heterogeneity are consistent with
the model's observable predictions.

- Start with source timing, sample flow and observed/constructed/proxy layers.
- Report ranking definitions and acreage-share transitions.
- Present temporal/geographic holdouts, heterogeneity and aggregation (Figure 6).
- State what is observed, model generated and unidentified next to each result.

**Evidence gate:** GOAL-15 data governance, frozen design, uncertainty,
robustness, holdout, replay and claim-boundary gates pass.

### 7. Information and flexibility implications

**Job:** interpret actionability without restoring the false universal
complementarity theorem.

- State the general zero/common-policy and weak nesting results.
- Present conditional complementarity only if GOAL-14 proves sufficient
  conditions and GOAL-12 tests instances satisfying them.
- Separate empirical relevance from empirical identification.

**Evidence gate:** theory class and confirmatory interaction precision agree.

### 8. Discussion

**Job:** explain the new decision principle, relation to prior work, practical
use, external validity and failure modes.

- Lead with what the paper establishes, then why the evidence supports it.
- Discuss constraints, dependence misspecification and information deployment as
  decision-design implications, not policy prescriptions unsupported by data.
- Preserve farm-level, causal, welfare, nonlinear, dynamic and price-feedback
  limitations.
- Name the nulls and adverse cases that bound generalization.

**Evidence gate:** adversarial claim review finds no unsupported mechanism jump.

### 9. Conclusion

**Job:** state contribution, decisive evidence, implication and boundary in four
compact moves.

- No new result, citation, threshold or future promise.
- If any major mechanism gate fails, narrow the conclusion rather than promoting
  a pilot pattern.

**Evidence gate:** final claim-evidence audit and manuscript validator pass.

## Methods and reporting architecture

Nature's online Methods should carry theory proof pointers, simulation design,
precision/stopping rules, empirical sources/timing, statistical methods,
software, data/code availability and claim governance. Detailed proofs,
full-factor robustness and diagnostic tables belong in Supplementary or Extended
Data. The main narrative should not include the Stage I convergence figure unless
an adverse confirmatory result is scientifically central.

## Current-to-target disposition

| Stage I section | Final disposition |
|---|---|
| Abstract | Rewrite last, after all evidence gates; retain no unsupported mechanism verb |
| Introduction | Rebuild around the positive decision problem and evidence ladder |
| Related literature | Integrate into Introduction and Discussion; update only with verified sources |
| Integrated model | Retain core equations; integrate GOAL-14 positive results |
| Repaired structural results | Split between Conceptual framework, Model and Mechanisms |
| Data and empirical design | Move design detail to Methods; retain only result-relevant setup |
| Numerical experiments | Replace pilot-centered narrative with GOAL-12 controlled results |
| Empirical results | Replace three-year prevalence centerpiece with GOAL-15 model-linked validation |
| Robustness and extensions | Distribute decisive robustness near results; move full suite to Extended Data |
| Discussion | Rebuild from positive findings outward while preserving identification limits |
| Conclusion | Rewrite after claim freeze |
| Methods | Expand statistics, stopping, timing, lineage and availability; keep concise main flow |

## Claim and paragraph architecture

Every Results subsection should open with `To test [question], we [controlled
action]`, followed by the result, uncertainty, mechanism interpretation and
boundary. Every paragraph has one job: question, method, result, mechanism,
robustness, implication or limitation.

The final claim registry must add these fields:

- `theory_basis`;
- `simulation_estimand`;
- `empirical_construct`;
- `figure_panel`;
- `identification_status`;
- `precision_status`;
- `boundary_sentence`;
- `promotion_decision`.

## Display-item and length budget

The target is approximately six main figure groups and no main table unless a
table carries evidence that cannot be read more efficiently in a figure. Nature
currently describes roughly 4,300 main-text words and five to six modest display
items as typical for an eight-page Article. The scientific argument determines
the final count; dense dashboard figures or prose compressed below
reproducibility needs are not acceptable.

## Final reconstruction gate

Manuscript rebuilding may begin only when all conditions are true:

1. GOAL-14 results, assumptions, proofs and proof status are frozen.
2. GOAL-12 confirmatory outputs pass their promotion gates.
3. GOAL-13 figures are generated only from approved source data and pass visual QA.
4. GOAL-15 results pass source, timing, uncertainty, holdout and replay gates.
5. Every proposed major claim has theory, simulation and empirical relevance;
   missing empirical identification is explicitly represented rather than hidden.
6. The supervisor approves the resulting core-claim hierarchy and target outlet.
