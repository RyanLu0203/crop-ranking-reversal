#!/usr/bin/env python3
"""Measure isolated peak memory for representative audited formal cells."""

from __future__ import annotations

import json
import multiprocessing as mp
import platform
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "simulation/src"), str(ROOT / "optimization/src")]

from crop_simulation.experiment_design import expand_design, load_experiment_design  # noqa: E402
from crop_simulation.formal_experiment import json_ready, run_replication  # noqa: E402


def _measure(cell: dict, connection) -> None:
    started = time.perf_counter()
    result, _ = run_replication(cell, 2026071901, 10000, audit_face=True)
    raw_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_bytes = int(raw_peak if sys.platform == "darwin" else raw_peak * 1024)
    connection.send({
        "cell_id": cell["cell_id"],
        "status": result["solver_status"],
        "face_status": result["face_status"],
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": peak_bytes,
        "peak_rss_gb": peak_bytes / 1_000_000_000.0,
        "resource_cap_gb": 0.5,
        "resource_cap_pass": peak_bytes <= 500_000_000,
    })
    connection.close()


def main() -> int:
    design = load_experiment_design()
    cells = expand_design(design).set_index("cell_id")
    context = mp.get_context("spawn")
    rows = []
    for cell_id in ("ANCHOR-001", "ANCHOR-009", "ANCHOR-012"):
        cell = cells.loc[cell_id].to_dict()
        cell["cell_id"] = cell_id
        parent, child = context.Pipe(duplex=False)
        process = context.Process(target=_measure, args=(cell, child))
        process.start()
        rows.append(parent.recv())
        process.join()
        if process.exitcode != 0:
            raise RuntimeError(f"resource audit child failed for {cell_id}")
    output = {
        "status": "PASS" if all(row["resource_cap_pass"] for row in rows) else "FAIL",
        "platform": platform.platform(),
        "measurement": "isolated process ru_maxrss",
        "representative_cells": rows,
        "maximum_peak_rss_bytes": max(row["peak_rss_bytes"] for row in rows),
        "maximum_peak_rss_gb": max(row["peak_rss_gb"] for row in rows),
        "frozen_cap_gb": 0.5,
    }
    path = ROOT / "simulation/outputs/resource_audit.json"
    path.write_text(json.dumps(json_ready(output), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(json_ready(output), sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
