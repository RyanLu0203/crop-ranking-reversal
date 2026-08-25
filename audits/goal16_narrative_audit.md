# GOAL-16 pre-rewrite narrative audit

## Baseline and method

This audit freezes the narrative state at commit `4088e62` before prose
reconstruction. It compares the section order, paragraph jobs, figure placement,
terminology and claim repetition with the requested results-led architecture.

## Central argument

The scientific argument is present and defensible: crop rankings are ordinal,
whereas acreage allocations require cardinal payoffs, uncertainty, feasibility
and a selection rule. The strongest positive evidence is E2 (operationally
forced universal reversal) and E6 (information value depends on the added
actions). Public state data show descriptive rank--acreage disagreement without
identifying a private optimization mechanism.

The manuscript nevertheless reads like a completed technical audit rather than
a Nature-style results narrative. The current sequence places related literature,
model, structural results, numerical experiments, data design, empirical
results, robustness, discussion and conclusion in separate serial blocks. That
delays the positive findings and repeats evidence boundaries in nearly every
section.

## Section audit

| Section | Current job | Strength | Problem | Decision |
|---|---|---|---|---|
| Abstract | Lists model, theory, E2, E6, failed experiments and state evidence. | Complete and numerically traceable. | Opens with definitions, uses internal terms such as “preregistered”, “promoted” and “adverse evidence”, and ends with a long prohibition list. | Rewrite as problem → theoretical advance → E2 → E6 → empirical result → bounded implication. Use conventional scientific language and fewer decimals. |
| Introduction | Seven paragraphs move from prediction/prescription to invariance, literature, framework, theory, simulations and data. | The gap and evidence hierarchy are explicit. | Too long, repeats “does not identify” and numerical results, and reads as a mini full paper. | Rebuild as exactly five argumentative paragraphs: decision problem; scientific gap; mechanism framework; evidence hierarchy; three contributions. |
| Related literature | Separates crop planning, prescriptive analytics and risk theory. | Citations are appropriately scoped. | A standalone literature block interrupts the results-led flow. | Integrate concise prior-work positioning into Introduction and Discussion; move detail to Supplement if needed. |
| Model | Defines the stochastic programme and reversal classes. | Essential scientific objects are rigorous. | Notation-first placement makes the reader cross a textbook-style gate before seeing results. | Fold the minimum model into “Ranking does not identify allocation”; move complete derivations/proofs to Supplementary Methods. |
| Structural results | Develops non-identification, forcing, KKT and boundaries. | Strongest bridge from theory to mechanism. | Multiple propositions and caveats compete; Figure 3 introduces simulation-style decomposition before the main positive experiments. | Retain core theorem and exact geometry as the first results section; compress technical proof detail and keep one boundary paragraph. |
| Numerical experiments | Presents E2 and E3 together, then E6 and E5 together. | All results and failures remain visible. | Positive and failed experiments share main figures and paragraphs, so internal evidence governance becomes the narrative. | Split into E2-only and E6-only main sections. Move E1/E3/E4/E5 inventories to Supplementary adverse-evidence sections. |
| Data and empirical design | Defines sample, scores, ranks, bootstrap and transitions. | Reproducible and cautious. | Method details precede the empirical result and the three-year limitation dominates. | Move result-driving definitions into concise Methods; open empirical Results with the scientific question and figure. |
| Empirical results | Reports concurrent, temporal and aggregation evidence. | Properly avoids mechanism/causal claims. | Spatial structure is absent, paragraph openings often lead with qualification, and several numbers repeat the Introduction/Abstract. | Rebuild around spatial distribution, definition sensitivity, lagged response, leader persistence and aggregation boundary. |
| Robustness/extensions | Separates empirical and simulation robustness. | Boundaries are explicit. | Reads as a governance checklist and generic extension list. | Distribute essential robustness beside each result; move full inventories to Supplement; keep only decision-relevant robustness in Discussion. |
| Discussion | Interprets mechanism distinction, failures, empirical evidence and limits. | Scientifically calibrated. | Repeats most Results boundaries, then repeats limitations and procedure. | Focus on meaning, relation to prior work, constraints and exactly identified data needs. Avoid figure-by-figure recap. |
| Conclusion | Restates all three layers. | Accurate and concise. | Redundant with Discussion and required structure does not need a separate conclusion. | Fold the bounded conclusion into the final Discussion paragraph. |
| Methods | Describes experiments, analytics, data and figures. | Auditable. | Contains internal pipeline language and the colour card in scientific prose. | Keep technical reproducibility here, translate governance terms, move palette/QA details to reporting/audit files. |

## Paragraph and terminology findings

- Repeated boundary: “observed acreage does not identify a private optimizer,
  constraint, CVaR preference, copula mechanism, welfare or causality” appears
  in the Abstract, Introduction, data design, empirical results, Discussion,
  Conclusion, Methods and captions. It should appear once in the empirical
  Results and once, more broadly, in Discussion.
- Repeated evidence status: “E1, E3, E4 and E5 failed precision” is repeated in
  the Introduction, Results, Robustness, Discussion and Conclusion. Main text
  needs one concise sentence plus a Supplementary pointer.
- Internal terms to remove from scientific prose: `admitted`, `promoted`,
  `adverse evidence`, `claim gate`, `registered package`, `Stage II`, and
  all-caps registry statuses. Replace with `public-data sample`, `met the
  pre-specified precision criterion`, `inconclusive`, or direct descriptions.
- Figure captions currently state boundaries well but do not consistently
  define every interval, symbol and sample size; this will be corrected during
  the figure rewrite.

## Frozen results-led architecture

1. Abstract.
2. Introduction.
3. Ranking does not identify allocation.
4. Operational constraints produce universal reversal.
5. Information value depends on feasible actions.
6. Empirical rank--acreage patterns and identification boundaries.
7. Discussion.
8. Methods.
9. References.

Every Results section will use: scientific question → mechanism → design →
result → interpretation → one concise boundary. Long proofs, failed-experiment
inventories and validation ledgers move to Supplementary Information without
being deleted.

