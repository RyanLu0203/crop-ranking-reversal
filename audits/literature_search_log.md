# Literature search and verification log

## Protocol

Search freeze: 2026-07-19

Scope: crop recommendation; crop and agricultural planning; stochastic programming; loss-CVaR; copulas and tail dependence; predictive-to-prescriptive and decision-focused learning; value of information; operational flexibility.

The teacher Draft and historical bibliographies were treated only as possible discovery leads. The canonical collection was rebuilt from structured metadata and full text.

### Source hierarchy

1. Crossref REST API for DOI-first structured discovery and metadata resolution.
2. Publisher full text or an author/institutional repository copy for content verification.
3. arXiv only for clearly labeled preprints or author versions subsequently matched to a journal DOI.
4. General web search only to locate publisher or repository full text.
5. Google Scholar snippets, blogs, Wikipedia, ResearchGate summaries, and AI summaries were not admitted as evidence.

The academic-search MCP endpoints named by the selected skill were not exposed in this session. The prescribed fallback was used: the official Crossref REST API plus direct full-text verification.

## Eligibility

Included records had to satisfy all of the following:

- directly support a paper claim, method choice, scope boundary, or novelty comparison;
- have a DOI or authoritative persistent identifier;
- have complete title, authorship, year, venue, and stable URL metadata;
- have full text inspected, not merely an abstract or search snippet;
- have a stated limitation preventing overgeneralization;
- not be retracted, replaced, or contradicted by a recorded correction as of the search freeze.

Excluded records were duplicates, non-scholarly summaries, inaccessible abstract-only records without an admissible repository copy, low-relevance applications, methodologically weak recommendation papers, or papers unable to support the intended claim.

## Search strings and captured records

Counts are result records actually captured for screening, not database-wide hit counts.

| ID | Source | Exact query or lookup strategy | Captured | Purpose |
|---|---|---|---:|---|
| Q01 | Crossref | crop planning conditional value at risk | 8 | Close CVaR crop-planning predecessors |
| Q02 | Crossref | crop planning stochastic programming agriculture | 8 | Agricultural planning and uncertainty |
| Q03 | Crossref | copula tail dependence portfolio CVaR | 8 | Dependence and tail-risk methods |
| Q04 | Crossref | predict then optimize prescriptive analytics | 8 | Prediction-to-decision literature |
| Q05 | Crossref | value of information decision analysis | 8 | Information-value foundations |
| Q06 | Crossref | operational flexibility uncertainty | 8 | Flexibility mechanisms |
| Q07 | Web to publisher/repository | crop planning CVaR stochastic programming agriculture portfolio DOI | 12 | Close-study expansion |
| Q08 | Web to publisher/repository | Decision-Focused Learning foundations state of the art DOI/full text | 7 | Recent review and citation chasing |
| Q09 | Web to publisher/repository | Value of Information Given Decision Flexibility full text | 6 | Information-flexibility interaction |
| Q10 | Web to institutional repository | exact-title searches for Filippi; Boyabatlı; Van Mieghem; Keisler | 9 | Legal full-text copies |
| Q11 | Publisher/reference chasing | references and related articles from included crop-planning and prescriptive papers | 17 | Backward and forward conceptual coverage |

Total captured records: 91. DOI normalization and title-plus-first-author matching removed 26 duplicates, leaving 65 unique records for title/abstract screening.

## Screening flow

| Stage | Records | Excluded at stage | Main reasons |
|---|---:|---:|---|
| Captured | 91 | 26 | DOI or normalized-title duplicates |
| Unique title/abstract screened | 65 | 34 | Off-topic; non-scholarly; weak venue; no claim-level role |
| Full text sought | 31 | 12 | Full text inaccessible; only snippet/abstract; method mismatch; version conflict unresolved |
| Canonical included | 19 | 0 | Full text and metadata verified |

The 19 included records comprise 3 theory foundations already verified in Issue #2 and 16 additions in Issue #3. Four additions are from 2022–2024, alongside foundational work from 1955 onward.

## Citation chasing

- Filippi et al. identified the closest direct CVaR crop-selection precedent and motivated searches for constrained crop rotation and dynamic allocation.
- Boyabatlı et al. and Benini et al. expanded operational-constraint coverage to rotation and multi-period allocation.
- Rockafellar and Uryasev anchored backward verification of the loss-CVaR formulation and atom-safe extension.
- Bertsimas and Kallus, Elmachtoub and Grigas, Wilder et al., and Mandi et al. established the prediction-to-decision branch.
- Keisler, Merkhofer, and Van Mieghem connected information value to available decisions and operational flexibility.
- Demarta and McNeil plus Ansari and Rockel constrained dependence statements to named families and verified orders.

## Retraction, correction, and version audit

Crossref metadata for every included DOI was checked for update-to, updated-by, and relation fields. No included item was marked retracted, withdrawn, or replaced. No correction changed a claim used here.

Version handling:

- Bertsimas–Kallus and Elmachtoub–Grigas use full author preprints for reading and final journal DOIs for citation.
- Mandi et al. remains explicitly labeled a preprint.
- Boyabatlı et al. uses the institutional submitted version matched to the final DOI.
- Merkhofer uses the 1975 DTIC report DOI; the later 1977 journal version was metadata-verified but is not a second canonical citation.
- Demarta–McNeil metadata was cross-checked against the ETH institutional record; the inspected full manuscript is the author version.

## Claims currently not writable

- “This is the first study” or “no prior study” is not admissible.
- A stronger lower-tail-dependence coefficient generally increases crop-portfolio CVaR or causes reversal is not admissible.
- Higher predictive accuracy necessarily improves acreage decisions is not admissible.
- Information and flexibility are generally strictly complementary is not admissible.
- Observed acreage reversal identifies farmer CVaR preferences is not admissible.

The defensible novelty wording is relational: among the included close studies, none jointly studies solution-set-aware reversal between an ordinal recommendation ranking and a constrained multi-crop loss-CVaR allocation while stress-testing named-family dependence and separating information from operational flexibility. This remains an inference from the bounded search, not a universal priority claim.

## Reproducibility

Automated validation is implemented in scripts/validate_literature_evidence.py. It checks registry completeness, DOI uniqueness, full-text status, claim mapping, BibTeX key/DOI alignment, and prohibited novelty wording.
