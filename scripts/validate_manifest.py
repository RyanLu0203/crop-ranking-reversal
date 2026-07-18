#!/usr/bin/env python3
"""Verify canonical manifest and checksum ledger against repository bytes."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "provenance/canonical_asset_manifest.csv"
CHECKSUMS = ROOT / "provenance/checksums/canonical_SHA256SUMS.txt"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


errors: list[str] = []
if not MANIFEST.is_file() or not CHECKSUMS.is_file():
    errors.append("missing_manifest_or_checksums")
    rows = []
    checksum_lines = []
else:
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    checksum_lines = CHECKSUMS.read_text(encoding="utf-8").splitlines()

for row in rows:
    path = ROOT / row["canonical_path"]
    actual = digest(path) if path.is_file() else "MISSING"
    if actual != row["sha256"]:
        errors.append(f"manifest_mismatch:{row['canonical_path']}")

for line in checksum_lines:
    try:
        expected, relative = line.split("  ", 1)
    except ValueError:
        errors.append(f"malformed_checksum_line:{line}")
        continue
    path = ROOT / relative
    actual = digest(path) if path.is_file() else "MISSING"
    if actual != expected:
        errors.append(f"checksum_mismatch:{relative}")

print(f"manifest_rows={len(rows)} checksum_rows={len(checksum_lines)} failures={len(errors)}")
for error in errors:
    print(error)
raise SystemExit(bool(errors))
