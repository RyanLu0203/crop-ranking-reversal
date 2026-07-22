#!/usr/bin/env python3
"""Build the canonical repository asset manifest and checksum ledger."""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "provenance/canonical_asset_manifest.csv"
CHECKSUMS = ROOT / "provenance/checksums/canonical_SHA256SUMS.txt"
EXCLUDED_NAMES = {
    MANIFEST.name,
    CHECKSUMS.name,
    ".DS_Store",
    # The deterministic delivery archive contains a snapshot of canonical
    # assets and therefore has its own checksum; including it here would make
    # the repository manifest self-referential after every package rebuild.
    "stage_ii_final_scientific_package.zip",
    "stage_ii_final_scientific_package.zip.sha256",
}
EXCLUDED_TOP_LEVEL = {"build", "dist", "scratch", "tmp"}
SYNC_COLLISION = re.compile(r" \d+$")


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return (
        path.is_file()
        and relative.parts[0] not in EXCLUDED_TOP_LEVEL
        and ".git" not in relative.parts
        and ".venv" not in relative.parts
        and not any(part.endswith(".egg-info") for part in relative.parts)
        and "__pycache__" not in relative.parts
        and ".pytest_cache" not in relative.parts
        and path.name not in EXCLUDED_NAMES
        and not SYNC_COLLISION.search(path.stem)
        and path.suffix != ".pyc"
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    files = sorted(path for path in ROOT.rglob("*") if included(path))
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["canonical_path", "asset_type", "sha256", "bytes", "evidence_role", "manuscript_admissible"],
            lineterminator="\n",
        )
        writer.writeheader()
        for path in files:
            relative = path.relative_to(ROOT).as_posix()
            role = "architecture_baseline" if relative.startswith("baselines/") else "component_or_governance"
            writer.writerow({
                "canonical_path": relative,
                "asset_type": path.suffix.lstrip(".") or "text",
                "sha256": digest(path),
                "bytes": path.stat().st_size,
                "evidence_role": role,
                "manuscript_admissible": "NO",
            })

    checksum_files = [*files, MANIFEST]
    CHECKSUMS.write_text(
        "".join(f"{digest(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in sorted(checksum_files)),
        encoding="utf-8",
    )
    print(f"manifest_rows={len(files)} checksum_rows={len(checksum_files)}")


if __name__ == "__main__":
    main()
