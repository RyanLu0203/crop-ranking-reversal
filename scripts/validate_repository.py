#!/usr/bin/env python3
"""Issue #1 repository, evidence, baseline, secret, and portability gate."""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DIRS = {
    "baselines", "manuscript", "theory", "literature", "data", "simulation",
    "optimization", "empirical", "visualization", "figures", "tables",
    "supplementary", "evidence_registry", "audits", "provenance",
}
BASELINE_HASHES = {
    "baselines/teacher_draft/Crop_ranking_reversal_total.tex": "e8885aa89be6a6010f0d3e6f8e40b4b8192a91fc90f6ca4fb16ae9b0aa9dd26c",
    "baselines/teacher_draft/Crop_ranking_reversal_total.pdf": "52ac1b4ef21c8d406fd6d722c877935a24d2cc6ea68520a6f35470ba8b334b44",
}
REGISTRY_SCHEMAS = {
    "evidence_registry/claims.csv": {"claim_id", "claim_summary", "status", "manuscript_admissible"},
    "evidence_registry/numbers.csv": {"number_id", "displayed_value", "output_field", "checksum", "verification_status"},
    "evidence_registry/assets.csv": {"asset_id", "canonical_path", "admissibility_status", "limitations"},
}
RUNTIME_SUFFIXES = {".py", ".yaml", ".yml", ".toml", ".sh"}
SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    "github_token": re.compile(r"gh[opsu]_[A-Za-z0-9]{20,}"),
    "aws_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "credential_assignment": re.compile(r"(?i)(?:api[_-]?key|secret|password|access[_-]?token)\s*[:=]\s*['\"][^'\"]{8,}"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iter_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or ".venv" in path.parts:
            continue
        if path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".parquet", ".lock"}:
            continue
        yield path


errors: list[str] = []

for directory in sorted(REQUIRED_DIRS):
    if not (ROOT / directory).is_dir():
        errors.append(f"missing_directory:{directory}")

for relative, expected in BASELINE_HASHES.items():
    path = ROOT / relative
    actual = sha256(path) if path.is_file() else "MISSING"
    if actual != expected:
        errors.append(f"baseline_hash:{relative}:{actual}")

for relative, expected_fields in REGISTRY_SCHEMAS.items():
    path = ROOT / relative
    if not path.is_file():
        errors.append(f"missing_registry:{relative}")
        continue
    with path.open(newline="", encoding="utf-8") as handle:
        header = set(next(csv.reader(handle)))
    missing = expected_fields - header
    if missing:
        errors.append(f"registry_schema:{relative}:{','.join(sorted(missing))}")

matrix_path = ROOT / "audits/draft_content_completion_matrix.csv"
if not matrix_path.is_file():
    errors.append("missing_completion_matrix")
    matrix_rows = []
else:
    with matrix_path.open(newline="", encoding="utf-8") as handle:
        matrix_rows = list(csv.DictReader(handle))
    ids = [row["content_id"] for row in matrix_rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_completion_matrix_id")
    for row in matrix_rows:
        if not row["canonical_disposition"].strip():
            errors.append(f"unmapped_disposition:{row['content_id']}")
        if not row["target_issue_ids"].strip() and row["supervisor_confirmation_required"] != "YES":
            errors.append(f"unmapped_issue:{row['content_id']}")

for path in iter_text_files():
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    relative = path.relative_to(ROOT).as_posix()
    for label, pattern in SECRET_PATTERNS.items():
        if pattern.search(text):
            errors.append(f"secret_scan:{label}:{relative}")
    if path.suffix.lower() in RUNTIME_SUFFIXES or path.name == "Makefile":
        unix_user_roots = ("/" + "Users/", "/" + "home/")
        windows_user_root = "\\\\" + "Users\\\\"
        if any(marker in text for marker in (*unix_user_roots, windows_user_root)):
            errors.append(f"absolute_runtime_path:{relative}")

print(
    f"required_directories={len(REQUIRED_DIRS)} "
    f"draft_matrix_rows={len(matrix_rows)} "
    f"baseline_files={len(BASELINE_HASHES)} failures={len(errors)}"
)
for error in errors:
    print(error)
raise SystemExit(bool(errors))
