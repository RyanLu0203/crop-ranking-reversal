# GOAL-16 title and terminology audit

## Title candidates

| Candidate | Accuracy | Breadth/readability | Risk | Decision |
|---|---|---|---|---|
| When crop rankings do not determine land allocations | Accurate and matches the baseline. | Clear, but “when” implies the paper identifies a comprehensive set of conditions. | Slightly longer and plural “allocations” is awkward. | Acceptable baseline. |
| Why crop rankings do not determine land allocation | Accurate and directly expresses the ordinal-to-cardinal gap. | Short, accessible beyond operations research. | “Why” requires the mechanism evidence to remain central. | Preferred working title. |
| Crop rankings do not determine acreage allocation | Accurate and most direct. | Very concise. | Declarative form can sound universal without the model context. | Strong alternative. |
| From crop rankings to constrained acreage allocation | Accurate about the decision bridge. | Broad and neutral. | Does not foreground the empirical disagreement/reversal problem. | Secondary alternative. |
| Set-valued crop allocation from ordinal rankings | Mathematically specific. | Narrow and jargon-heavy. | Depends on internal technical terminology and underplays E2/E6. | Reject. |

The preferred title is not a cosmetic change: it matches the central scientific
question and the redesigned mechanism-led Results. It will be adopted only with
that structural rewrite.

## Canonical terminology

| Canonical term | Use for | Avoid as interchangeable alternatives |
|---|---|---|
| crop ranking | an ordinal ordering of crops | priority list, crop order, score order when the ranking itself is meant |
| suitability score | an input score with a defined construction | suitability index unless the source uses that formal name |
| expected margin | a cardinal expected economic return | expected profit when costs/units differ from the defined margin |
| acreage allocation | crop shares or acreage vector | land use, plan, portfolio when the mathematical allocation is meant |
| optimal face | the full set of optimal allocations | solution set, multiple solution region, optimal set without definition |
| selected allocation | the optimizer returned under a declared selection rule | observed allocation or chosen optimum unless actually selected by the model |
| possible reversal | at least one optimizer reverses the ranking | weak reversal |
| universal reversal | every optimizer reverses the ranking | strong reversal |
| selected reversal | the declared selected allocation reverses the ranking | solver reversal |
| operational intervention | an assigned change to budget, rotation, contract or bound | treatment constraint, operational forcing where no forcing is proven |
| downside-risk constraint | the loss-CVaR feasibility restriction | risk preference or risk aversion without identification |
| information value | value difference between informed and uninformed problems | prediction value or signal benefit without the formal contrast |
| action-set flexibility | enlargement of the feasible contingent action set | generic flexibility |

## Evidence language

- `promoted` → `met the pre-specified precision criterion` or simply state the
  result.
- `non-promoted` / `adverse` → `did not meet the pre-specified precision
  criterion` or `retained as inconclusive evidence`.
- `admitted data` → `public-data sample` or `included official observations`.
- `claim gate` → `precision criterion`.
- `registered package` → `pre-specified design and reproducibility record`.
- `unidentified` remains valid only for a defined estimand/construct; otherwise
  prefer `not measured in these data`.

Registry and audit files may retain machine-facing status vocabulary. Main
scientific prose, titles and figure legends may not.

