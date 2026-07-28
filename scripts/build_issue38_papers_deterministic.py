#!/usr/bin/env python3
"""Build both academic PDFs twice and require byte-identical outputs."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = ("main_manuscript", "supplementary_information")
REPORT = ROOT / "audits" / "issue38_deterministic_build.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_once() -> dict[str, str]:
    environment = dict(os.environ)
    environment.setdefault("SOURCE_DATE_EPOCH", "1785081600")
    for document in DOCUMENTS:
        subprocess.run(
            ["latexmk", "-norc", "-C", f"{document}.tex"],
            cwd=ROOT,
            env=environment,
            check=True,
        )
        subprocess.run(
            [
                "latexmk", "-norc", "-pdf", "-interaction=nonstopmode",
                "-halt-on-error", f"{document}.tex",
            ],
            cwd=ROOT,
            env=environment,
            check=True,
        )
    return {
        f"{document}.pdf": digest(ROOT / f"{document}.pdf")
        for document in DOCUMENTS
    }


def main() -> None:
    first = build_once()
    second = build_once()
    assert first == second, {"first": first, "second": second}
    report = {
        "status": "PASS",
        "source_date_epoch": os.environ.get("SOURCE_DATE_EPOCH", "1785081600"),
        "first_build_sha256": first,
        "second_build_sha256": second,
        "byte_identical": True,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
