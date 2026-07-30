#!/usr/bin/env python3
"""Validate the Issue #40 scientific, semantic and visual consistency gates."""

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
FIGURES = ROOT / "figures" / "issue34"
QA = ROOT / "audits" / "issue40_visual_qa"
REPORT = ROOT / "audits" / "issue40_final_consistency.json"
BASELINE = "2c03e0ddd1bfa29ff8b16078d3effff592e36508"


def canonical_policy() -> dict[str, object]:
    canonical = pd.read_csv(OUTPUT / "canonical_mean_variance_policy.csv")
    assert len(canonical) == 1
    row = canonical.iloc[0]
    source = pd.read_csv(OUTPUT / "diversification_failure.csv")
    source = source.loc[source["policy"].eq(row["source_policy_id"])].iloc[0]
    mapping = {
        "gamma": "gamma",
        "allocation_Corn": "allocation_Corn",
        "allocation_Soybean": "allocation_Soybean",
        "allocation_Winter_Wheat": "allocation_Winter_Wheat",
        "gaussian_expected_profit": "gaussian_expected_profit",
        "gaussian_profit_variance": "gaussian_profit_variance",
        "student_t_evaluation_expected_profit": "evaluation_expected_profit",
        "student_t_evaluation_loss_CVaR": "evaluation_loss_CVaR",
        "risk_ceiling": "risk_ceiling",
    }
    assert all(np.isclose(row[left], source[right]) for left, right in mapping.items())
    assert np.isclose(row["gamma"], 0.0082)
    return {
        "name": row["policy"],
        "selection_rule": row["selection_rule"],
        "target": float(row["variance_reduction_target"]),
        "gamma": float(row["gamma"]),
        "allocation": {
            crop: float(row[f"allocation_{crop}"])
            for crop in ("Corn", "Soybean", "Winter_Wheat")
        },
        "gaussian_expected_profit": float(row["gaussian_expected_profit"]),
        "gaussian_variance": float(row["gaussian_profit_variance"]),
        "student_t_expected_profit": float(
            row["student_t_evaluation_expected_profit"]
        ),
        "student_t_loss_cvar": float(row["student_t_evaluation_loss_CVaR"]),
        "operational_feasible": bool(row["operational_feasible"]),
        "risk_feasible": bool(row["risk_ceiling_feasible"]),
    }


def reversal_results() -> dict[str, object]:
    frame = pd.read_csv(OUTPUT / "strong_reversal_lower_bound_summary.csv")
    principal = frame.loc[np.isclose(frame["near_zero_tolerance"], 1e-4)]
    report: dict[str, object] = {}
    for _, row in principal.iterrows():
        report[row["lower_bound_specification"]] = {
            column: int(row[column])
            for column in (
                "selected_pairwise_reversal_cells",
                "possible_pairwise_reversal_cells",
                "universal_pairwise_reversal_cells",
                "selected_complete_rank_reversal_cells",
                "possible_complete_rank_reversal_cells",
                "universal_complete_rank_reversal_cells",
                "selected_strong_reversal_cells",
                "possible_strong_reversal_cells",
                "universal_strong_reversal_cells",
                "multiple_optimum_cells",
                "infeasible_cells",
            )
        } | {
            "structural_strong_zero": bool(
                row["strong_reversal_structurally_inadmissible"]
            ),
            "first_strong_boundary": row["first_strong_boundary_status"],
            "minimum_top_crop_allocation": float(
                row["minimum_selected_top_crop_allocation"]
            ),
        }
    relaxed = frame.loc[~frame["strong_reversal_structurally_inadmissible"]]
    assert relaxed[[
        "selected_strong_reversal_cells",
        "possible_strong_reversal_cells",
        "universal_strong_reversal_cells",
    ]].eq(0).all().all()
    report["zero_tolerances"] = sorted(
        float(value) for value in frame["near_zero_tolerance"].unique()
    )
    return report


def projection_results() -> dict[str, object]:
    frame = pd.read_csv(OUTPUT / "heuristic_projection_sensitivity.csv")
    winner = frame.loc[frame["heuristic_policy"].eq("winner_take_all")]
    result: dict[str, object] = {}
    for _, row in winner.iterrows():
        result[row["projection_method"]] = {
            "raw": [float(row[f"raw_{crop}"]) for crop in (
                "Corn", "Soybean", "Winter_Wheat"
            )],
            "projected": [float(row[f"projected_{crop}"]) for crop in (
                "Corn", "Soybean", "Winter_Wheat"
            )],
            "distance_l1": float(row["projection_distance_l1"]),
            "distance_l2": float(row["projection_distance_l2"]),
            "classification": row["classification"],
            "risk_feasible": bool(row["risk_feasible"]),
        }
    assert result["euclidean_l2"]["classification"] == "no_reversal"
    assert result["l1_lexicographic"]["classification"] == (
        "selected_pairwise_reversal"
    )
    return result


def language_scan() -> dict[str, list[str]]:
    sources = list((ROOT / "manuscript" / "issue34").glob("*.tex")) + [
        ROOT / "main_manuscript.tex", ROOT / "supplementary_information.tex"
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in sources)
    for pdf in (ROOT / "main_manuscript.pdf", ROOT / "supplementary_information.pdf"):
        assert pdf.exists()
        text += "\n" + "\n".join(
            page.extract_text() or "" for page in PdfReader(pdf).pages
        )
    forbidden = {
        "revision-history semantics": (
            r"return(?:s|ed)?\s+to\s+(?:its\s+)?intended\s+foundation",
            r"restor(?:e|ed|ing)\s+(?:the\s+)?(?:exclusion\s+)?definition",
            r"the\s+paper\s+does\s+not\s+recast",
            r"previous\s+version",
            r"earlier\s+version",
            r"supervisor\s+draft",
        ),
        "workflow metadata": (
            r"\bissue\s*#?\s*40\b", r"\bpull request\b", r"\bcodex\b"
        ),
    }
    hits = {
        label: sorted({match.group(0) for pattern in patterns
                       for match in re.finditer(pattern, text, re.I)})
        for label, patterns in forbidden.items()
    }
    assert all(not values for values in hits.values()), hits
    return hits


def figure_checks() -> dict[str, object]:
    manifest = pd.read_csv(FIGURES / "figure_manifest.csv")
    assert len(manifest) >= 6
    main = manifest.loc[manifest["figure_id"].str.match(r"Figure[1-6]$")]
    assert len(main) == 6
    assert np.allclose(main["width_mm"], 183.007, atol=0.2)
    editable_counts: dict[str, int] = {}
    for number in range(1, 7):
        svg = (FIGURES / f"Figure{number}.svg").read_text(encoding="utf-8")
        count = len(re.findall(r"<text\b", svg))
        assert count > 0
        editable_counts[f"Figure{number}"] = count
        for extension in ("pdf", "png", "tiff"):
            assert (FIGURES / f"Figure{number}.{extension}").exists()
        for width in (89, 183):
            assert (QA / f"{width}mm" / f"Figure{number}.png").exists()
    renderer = pd.read_csv(QA / "renderer_qa.csv")
    assert renderer["bounds_failure_count"].sum() == 0
    assert renderer["title_collision_count"].sum() == 0
    generation = json.loads((QA / "generation_report.json").read_text())
    assert generation["minimum_svg_font_px"] >= 4.0
    assert generation["declared_ordinary_font_range_px"][0] >= 5.0
    assert generation["declared_ordinary_font_range_px"][1] <= 7.0
    assert generation["panel_label_font_px"] == 8.0
    assert generation["maximum_svg_font_px"] <= 11.0
    return {
        "figure_count": len(main),
        "widths_mm": sorted(float(value) for value in main["width_mm"].unique()),
        "editable_svg_text_nodes": editable_counts,
        "minimum_svg_font_px": generation["minimum_svg_font_px"],
        "maximum_svg_font_px": generation["maximum_svg_font_px"],
        "ordinary_font_range_px": generation["declared_ordinary_font_range_px"],
        "panel_label_font_px": generation["panel_label_font_px"],
        "renderer_bounds_failures": 0,
        "renderer_title_collisions": 0,
    }


def main() -> None:
    design = yaml.safe_load(
        (ROOT / "simulation" / "configs" / "issue34_full_model_design.yaml")
        .read_text(encoding="utf-8")
    )
    assert design["editorial_consistency_baseline_commit"] == BASELINE
    policies = pd.read_csv(OUTPUT / "policy_comparison.csv")
    assert not policies["policy"].str.contains("mean_variance|low_penalty").any()
    report = {
        "status": "PASS",
        "exact_parent_commit": BASELINE,
        "canonical_mean_variance_policy": canonical_policy(),
        "strong_reversal": reversal_results(),
        "heuristic_projection": projection_results(),
        "language_scan": language_scan(),
        "figures": figure_checks(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
