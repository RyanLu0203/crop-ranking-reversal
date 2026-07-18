# Claim-organized annotated literature synthesis

This is an evidence map, not the manuscript Literature Review. It states what each literature cluster can and cannot support.

## 1. Agricultural prediction is not acreage prescription

Agricultural machine learning commonly uses weather, soil, sensor, and remote-sensing variables to predict yields or classify agronomic outcomes (Liakos et al., 2018; van Klompenburg et al., 2020). These sources support the background proposition that predictive crop analytics are mature enough to produce scores, forecasts, and rankings.

They do not show that a highest-scoring crop should receive the most land. Neither predictive accuracy nor an ordinal suitability rank encodes land, budget, crop bounds, rotations, portfolio dependence, or tail-risk tolerance. The manuscript may therefore motivate a prediction–prescription gap, but must not describe the specific suitability score as externally validated until its construction is documented.

## 2. Crop planning is a constrained portfolio decision

Filippi et al. (2017) is the closest included predecessor: it formulates realistic crop selection with stochastic prices and yields, resource and timing constraints, and a CVaR-based alternative to expected profit. Boyabatlı et al. (2019) shows that revenue uncertainty and rotation benefits jointly shape dynamic farmland allocation. Benini et al. (2023) formalizes multi-period crop rotation and diversification constraints. Randall et al. (2022) provides a distinct robust-optimization treatment of climate-model uncertainty, while Randall et al. (2024) maps the broader recent field.

Together these papers support retaining a multi-crop operational feasible set. They also show why a two-crop unconstrained toy model cannot substitute for the main model. They do not, however, establish the present paper's reversal definitions, copula-tail mechanism, or information-flexibility results.

## 3. Stochastic programming fixes decision timing

Dantzig (1955) separates here-and-now decisions from later actions contingent on revealed uncertainty. This supports the paper's insistence that acreage, forecast, and recourse timing be explicit. It also explains why the original value-of-information expression could not mix prior and posterior decisions under inconsistent expectations.

The foundational result supplies architecture, not a crop-specific distribution, scenario count, or empirical parameter.

## 4. Loss-CVaR has a precise sign, tail, and optimization representation

Rockafellar and Uryasev (2000) give the auxiliary-function representation that makes loss-CVaR convex and scenario-linearizable. Their 2002 treatment handles general distributions, including discontinuities and atoms. These sources directly support the repaired loss convention and finite-scenario LP.

They do not support the Draft's negative upper-profit-tail expression, nor do they imply an acreage-ranking theorem. The crop-selection application by Filippi et al. demonstrates relevance but not general equivalence between a CVaR marginal condition and acreage levels.

## 5. Copula tail dependence requires family-specific discipline

Demarta and McNeil (2005) describes t-copula tail dependence and related constructions. Ansari and Rockel (2024) demonstrates that dependence properties and orderings vary across named bivariate families. These sources support use of a declared copula family and explicit tail-dependence diagnostics.

They do not justify ordering arbitrary joint laws by one lower-tail coefficient. The canonical dependence theorem therefore assumes portfolio-loss convex order on a declared domain; simulations must verify that premise rather than infer it from the coefficient.

## 6. Predictive performance and decision quality are different targets

Bertsimas and Kallus (2020) link side information to conditional prescriptions. Elmachtoub and Grigas (2022) define downstream decision regret and an optimization-aware surrogate. Wilder et al. (2019) differentiates through combinatorial decision structure, and Mandi et al. (2023) surveys and benchmarks the broader decision-focused learning field.

These works support evaluating forecasts by the quality of downstream allocations in addition to conventional prediction metrics. They do not license end-to-end learning in this paper without leakage controls, an identified decision problem, and an admissible holdout design. For the first paper, the safer contribution is a transparent forecast-to-optimization bridge rather than a claim of a new learning algorithm.

## 7. Information is valuable only through changed feasible actions

Keisler (2004) evaluates information strategies by the resource-allocation decisions they improve. Merkhofer (1975) analyzes information value under decision flexibility. These sources support the canonical actionability result: if signal-contingent optimal policies coincide, information has zero operational value.

They do not prove general strict information–flexibility complementarity. Weak value monotonicity follows from nested action sets; strictness or supermodularity requires additional structure and must remain a restricted extension or simulation hypothesis.

## 8. Flexibility value depends on the complete decision environment

Van Mieghem (1998) shows that the value of flexible resources depends on margins, costs, and multivariate uncertainty, and can defy intuition based on correlation alone. This reinforces two boundaries: expanded feasible action sets weakly increase optimized value, while a scalar dependence measure cannot identify flexibility value.

Manufacturing capacity is an analogy, not crop evidence. In the empirical paper, flexibility must be represented by documented acreage bounds, timing, rotation, or recourse options rather than asserted from observed diversification.

## 9. Defensible novelty position

The included close crop studies optimize crop mix, rotation, or robustness. The included dependence papers characterize joint-tail structure. The included prescriptive papers connect predictions to decisions, and the information/flexibility papers value action-contingent information.

The paper's defensible integration is to compare an ordinal recommendation ranking with the entire optimal solution set of a constrained multi-crop loss-CVaR program; identify possible, universal, and selected reversals; stress a named dependence family without treating a tail coefficient as a global order; and evaluate forecast information conditional on operational flexibility.

This is a bounded comparison against the verified set. It must be written as “differs from the included close studies by jointly…” rather than “is the first.”
