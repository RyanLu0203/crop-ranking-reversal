# Issue #3 literature acceptance report

Date: 2026-07-19

Branch: codex/issue-3-literature-evidence

Issue: https://github.com/RyanLu0203/crop-ranking-reversal/issues/3

## Search and screening

- Captured discovery records: 91
- Unique records after DOI and title/author deduplication: 65
- Full texts sought: 31
- Canonical included: 19
- Excluded at full-text stage: 12
- Unresolved full-text access among canonical references: 0

Search strings, source routing, screening rules, citation chasing, and version handling are recorded in audits/literature_search_log.md.

## Canonical evidence

The 19-reference registry covers:

- agricultural prediction and crop recommendation context;
- constrained crop and rotation planning;
- stochastic-program decision timing;
- loss-CVaR and finite-scenario optimization;
- named-family copulas and tail dependence;
- predictive-to-prescriptive and decision-focused learning;
- value of information; and
- operational flexibility.

Every canonical row has complete authorship, title, year, venue, DOI, authoritative full-text location, verification date, supported claim, limitations, and citation role. All have full_text_verified=YES.

## Claim and novelty governance

Eleven literature claims LIT-C01–LIT-C11 are mapped to sources and carry required qualifications. The novelty matrix compares the proposed paper with 11 literature rows plus the proposed integration.

Filippi et al. (2017) is the closest included method predecessor because it combines crop selection, stochastic profit, operational constraints, and CVaR. It does not analyze ordinal recommendation rankings, entire optimal-solution sets, possible/universal/selected reversal, copula-tail stress, or information value.

The permitted contribution wording is bounded: the proposed integration differs from the included close studies by jointly analyzing these elements. “First study” and “no prior study” remain prohibited.

## Metadata, corrections, and versions

The 19-row citation metadata audit records title, author, year, full-text version, and Crossref/DataCite/DTIC authority. No canonical DOI has an adverse update, retraction, withdrawal, or unresolved correction relation.

Two benign version notes are explicit:

- Demarta–McNeil is cited by its 2005 issue year although Crossref also records later online publication metadata.
- Bertsimas–Kallus is cited by its 2020 journal issue; the inspected author preprint predates final publication.

Mandi et al. is explicitly retained as a preprint and quality grade B.

## Validation

Literature gate:

    uv run --python 3.11 python scripts/validate_literature_evidence.py

Result:

    canonical_references=19 included_quality=19 excluded_quality=12 literature_claims=11 bibtex_entries=19 metadata_audits=19 failures=0

BibTeX data-model validation:

    biber --tool --validate-datamodel --output-format=bibtex --output-file=/tmp/references-validated.bib references.bib

Result: validation complete with no data-model error.

Repository-wide tests:

    uv run --python 3.11 pytest -q

Result: 75 passed, 0 failed.

## Claims deliberately left unavailable

- general monotonic effects of a lower-tail coefficient;
- general unique reversal thresholds;
- general strict information–flexibility complementarity;
- predictive accuracy as proof of allocation quality;
- observed reversal as identification of risk preferences; and
- universal priority or first-study claims.

These exclusions are scientific boundaries, not missing deliverables.
