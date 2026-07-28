#!/usr/bin/env python3
"""Compare two isolated GOAL-15 runs byte for byte."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "empirical/stage_ii/outputs/reproducibility.json"


def hashes(directory: Path) -> dict[str, str]:
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(directory.iterdir()) if path.is_file()}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="crr-stageii-empirical-") as temp:
        base = Path(temp)
        runs = []
        for index in (1, 2):
            output = base / f"run-{index}"
            subprocess.run(
                [sys.executable, str(ROOT / "scripts/run_stage_ii_empirical.py"),
                 "--output-dir", str(output)], check=True, capture_output=True, text=True,
            )
            runs.append(hashes(output))
    names_match = set(runs[0]) == set(runs[1])
    mismatches = sorted(name for name in set(runs[0]) | set(runs[1])
                        if runs[0].get(name) != runs[1].get(name))
    result = {
        "status": "PASS" if names_match and not mismatches else "FAIL",
        "files_compared": len(runs[0]), "filename_sets_match": names_match,
        "mismatched_files": mismatches,
        "comparison": "two isolated admitted-panel-to-output executions",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksum = OUTPUT.parent / "SHA256SUMS.txt"
    checksum.write_text("".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
        for path in sorted(OUTPUT.parent.iterdir())
        if path.is_file() and path != checksum and path.name != "validation_report.json"
    ), encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
