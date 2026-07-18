"""Regression tests for the Issue #4 official-data contract."""

from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _rows(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_frozen_raw_snapshot_hashes_and_sizes():
    rows = _rows("data/raw_manifest.csv")
    assert len(rows) == 9
    for row in rows:
        path = ROOT / row["local_path"]
        assert path.stat().st_size == int(row["bytes"])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]


def test_downloader_default_is_verify_only_and_nonnetworked():
    result = subprocess.run(
        [sys.executable, "scripts/download_official_data.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "raw_snapshots=9 local_failures=0" in result.stdout


def test_panel_rebuild_is_byte_reproducible(tmp_path):
    rebuilt = tmp_path / "panel.csv"
    subprocess.run(
        [sys.executable, "scripts/process_official_data.py", "--output", str(rebuilt)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert rebuilt.read_bytes() == (ROOT / "data/processed/canonical_crop_year_panel.csv").read_bytes()


def test_panel_is_complete_balanced_and_unit_consistent():
    rows = _rows("data/processed/canonical_crop_year_panel.csv")
    assert len(rows) == 81
    assert {(row["crop"], row["year"]) for row in rows} == {
        (crop, str(year))
        for crop in ("corn", "soybeans", "wheat")
        for year in range(1998, 2025)
    }
    assert {row["geography"] for row in rows} == {"United States"}
    for row in rows:
        assert not any(value == "" for value in row.values())
        assert float(row["yield_bushels_per_planted_acre"]) > 0
        assert float(row["harvest_price_usd_per_bushel"]) > 0
        assert abs(
            float(row["dryland_share_percent"])
            + float(row["irrigated_share_percent"])
            - 100
        ) < 1e-9


def test_national_covariates_are_one_to_one_by_year():
    rows = _rows("data/processed/canonical_crop_year_panel.csv")
    for year in range(1998, 2025):
        current = [row for row in rows if row["year"] == str(year)]
        assert len({row["cpi_u_annual_index"] for row in current}) == 1
        assert len({row["annual_precipitation_inches"] for row in current}) == 1
        assert len({row["annual_mean_temperature_f"] for row in current}) == 1
    assert {
        row["cpi_u_deflator_to_2024"]
        for row in rows
        if row["year"] == "2024"
    } == {"1.000000"}


def test_source_registry_is_primary_agency_only_and_complete():
    rows = _rows("evidence_registry/data_source_registry.csv")
    assert len(rows) == 8
    assert all(row["official_url"].startswith("https://") for row in rows)
    assert all(".gov" in row["official_url"] for row in rows)
    required = {
        "owner", "documentation_url", "access_date", "version_or_release",
        "coverage", "unit_of_observation", "geography", "time_period", "variables",
        "units", "missing_codes", "revision_policy", "license_or_access", "status", "notes",
    }
    assert all(all(row[field] for field in required) for row in rows)


def test_unobserved_risk_and_farm_constraints_are_illustrative_only():
    rows = {row["parameter_id"]: row for row in _rows(
        "evidence_registry/parameter_provenance.csv"
    )}
    for parameter_id in (
        "P-SIM-001", "P-SIM-002", "P-SIM-003", "P-SIM-004", "P-CONSTRAINT-001"
    ):
        assert rows[parameter_id]["evidence_status"] == "ILLUSTRATIVE_ONLY"
    assert rows["P-MODEL-001"]["evidence_status"] == "MODEL_NORMALIZATION"
