#!/usr/bin/env python3
"""Issue #4 official-data, provenance, parameter, and panel acceptance gate."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


errors: list[str] = []
sources = rows("evidence_registry/data_source_registry.csv")
source_ids = [row["source_id"] for row in sources]
if len(source_ids) != len(set(source_ids)):
    errors.append("duplicate_source_id")

required_source_fields = {
    "source_id", "owner", "dataset_title", "official_url", "documentation_url",
    "access_date", "version_or_release", "coverage", "unit_of_observation",
    "geography", "time_period", "variables", "units", "missing_codes",
    "revision_policy", "license_or_access", "status", "notes",
}
for row in sources:
    for field in required_source_fields:
        if not row[field].strip():
            errors.append(f"source_blank:{row['source_id']}:{field}")
    if row["status"] != "REGISTERED_SPATIAL_EXTENSION_ONLY":
        if not row["raw_path"] or not row["sha256"]:
            errors.append(f"source_missing_snapshot:{row['source_id']}")

raw = rows("data/raw_manifest.csv")
raw_ids = [row["raw_id"] for row in raw]
if len(raw_ids) != len(set(raw_ids)):
    errors.append("duplicate_raw_id")
for row in raw:
    if row["source_id"] not in source_ids:
        errors.append(f"raw_unknown_source:{row['raw_id']}")
    path = ROOT / row["local_path"]
    if not path.is_file():
        errors.append(f"raw_missing:{row['raw_id']}")
        continue
    if path.stat().st_size != int(row["bytes"]):
        errors.append(f"raw_bytes:{row['raw_id']}")
    if digest(path) != row["sha256"]:
        errors.append(f"raw_hash:{row['raw_id']}")
    if row["overwrite_policy"] not in {
        "NEVER_OVERWRITE_STAGE_AND_REVIEW", "NEVER_OVERWRITE_NEW_RELEASE_NEW_RAW_ID"
    }:
        errors.append(f"raw_overwrite_policy:{row['raw_id']}")

panel = rows("data/processed/canonical_crop_year_panel.csv")
keys = [(row["crop"], row["year"]) for row in panel]
if len(panel) != 81 or len(keys) != len(set(keys)):
    errors.append(f"panel_cardinality:{len(panel)}:{len(set(keys))}")
if {row["crop"] for row in panel} != {"corn", "soybeans", "wheat"}:
    errors.append("panel_crop_set")
if {int(row["year"]) for row in panel} != set(range(1998, 2025)):
    errors.append("panel_year_set")
if {row["geography"] for row in panel} != {"United States"}:
    errors.append("panel_geography")
for row in panel:
    if any(value == "" for value in row.values()):
        errors.append(f"panel_missing:{row['crop']}:{row['year']}")
    if abs(float(row["dryland_share_percent"]) + float(row["irrigated_share_percent"]) - 100) > 1e-9:
        errors.append(f"practice_share:{row['crop']}:{row['year']}")
    if min(
        float(row["yield_bushels_per_planted_acre"]),
        float(row["harvest_price_usd_per_bushel"]),
        float(row["operating_cost_usd_per_planted_acre"]),
        float(row["total_cost_usd_per_planted_acre"]),
        float(row["cpi_u_annual_index"]),
    ) <= 0:
        errors.append(f"nonpositive_input:{row['crop']}:{row['year']}")

per_crop = Counter(row["crop"] for row in panel)
if set(per_crop.values()) != {27}:
    errors.append(f"unbalanced_panel:{dict(per_crop)}")

base_rows = [row for row in panel if row["year"] == "2024"]
if any(abs(float(row["cpi_u_deflator_to_2024"]) - 1) > 1e-6 for row in base_rows):
    errors.append("cpi_base_not_one")

parameters = rows("evidence_registry/parameter_provenance.csv")
parameter_ids = [row["parameter_id"] for row in parameters]
if len(parameter_ids) != len(set(parameter_ids)):
    errors.append("duplicate_parameter_id")
for row in parameters:
    if not row["evidence_status"] or not row["uncertainty_method"] or not row["notes"]:
        errors.append(f"parameter_incomplete:{row['parameter_id']}")
for parameter_id in {"P-SIM-001", "P-SIM-002", "P-SIM-003", "P-SIM-004", "P-CONSTRAINT-001"}:
    row = next((item for item in parameters if item["parameter_id"] == parameter_id), None)
    if not row or row["evidence_status"] != "ILLUSTRATIVE_ONLY":
        errors.append(f"unsupported_parameter_not_illustrative:{parameter_id}")

data_claims = [row for row in rows("evidence_registry/claims.csv") if row["claim_id"].startswith("DATA-C")]
if {row["claim_id"] for row in data_claims} != {f"DATA-C{i:02d}" for i in range(1, 6)}:
    errors.append("data_claim_set")
if any(row["qualification_required"] != "YES" for row in data_claims):
    errors.append("unqualified_data_claim")

required_docs = {
    "data/contracts/canonical_panel_specification.md",
    "data/contracts/data_dictionary.csv",
    "data/contracts/source_access_and_license.md",
    "audits/data_provenance_audit.md",
    "audits/geographic_temporal_alignment.md",
    "audits/issue_4_data_acceptance_report.md",
}
for relative in required_docs:
    if not (ROOT / relative).is_file():
        errors.append(f"missing_data_document:{relative}")

print(
    f"data_sources={len(sources)} raw_snapshots={len(raw)} panel_rows={len(panel)} "
    f"parameters={len(parameters)} data_claims={len(data_claims)} failures={len(errors)}"
)
for error in errors:
    print(error)
raise SystemExit(bool(errors))
