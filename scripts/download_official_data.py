#!/usr/bin/env python3
"""Verify frozen Issue #4 raw bytes or stage agency downloads without overwrite.

The canonical raw directory is immutable.  A live endpoint may be revised, so
network downloads are written only to an explicit staging directory and are
compared with the recorded snapshot.  This script never overwrites canonical
raw data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/raw_manifest.csv"
USER_AGENT = "crop-ranking-reversal-research/1.0 (official-data audit)"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> list[dict[str, str]]:
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verify_local(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    for row in rows:
        path = ROOT / row["local_path"]
        if not path.is_file():
            errors.append(f"missing:{row['raw_id']}")
            continue
        if path.stat().st_size != int(row["bytes"]):
            errors.append(f"bytes:{row['raw_id']}:{path.stat().st_size}")
        actual = sha256(path)
        if actual != row["sha256"]:
            errors.append(f"sha256:{row['raw_id']}:{actual}")
    return errors


def build_request(row: dict[str, str]) -> urllib.request.Request:
    payload = row["request_body"].encode("utf-8") if row["request_body"] else None
    headers = {"User-Agent": USER_AGENT}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    return urllib.request.Request(
        row["url"], data=payload, headers=headers, method=row["method"]
    )


def stage_downloads(rows: list[dict[str, str]], stage: Path) -> list[str]:
    stage.mkdir(parents=True, exist_ok=True)
    drift: list[str] = []
    for row in rows:
        request = build_request(row)
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read()
        target = stage / Path(row["local_path"]).name
        target.write_bytes(body)
        actual = hashlib.sha256(body).hexdigest()
        state = "MATCH" if actual == row["sha256"] else "REVISION_DETECTED"
        print(f"{row['raw_id']} {state} bytes={len(body)} sha256={actual}")
        if state != "MATCH":
            drift.append(row["raw_id"])
    return drift


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        type=Path,
        help="download to this noncanonical directory and compare with frozen hashes",
    )
    parser.add_argument(
        "--print-requests",
        action="store_true",
        help="print method and URL without network access",
    )
    args = parser.parse_args()
    rows = load_manifest()
    errors = verify_local(rows)
    print(f"raw_snapshots={len(rows)} local_failures={len(errors)}")
    for error in errors:
        print(error)
    if errors:
        return 1
    if args.print_requests:
        for row in rows:
            print(f"{row['raw_id']} {row['method']} {row['url']}")
    if args.stage:
        stage = args.stage.resolve()
        canonical = (ROOT / "data/raw").resolve()
        if stage == canonical or canonical in stage.parents:
            print("refusing_to_stage_inside_canonical_raw_directory")
            return 2
        drift = stage_downloads(rows, stage)
        if drift:
            print("review_required=" + ",".join(drift))
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
