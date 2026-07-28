#!/usr/bin/env python3
"""Acceptance gate for Issue #3 literature and citation governance."""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "evidence_registry/literature_registry.csv"
CLAIMS = ROOT / "evidence_registry/claims.csv"
QUALITY = ROOT / "audits/literature_quality_matrix.csv"
NOVELTY = ROOT / "audits/novelty_comparison_matrix.csv"
METADATA_AUDIT = ROOT / "audits/citation_metadata_audit.csv"
BIB = ROOT / "references.bib"
ISSUE34_REGISTRY = ROOT / "literature_registry.csv"
REQUIRED = {
    REGISTRY,
    CLAIMS,
    QUALITY,
    NOVELTY,
    METADATA_AUDIT,
    BIB,
    ISSUE34_REGISTRY,
    ROOT / "audits/literature_search_log.md",
    ROOT / "literature/annotated_synthesis.md",
}
REQUIRED_DOMAINS = {
    "Crop planning",
    "Agricultural prediction",
    "Stochastic programming",
    "CVaR optimization",
    "Copula tail dependence",
    "Prescriptive analytics",
    "Decision-focused learning",
    "Value of information",
    "Value of information and flexibility",
    "Operational flexibility",
}
DOI = re.compile(r"^10\.\S+$", re.IGNORECASE)
OFFICIAL_WITHOUT_DOI = {
    "bls2026cpi",
    "usdaers2026costs",
    "usdanass2019crop",
    "usdanass2022crop",
    "usdanass2025crop",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_bibtex(text: str) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    position = 0
    start_pattern = re.compile(r"@([A-Za-z]+)\s*\{\s*([^,\s]+)\s*,")
    field_pattern = re.compile(
        r"(?ms)^\s*([A-Za-z][A-Za-z0-9_-]*)\s*=\s*\{(.*?)\}\s*,?\s*$"
    )
    while match := start_pattern.search(text, position):
        entry_type, key = match.group(1).lower(), match.group(2)
        depth = 1
        cursor = match.end()
        while cursor < len(text) and depth:
            if text[cursor] == "{":
                depth += 1
            elif text[cursor] == "}":
                depth -= 1
            cursor += 1
        if depth:
            raise ValueError(f"unbalanced_bibtex:{key}")
        body = text[match.end(): cursor - 1]
        fields = {name.lower(): value.strip() for name, value in field_pattern.findall(body)}
        fields["_type"] = entry_type
        entries[key] = fields
        position = cursor
    return entries


errors: list[str] = []
for path in sorted(REQUIRED):
    if not path.is_file():
        errors.append(f"missing:{path.relative_to(ROOT)}")

registry = read_rows(REGISTRY)
issue34_registry = read_rows(ISSUE34_REGISTRY)
quality = read_rows(QUALITY)
claims = read_rows(CLAIMS)
included = [row for row in quality if row["included"] == "YES"]
excluded = [row for row in quality if row["included"] == "NO"]

ids = [row["reference_id"] for row in registry]
if len(ids) != len(set(ids)):
    errors.append("duplicate_reference_id")
dois = [row["doi"].lower() for row in registry]
if len(dois) != len(set(dois)):
    errors.append("duplicate_registry_doi")

required_fields = {
    "title", "authors", "year", "journal_or_publisher", "doi",
    "official_full_text_url_or_repository", "verification_date",
    "manuscript_claims_supported", "limitations", "citation_status",
}
for row in registry:
    for field in required_fields:
        if not row[field].strip():
            errors.append(f"empty_registry_field:{row['reference_id']}:{field}")
    if row["full_text_verified"] != "YES":
        errors.append(f"full_text_not_verified:{row['reference_id']}")
    if row["verification_date"] != "2026-07-19":
        errors.append(f"unexpected_verification_date:{row['reference_id']}")
    if not DOI.fullmatch(row["doi"]):
        errors.append(f"invalid_doi:{row['reference_id']}")

domains = {row["research_domain"] for row in registry}
for domain in sorted(REQUIRED_DOMAINS - domains):
    errors.append(f"missing_domain:{domain}")

quality_ids = {row["record_id"] for row in included}
if quality_ids != set(ids):
    errors.append("quality_matrix_included_set_mismatch")
if len(excluded) < 10:
    errors.append("insufficient_exclusion_audit")
for row in excluded:
    if not row["exclusion_reason"].strip():
        errors.append(f"missing_exclusion_reason:{row['record_id']}")

claim_rows = [row for row in claims if row["claim_id"].startswith("LIT-C")]
if {row["claim_id"] for row in claim_rows} != {f"LIT-C{i:02d}" for i in range(1, 12)}:
    errors.append("literature_claim_set_must_be_LIT_C01_C11")
for row in claim_rows:
    if row["manuscript_admissible"] != "YES":
        errors.append(f"claim_not_admissible:{row['claim_id']}")
    if not row["supporting_assets"].strip():
        errors.append(f"claim_without_source:{row['claim_id']}")

try:
    bib_entries = parse_bibtex(BIB.read_text(encoding="utf-8"))
except ValueError as exc:
    errors.append(str(exc))
    bib_entries = {}
bib_keys = list(bib_entries)
scholarly_keys = [key for key in bib_keys if key not in OFFICIAL_WITHOUT_DOI]
official_keys = [key for key in bib_keys if key in OFFICIAL_WITHOUT_DOI]
if (
    scholarly_keys != sorted(scholarly_keys)
    or official_keys != sorted(official_keys)
    or bib_keys != scholarly_keys + official_keys
):
    errors.append("bibtex_keys_not_sorted_by_scholarly_then_official")
if len(bib_keys) != len(set(bib_keys)):
    errors.append("duplicate_bibtex_key")

quality_keys = {row["citation_key"] for row in included}
if not quality_keys.issubset(bib_keys):
    errors.append("bibtex_quality_key_mismatch")
registry_dois = {doi.lower() for doi in dois}
bib_dois: set[str] = set()
for key, fields in bib_entries.items():
    required = {"author", "title", "year"}
    if fields.get("_type") == "article":
        required.add("journal")
    elif fields.get("_type") == "inproceedings":
        required.add("booktitle")
    elif fields.get("_type") == "techreport":
        required.add("institution")
    missing = required - fields.keys()
    if missing:
        errors.append(f"bibtex_missing:{key}:{','.join(sorted(missing))}")
    doi = fields.get("doi", "").lower()
    if key in OFFICIAL_WITHOUT_DOI:
        if doi:
            errors.append(f"official_source_should_not_invent_doi:{key}")
        if not fields.get("url", "").startswith("https://"):
            errors.append(f"official_source_missing_https_url:{key}")
    else:
        if not DOI.fullmatch(doi):
            errors.append(f"bibtex_invalid_doi:{key}")
        bib_dois.add(doi)
if not registry_dois.issubset(bib_dois):
    errors.append("bibtex_registry_doi_mismatch")

# Issue #3's 19-record registry remains a strict canonical subset.  Later
# manuscript extensions must be registered separately rather than weakening
# that historical gate.  Issue #34 registers every canonical and added entry,
# so the full bibliography must match its key/DOI mapping exactly.
issue34_keys = [row["citation_key"] for row in issue34_registry]
if len(issue34_keys) != len(set(issue34_keys)):
    errors.append("duplicate_issue34_citation_key")
issue34_by_key = {row["citation_key"]: row for row in issue34_registry}
if set(bib_keys) != set(issue34_by_key):
    errors.append("bibtex_issue34_registry_key_mismatch")
for key, row in issue34_by_key.items():
    doi = row["doi"].lower()
    if row["verified_2026_07_27"] != "YES":
        errors.append(f"issue34_reference_not_verified:{key}")
    if key in OFFICIAL_WITHOUT_DOI:
        if doi:
            errors.append(f"official_registry_should_not_invent_doi:{key}")
        if not row["verification_source"].startswith("https://"):
            errors.append(f"official_registry_missing_https_url:{key}")
    elif not DOI.fullmatch(doi):
        errors.append(f"invalid_issue34_doi:{key}")
    if key in bib_entries and bib_entries[key].get("doi", "").lower() != doi:
        errors.append(f"bibtex_issue34_doi_mismatch:{key}")

novelty = read_rows(NOVELTY)
if not any(row["study_id"] == "PROPOSED_PAPER" for row in novelty):
    errors.append("missing_proposed_paper_novelty_row")
if not any(row["citation_key"] == "filippi2017mixed" for row in novelty):
    errors.append("missing_closest_crop_cvar_predecessor")

metadata_audit = read_rows(METADATA_AUDIT)
if {row["reference_id"] for row in metadata_audit} != set(ids):
    errors.append("metadata_audit_reference_set_mismatch")
for row in metadata_audit:
    if not row["verification_status"].startswith("VERIFIED"):
        errors.append(f"metadata_not_verified:{row['reference_id']}")
    if row["update_or_correction_relation"] != "NONE":
        errors.append(f"unresolved_update_relation:{row['reference_id']}")

print(
    f"canonical_references={len(registry)} included_quality={len(included)} "
    f"excluded_quality={len(excluded)} literature_claims={len(claim_rows)} "
    f"bibtex_entries={len(bib_entries)} issue34_registry={len(issue34_registry)} "
    f"metadata_audits={len(metadata_audit)} "
    f"failures={len(errors)}"
)
for error in errors:
    print(error)
raise SystemExit(bool(errors))
