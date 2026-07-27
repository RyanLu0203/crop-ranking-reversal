# Issue #34 acceptance matrix

Status vocabulary: `BASELINE_PASS`, `BASELINE_PARTIAL`, `BASELINE_FAIL`,
`IN_PROGRESS`, `PASS`, `BLOCKED`.  A keyword match is not evidence.  Every
`PASS` row must cite an executable check or a registered output.

The immutable supervisor Draft is the research-direction authority.  The
Goal-17 manuscript at commit `1262b19150fd1e63f549d3511ba478b003b08d9e`
is only the technical baseline for this reconstruction.

## Baseline alignment diagnosis

| ID | Issue #34 requirement | Baseline status | Baseline evidence | Required reconstruction / closure evidence |
|---|---|---|---|---|
| R01 | Ranking reversal is the central phenomenon | BASELINE_PARTIAL | Title and manuscript study ranking/allocation disagreement, but the dominant claim is non-identification | Reposition title, abstract, introduction, theory, experiments and conclusion around conditional reversal mechanisms |
| R02 | Margin heterogeneity is a principal mechanism | BASELINE_PARTIAL | Margin-gap experiment and operating-margin evidence exist | Integrate the mechanism into the full-model experiment and reversal frontier |
| R03 | Lower-tail dependence is a principal mechanism | BASELINE_PARTIAL | Named-copula sensitivity exists; headline evidence is inconclusive | Add matched-dependence comparisons, active-set/reversal regions and uncertainty |
| R04 | Diversification failure is a formal contribution | BASELINE_PARTIAL | Executable diagnostic exists, but no sufficiently strong headline theorem/criterion | State a formal criterion and demonstrate variance/Gaussian versus CVaR allocation disagreement |
| R05 | Operational inflexibility is a principal mechanism | BASELINE_PARTIAL | Budget, rotation and contract experiments exist separately | Solve them jointly with bounds and shared resources in the principal experiment |
| R06 | Information–flexibility interaction is formal and agricultural | BASELINE_FAIL | Existing payoff archetypes are abstract and include a dominated-option illustration | Build a staged agricultural signal/partial-commitment experiment with strict, zero and substitution regions |
| R07 | Paper is not an ordinal-insufficiency paper | BASELINE_FAIL | Baseline title is “Why crop rankings do not determine land allocation”; foundational non-identification dominates | Make non-identification foundational only; lead with reconstructed conditional theory and evidence |
| R08 | Supervisor Draft remains scientific authority | BASELINE_PARTIAL | Immutable hashes and audit trail are preserved | Produce an item-by-item alignment audit against the Draft’s concepts, model and innovation chain |

## Mathematical validity

| ID | Requirement | Baseline status | Closure evidence |
|---|---|---|---|
| M01 | Correct loss-CVaR and finite-scenario RU formulation | BASELINE_PASS | Existing theory, optimizer and atom-safe tests |
| M02 | Multi-crop stochastic price, yield, cost and margin model | BASELINE_PARTIAL | Existing scenarios model margins directly | Explicit price-yield-cost construction and timing in model/data sections |
| M03 | Land and explicit idle-land treatment | BASELINE_PARTIAL | Land is `<=`; idle land is implicit | Define idle acreage and report it in solver outputs |
| M04 | Crop lower/upper bounds | BASELINE_PASS | Optimizer bounds and diagnostics |
| M05 | Budget/liquidity | BASELINE_PASS | Optimizer budget row and dual |
| M06 | Rotation constraints | BASELINE_PASS | Crop caps and duals |
| M07 | Contract commitments | BASELINE_PASS | Minimum crop shares and duals |
| M08 | Equipment/labour/shared-capacity constraints | BASELINE_FAIL | No general shared-resource matrix in optimizer | Extend both expected-profit and CVaR solvers, diagnostics, KKT and tests |
| M09 | Expected-profit maximum under CVaR ceiling | BASELINE_PASS | Existing LP objective and CVaR row |
| M10 | Complete KKT including all rows, bounds, excess variables and free VaR | BASELINE_PARTIAL | Existing LP KKT is complete for implemented rows | Add shared-resource terms and supplementary derivation |
| M11 | Multiple optima and deterministic selection | BASELINE_PASS | Optimal-face audit plus deterministic HiGHS selection |
| M12 | Non-trivial reversal characterization/frontier | BASELINE_PARTIAL | Exchange/KKT certificates exist; no strong restricted iff frontier theorem | Add restricted necessary-and-sufficient/active-set result and computational verification |
| M13 | Named-family dependence result with valid scope | BASELINE_PARTIAL | Gaussian, Student-t, Clayton and empirical paths exist | Report risk-feasible set, active sets, reversal set connectedness and uncertainty |
| M14 | Formal executable diversification-failure result | BASELINE_PARTIAL | Diagnostic only | Theorem/criterion plus matched-correlation numerical witness |
| M15 | Information value, nested flexibility, strict/zero/substitution results | BASELINE_PARTIAL | Abstract archetype theorems exist | Agricultural decision timeline, sufficient conditions and integrated experiment |
| M16 | Full proofs and symbolic/computational verification | BASELINE_PARTIAL | Supplementary proofs and unit tests exist | Add proofs/tests for every new Issue #34 result |

## Numerical, empirical and evidence validity

| ID | Requirement | Baseline status | Closure evidence |
|---|---|---|---|
| E01 | Principal experiment solves the complete theoretical model | BASELINE_FAIL | Existing mechanisms are mainly isolated experimental blocks | Joint full-model registered design and solver-generated outputs |
| E02 | Suitability-proportional policy | BASELINE_PASS | Existing benchmark implementation |
| E03 | Winner-take-all policy | BASELINE_FAIL | Not in the formal experiment | Add feasibility-repaired and unconstrained labels where required |
| E04 | Expected-profit policy without CVaR | BASELINE_PASS | Existing LP benchmark |
| E05 | Mean–variance/correlation policy | BASELINE_PASS | Existing nonlinear benchmark |
| E06 | Full CVaR operational optimum | BASELINE_PARTIAL | Existing model omits shared resources | Add shared resources and joint constraint regime |
| E07 | Separate general dependence from lower-tail dependence | BASELINE_PARTIAL | Cross-family sensitivity exists | Matched Kendall/Pearson comparisons and attribution labels |
| E08 | Multi-dimensional phase diagram | BASELINE_FAIL | Existing risk/dependence outputs are not the requested full classification | Generate no/weak/strong/infeasible/multiple/active-set map |
| E09 | Systematic sensitivity across all registered dimensions | BASELINE_PARTIAL | Many dimensions exist, dispersed across workflows | Issue #34 robustness registry and complete results, including null/non-monotone cells |
| E10 | Bootstrap/MCSE/bands/boundary uncertainty | BASELINE_PARTIAL | Replication intervals exist; core frontier uncertainty is absent | Bootstrap calibration and reversal-boundary bands |
| E11 | Raw-official-data-to-results empirical pipeline | BASELINE_PASS | Retrieval, cleaning and state-panel scripts exist | Re-run and package under Issue #34 paths |
| E12 | Genuine recommendation score | BASELINE_PARTIAL | Lagged relative-yield score exists but main narrative mixes score definitions | Elevate pre-decision historical yield potential as central score; distinguish all score families |
| E13 | Timing, leakage, geography, sample and missingness documented | BASELINE_PARTIAL | Contracts and empirical notes exist | Consolidated dictionary, manifest and manuscript methods |
| E14 | Aggregate evidence keeps identification boundaries | BASELINE_PASS | Current manuscript is appropriately descriptive | Preserve null intervals and ecological limits |
| E15 | Literature search covers every innovation stream | BASELINE_FAIL | Nineteen-source registry and incomplete Scholar/citation chaining | Multi-stream Scholar/Crossref/publisher/backward-forward search log |
| E16 | Citation existence and claim support audited separately | BASELINE_PARTIAL | Registries exist | Complete Issue #34 claim-reference matrix and reliability audit |

## Presentation and reproducibility

| ID | Requirement | Baseline status | Closure evidence |
|---|---|---|---|
| P01 | Required supervisor-Draft scientific order | BASELINE_FAIL | Current structure omits standalone literature review/model/implications sections | Rebuild main manuscript structure |
| P02 | Formal research-paper identity; no internal labels/placeholders | BASELINE_FAIL | Title metadata says “Stage II final scientific draft”; author is unconfirmed | Clean title page, metadata and all internal process language |
| P03 | Natural 18–25-page main manuscript plus substantial supplement | BASELINE_FAIL | Baseline is 16 + 11 pages | Complete content first, then verify 18–25 main pages |
| P04 | Six-figure scientific narrative with uncertainty | BASELINE_PARTIAL | Six polished figures exist but carry the corrective-manuscript narrative | Regenerate figures from Issue #34 registered outputs |
| P05 | No unresolved citations/refs, overfull boxes or broken equations | PASS | `make issue34`; final `main_manuscript.log` has no unresolved citations/references or overfull boxes; supplement has only non-substantive float-placement warnings |
| P06 | Page-by-page visual QA | PASS | All 20 main-text pages and all 7 supplementary pages were rendered with `pdftoppm` and inspected; see `audits/issue34_final_page_qa.md` |
| P07 | One-command or deterministic raw-to-paper pipeline | BASELINE_PARTIAL | `make release` exists | Extend and verify clean Issue #34 release target |
| P08 | Seeds, solver/tolerances, hashes and number lineage | BASELINE_PASS | Existing registries and lock file | Preserve and extend for new outputs |

## Required deliverables

| ID | Deliverable | Status | Final path / evidence |
|---|---|---|---|
| D01 | `main_manuscript.tex` | PASS | `main_manuscript.tex` |
| D02 | `main_manuscript.pdf` | PASS | `main_manuscript.pdf` (20 pages) |
| D03 | `supplementary_information.tex` | PASS | `supplementary_information.tex` |
| D04 | `supplementary_information.pdf` | PASS | `supplementary_information.pdf` (7 pages) |
| D05 | `references.bib` | PASS | `references.bib` (31 DOI-verified scholarly/context records plus 5 official USDA/BLS URL-verified records) |
| D06 | `literature_registry.csv` | PASS | `literature_registry.csv` |
| D07 | `claim_reference_matrix.csv` | PASS | `claim_reference_matrix.csv` |
| D08 | `source_registry.csv` | PASS | `source_registry.csv` |
| D09 | `data_dictionary.md` | PASS | `data_dictionary.md` |
| D10 | `analysis_manifest.json` | PASS | `analysis_manifest.json` |
| D11 | Raw-data acquisition/import scripts | PASS | `scripts/download_official_data.py`; `scripts/fetch_goal17_census_geometry.py`; `empirical/src/crop_empirical/nass_summary.py` |
| D12 | Data-cleaning scripts | PASS | `scripts/process_official_data.py`; `empirical/src/crop_empirical/goal16_analysis.py` |
| D13 | Dependence-estimation scripts | PASS | `scripts/run_issue34_reconstruction.py`; `empirical/src/crop_empirical/empirical_dependence.py` |
| D14 | Optimization scripts | PASS | `scripts/run_issue34_reconstruction.py`; `optimization/src/crop_optimization/` |
| D15 | Empirical-analysis scripts | PASS | `scripts/run_goal16_empirical.py`; `empirical/src/crop_empirical/goal16_analysis.py` |
| D16 | Robustness-analysis scripts | PASS | `scripts/run_issue34_reconstruction.py`; `optimization/src/crop_optimization/robustness.py` |
| D17 | All figure-generation scripts | PASS | `scripts/make_issue34_figures.py` |
| D18 | All table-generation scripts | PASS | `scripts/render_issue34_manuscript_numbers.py`; source tables are solver/data-pipeline outputs |
| D19 | Source data for every figure | PASS | `figures/issue34/source_data/` |
| D20 | Source data for every table | PASS | `reconstruction/issue34/outputs/`; `empirical/goal16/outputs/` |
| D21 | `README_REPRODUCIBILITY.md` | PASS | `README_REPRODUCIBILITY.md` |
| D22 | `TEACHER_DRAFT_ALIGNMENT_AUDIT.md` | PASS | `TEACHER_DRAFT_ALIGNMENT_AUDIT.md` |
| D23 | `MATHEMATICAL_REPAIR_LOG.md` | PASS | `MATHEMATICAL_REPAIR_LOG.md` |
| D24 | `EXPERIMENT_RELIABILITY_AUDIT.md` | PASS | `EXPERIMENT_RELIABILITY_AUDIT.md` |
| D25 | `REFERENCE_RELIABILITY_AUDIT.md` | PASS | `REFERENCE_RELIABILITY_AUDIT.md` |
| D26 | `LIMITATIONS_AND_CLAIM_BOUNDARIES.md` | PASS | `LIMITATIONS_AND_CLAIM_BOUNDARIES.md` |
| D27 | Complete reproducible archive | PASS | `release/crop-ranking-reversal-issue36-reproducibility.tar.gz`; contents enumerated and extraction-readable |
| D28 | Archive SHA-256 | PASS | `release/crop-ranking-reversal-issue36-reproducibility.tar.gz.sha256`; verified after final archive construction |

## Final closure

Issue #34 closes with all research-direction, mathematical-validity,
numerical/empirical-evidence, presentation/reproducibility and delivery gates
satisfied.  The immutable Draft hashes remain unchanged.  The authoritative
end-to-end command `make issue36` completed successfully: 159 tests passed,
all registered output checksums verified, the main manuscript built to 20
pages, the supplement built to 7 pages, and the reproducibility archive
checksum verified.  Scientific limitations and items requiring supervisor
confirmation remain disclosed rather than being represented as resolved.

## Issue #36 authoritative repair addendum

Issue #36 supersedes any Issue #34 closure statement that conflicts with the
following verified repairs:

| Gate | Issue #36 result | Evidence |
|---|---|---|
| Supervisor strong-reversal definition | Strong means exclusion, \(s_i>s_j,\ x_i=0<x_j\); selected, possible and universal counts are all 0/165 | `SCIENTIFIC_CLAIM_REPAIR_AUDIT.md`; `reversal_phase_diagram.csv` |
| Complete versus strong | Principal Kansas solution is complete top-crop inversion, not strong reversal | `summary.json`; manuscript |
| Mechanism isolation | Primary inversion is margin-induced; separate risk path crosses with score and mean order preserved; full operational sequence is null and controlled cap path crosses | `MECHANISM_ISOLATION_AUDIT.md` |
| Diversification failure | Declared Gaussian benchmark strictly reduces variance but its allocation differs and fails the true-law CVaR ceiling | `DIVERSIFICATION_FAILURE_VALIDATION.md` |
| Information--flexibility | Option B: restricted theorem plus shared ex-ante-CVaR numerical cross-difference classification | `INFORMATION_FLEXIBILITY_VALIDATION.md` |
| Uncertainty | 62/64 pairwise frequency uses exact Clopper--Pearson 95% interval [0.891629, 0.996193] | `uncertainty_summary.csv`; Figure 6 |
| Presentation | Main manuscript 20 pages; supplement 7 pages; revised Figures 1--6 use the approved Issue #34 palette | final PDFs and page-QA audit |
| Release | Issue #36 deterministic archive and adjacent SHA-256 | `release/crop-ranking-reversal-issue36-reproducibility.tar.gz` |

The Issue #36 package is suitable for supervisor review, not represented as
publication-ready.  Its clean integration vehicle is a new Draft PR directly
to `main`; PRs #33 and #35 remain unmerged and are not automatic prerequisites.

## Legacy Issue #34 completion-report contract

The following 30-field contract documents the earlier Issue #34 handoff.  The
Issue #36 completion report supersedes it and additionally requires the repair
branch/commit, Draft PR/base, PR integration strategy, repaired classification
counts, three isolated mechanisms, exact diversification inequalities,
cross-difference results, exact binomial interval, revised page/figure counts,
all validation results, limitations, commands and release hash.

The final response must report, in exactly this order: (1) final research
question; (2) innovation chain; (3) preserved Draft components; (4) original
mathematical defects; (5) repairs; (6) new valid results; (7) datasets; (8)
coverage; (9) effective sample sizes; (10) principal numerical results; (11)
frontier results; (12) diversification failure; (13) information–flexibility;
(14) empirical findings; (15) robustness; (16) uncertainty; (17) reference
verification; (18) unverified claims; (19) limitations; (20) differences from
the corrective manuscript; (21) supervisor-confirmation items; (22) main page
count; (23) supplement page count; (24) delivery paths; (25) reproduction
commands; (26) branch; (27) commit; (28) repository status; (29) archive path;
and (30) archive SHA-256.
