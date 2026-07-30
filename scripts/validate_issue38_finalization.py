#!/usr/bin/env python3
"""Validate the scientific-finalization outputs and compiled-paper cleanroom."""

from __future__ import annotations

import json
from pathlib import Path
import re

import numpy as np
import pandas as pd
from pypdf import PdfReader
import yaml


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reconstruction" / "issue34" / "outputs"
REPORT = ROOT / "audits" / "issue38_manuscript_language_scan.json"
BASELINE = "d058f0764e42e994bf2c1c00b48cbde3622f96c6"
PDFS = [ROOT / "main_manuscript.pdf", ROOT / "supplementary_information.pdf"]
FORBIDDEN = {
    "issue": r"\bissue(?:s)?\b",
    "goal": r"\bgoal(?:s)?\b",
    "prompt": r"\bprompt(?:s)?\b",
    "codex": r"\bcodex\b",
    "agent": r"\bagent(?:s)?\b",
    "scheduler": r"\bscheduler\b",
    "github": r"\bgithub\b",
    "pull request": r"\bpull request(?:s)?\b",
    "PR": r"\bPR\s*#?\d+\b",
    "branch": r"\bbranch(?:es)?\b",
    "commit": r"\bcommit(?:s|ted|ting)?\b",
    "merge": r"\bmerg(?:e|ed|ing)\b",
    "supervisor draft": r"\bsupervisor\s+draft\b",
    "teacher draft": r"\bteacher\s+draft\b",
    "repository": r"\brepositor(?:y|ies)\b",
    "pipeline": r"\bpipeline(?:s)?\b",
    "validator": r"\bvalidator(?:s)?\b",
    "acceptance matrix": r"\bacceptance\s+matrix\b",
    "audit log": r"\baudit\s+log\b",
    "repair log": r"\brepair\s+log\b",
    "manifest": r"\bmanifest(?:s)?\b",
    "checksum": r"\bchecksum(?:s)?\b",
    "SHA-256": r"\bSHA-?256\b",
    "script path": r"\bscripts?/",
    "build command": r"\bmake\s+(?:reproduce|validate|paper)\b",
    "repository-registered": r"\brepository[- ]registered\b",
    "frozen before results": r"\bfrozen\s+before\s+results\b",
    "true law": r"\btrue[- ]law\b",
}


def pdf_text(pdf: Path) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(pdf).pages)


def validate_diversification() -> dict[str, object]:
    frame = pd.read_csv(OUTPUT / "diversification_failure.csv")
    frontier = frame.loc[frame["row_type"].eq("mean_variance_frontier")].sort_values(
        "gamma"
    )
    selected = frame.loc[
        frame["policy"].eq("xMV_variance_target_selected")
    ].iloc[0]
    tail = frame.loc[
        frame["policy"].eq("xT_CVaR_under_student_t_evaluation")
    ].iloc[0]
    assert len(frontier) == 301
    assert np.allclose(frontier["gamma"], np.arange(301) / 10000)
    assert frontier["policy_solver_generated"].all()
    assert frontier["solver_status"].eq("optimal").all()
    assert frontier["feasibility_max_violation"].max() <= 1e-7
    assert frontier["full_investment_residual"].abs().max() <= 1e-7
    assert selected["selection_rule"] == (
        "smallest_gamma_achieving_fixed_gaussian_variance_reduction"
    )
    assert bool(selected["selected_gamma_is_interior"])
    assert bool(selected["strong_diversification_failure"])
    assert bool(selected["tail_and_ceiling_conditions_numerically_dependent"])
    assert selected["xMV_vs_xT_allocation_L1"] > 0.01
    assert selected["evaluation_loss_CVaR"] > tail["evaluation_loss_CVaR"] + 1e-6
    assert selected["evaluation_loss_CVaR"] > selected["risk_ceiling"] + 1e-6
    sensitivity = pd.read_csv(OUTPUT / "diversification_sensitivity.csv")
    required = {
        "baseline", "scenario_count", "seed", "kendall_tau",
        "student_t_copula_df", "cvar_alpha", "risk_ceiling_path",
        "evaluation_marginal", "selection_target",
    }
    assert required <= set(sensitivity["varied_factor"])
    return {
        "frontier_points": len(frontier),
        "selected_gamma": float(selected["gamma"]),
        "weak_interval": selected["weak_failure_gamma_intervals"],
        "strong_interval": selected["strong_failure_gamma_intervals"],
        "sensitivity_cases": len(sensitivity),
        "sensitivity_weak_cases": int(
            sensitivity["selected_weak_failure"].sum()
        ),
        "sensitivity_strong_cases": int(
            sensitivity["selected_strong_failure"].sum()
        ),
    }


def validate_risk_map() -> dict[str, int]:
    frame = pd.read_csv(OUTPUT / "risk_shock_sensitivity.csv")
    assert len(frame) == 49
    assert frame["mean_preservation_error"].abs().max() <= 1e-9
    assert set(frame["classification"]) <= {
        "crossing", "no_crossing", "infeasible"
    }
    focal = frame.loc[frame["focal_case"]]
    assert len(focal) == 1 and focal.iloc[0]["classification"] == "crossing"
    return {
        label: int(frame["classification"].eq(label).sum())
        for label in ("crossing", "no_crossing", "infeasible")
    }


def main() -> None:
    design = yaml.safe_load(
        (ROOT / "simulation" / "configs" / "issue34_full_model_design.yaml")
        .read_text(encoding="utf-8")
    )
    assert design["finalization_baseline_commit"] == BASELINE
    scans: dict[str, dict[str, list[str]]] = {}
    for pdf in PDFS:
        if not pdf.exists():
            raise FileNotFoundError(pdf)
        text = pdf_text(pdf)
        hits: dict[str, list[str]] = {}
        for label, pattern in FORBIDDEN.items():
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            if matches:
                hits[label] = sorted(set(matches))
        scans[pdf.name] = hits
    assert all(not hits for hits in scans.values()), scans
    report = {
        "status": "PASS",
        "exact_scientific_baseline": BASELINE,
        "compiled_pdf_language_scan": scans,
        "diversification": validate_diversification(),
        "risk_shock_sensitivity": validate_risk_map(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
