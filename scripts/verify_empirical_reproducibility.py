#!/usr/bin/env python3
"""Run the empirical pipeline twice in isolated directories and compare bytes."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "empirical/outputs/reproducibility.json"


def hashes(directory: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.iterdir())
        if path.is_file()
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="crr-empirical-replay-") as temp:
        base = Path(temp)
        runs = []
        for index in (1, 2):
            output = base / f"outputs-{index}"
            command = [
                sys.executable, str(ROOT / "scripts/run_empirical_analysis.py"),
                "--output-dir", str(output),
                "--nass-processed", str(base / f"nass-{index}.csv"),
                "--analysis-panel", str(base / f"analysis-{index}.csv"),
                "--national-panel", str(base / f"national-{index}.csv"),
                "--skip-official-validation",
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            run_hashes = hashes(output)
            for label in ("nass", "analysis", "national"):
                path = base / f"{label}-{index}.csv"
                run_hashes[f"processed_{label}.csv"] = hashlib.sha256(path.read_bytes()).hexdigest()
            runs.append(run_hashes)
        names_match = set(runs[0]) == set(runs[1])
        mismatches = sorted(name for name in set(runs[0]) | set(runs[1]) if runs[0].get(name) != runs[1].get(name))
    result = {
        "status": "PASS" if names_match and not mismatches else "FAIL",
        "files_compared": len(runs[0]),
        "filename_sets_match": names_match,
        "mismatched_files": mismatches,
        "comparison": "two isolated complete raw-to-analysis executions",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksum_path = OUTPUT.parent / "SHA256SUMS.txt"
    checksum_lines = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
        for path in sorted(OUTPUT.parent.iterdir())
        if path.is_file() and path.name != checksum_path.name
    ]
    checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
