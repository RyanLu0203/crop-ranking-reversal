#!/usr/bin/env python3
"""Refresh the aggregate Stage-I figure ledger after versioned figure builds."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    figures = ROOT / "figures"
    paths = sorted(
        path for path in figures.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS"
    )
    ledger = "".join(f"{sha(path)}  {path.relative_to(ROOT)}\n" for path in paths)
    (figures / "SHA256SUMS").write_text(ledger, encoding="utf-8")
    print(f"aggregate_figure_checksums={len(paths)}")


if __name__ == "__main__":
    main()

