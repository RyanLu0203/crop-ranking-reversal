# Proposed minimal repairs

These repairs preserve the teacher's multi-crop architecture and are ordered from least to most invasive.

| Repair ID | Original statement | Identified flaw | Proposed repair | Mathematical cost | Effect on innovation | Effect on simulation design | Effect on empirical design | Supervisor approval required |
|---|---|---|---|---|---|---|---|---|
| M01 | Negative upper-profit-tail integral defines CVaR | Selects best profits, not worst losses | Declare $L=-\Pi$; use RU definition/lower-profit tail | Notational only | None | Enforces loss-tail unit tests | Align observed/simulated loss outcomes | No |
| M02 | Marginal CVaR is a unique conditional derivative at $F_\Pi^{-1}(\alpha)$ | Wrong cutoff and invalid at atoms | Use $1-\alpha$; default to subgradient/LP dual | Adds regularity caveat | Strengthens rigor | Requires atom and dual checks | Requires tail sample-size disclosure | No |
| M03 | Displayed KKT equation is complete | Budget and shared/rotation normals omitted | Add $\beta c+H^T\eta+u^+-u^-$ | More dual terms | Preserves mechanism with correct attribution | Report all active constraints/duals | Requires sources for operational bounds | No |
| M04 | Pairwise dual-gap inequality iff acreage reversal | Marginal stationarity does not order levels | Replace with KKT characterization plus feasibility-forced sufficient result | Removes iff theorem | Narrows headline but makes it defensible | Audit full optimal set | Distinguish constraint prevalence from risk causation | Yes |
| M05 | $s_i=\mu_i$ | Score and monetary mean have incompatible units | Require rank equivalence only | One assumption rewrite | None | Compare rank mappings | Estimate rank concordance | No |
| M06 | $\lambda_L$ globally raises marginal-CVaR gap | Scalar does not order copulas | Restrict to fixed marginals/named family and proved order; otherwise numerical conjecture | Strong restrictions | Converts universality to conditional mechanism | Family-specific sweeps and falsification | Dependence-family uncertainty required | Yes |
| M07 | Unique reversal threshold always exists | Missing crossing, monotonicity, uniqueness, selection | Allow no/single/interval/multiple crossings; conditional crossing lemma only | Removes global theorem | Preserves threshold as estimand, not fact | Adaptive grid and basis audit | Report crossing-set uncertainty | Yes |
| M08 | Pseudo-diversifier scalars imply optimizer inclusion/exclusion | Means, constraints, and risk limits also determine choice | Keep descriptive label with declared thresholds; replace proposition by benchmark examples | Downgrades proposition | Retains diagnostic contribution | Test both edge directions | Avoid causal mechanism label | Yes |
| M09 | VOI expression mixes posterior and random payoff terms | Timing and expectations inconsistent | Use common outer expectation and signal-before-recourse policy | Definition repair | None | Add signal/action timing tests | Requires forecast vintages and decision dates | No |
| M10 | Information-flexibility complementarity is strictly positive/supermodular | Lattice and increasing-differences conditions absent | Retain zero-value/common-policy and weak nesting results; move strict complementarity to conditional extension | Major theorem restriction | Main novelty may shift | Include zero/substitute cases | Interaction cannot be causal without design | Yes |
| M11 | Illustrative thresholds/percentages are findings | No admissible provenance | Quarantine pending preregistered simulation/empirical run | Removes unsupported numbers | Protects credibility | Register config/seeds/outputs | Freeze holdout design and provenance | No |

No repair directly edits the canonical teacher manuscript in this goal.
