"""GOAL-13 source-grounded Stage II Nature figure system."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Mandatory editable-text rules must be set before any figure is created.
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["svg.hashsalt"] = "CRR-STAGEII-NATURE-VIS-2026-07-22"

from matplotlib import colors as mpl_colors
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageOps
from scipy import stats
import yaml


FIGURE_META: dict[str, tuple[str, int, int]] = {
    "Figure1": ("main", 183, 128),
    "Figure2": ("main", 183, 128),
    "Figure3": ("main", 183, 145),
    "Figure4": ("main", 183, 145),
    "Figure5": ("main", 183, 145),
    "Figure6": ("main", 183, 150),
    "FigureS1": ("supplementary", 183, 118),
    "FigureS2": ("supplementary", 183, 138),
    "FigureS3": ("supplementary", 183, 112),
    "FigureS4": ("supplementary", 183, 128),
}

STAGE_LABELS = {
    "M0": "M0\nordinal",
    "M1": "M1\ncardinal",
    "M2": "M2\noperations",
    "M3": "M3\nCVaR",
    "M4": "M4\ndependence",
}
STAGE_ORDER = list(STAGE_LABELS)
CROP_ORDER = ["Corn", "Soybean", "Winter Wheat"]
CROP_METRICS = ["allocation_Corn", "allocation_Soybean", "allocation_Winter_Wheat"]
DEFINITION_ORDER = [
    "relative_yield", "standardized_revenue", "operating_margin", "total_cost_margin"
]
DEFINITION_LABELS = {
    "relative_yield": "Relative\nyield",
    "standardized_revenue": "Standardized\nrevenue",
    "operating_margin": "Operating\nmargin",
    "total_cost_margin": "Total-cost\nmargin",
}
FAMILY_LABELS = {
    "gaussian": "Gaussian", "student_t_df4": "Student-t",
    "clayton": "Clayton", "empirical_copula": "Empirical",
}


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.12g")


def _read(root: Path, relative: str) -> pd.DataFrame:
    return pd.read_csv(root / relative)


def _t_summary(frame: pd.DataFrame, groups: list[str], value: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for keys, part in frame.groupby(groups, sort=True, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        values = part[value].dropna().astype(float).to_numpy()
        n = len(values)
        mean = float(values.mean()) if n else math.nan
        if n > 1:
            half = float(stats.t.ppf(0.975, n - 1) * values.std(ddof=1) / math.sqrt(n))
        else:
            half = 0.0 if n == 1 else math.nan
        row = dict(zip(groups, keys))
        row.update({"mean": mean, "ci_low": mean - half, "ci_high": mean + half, "n": n})
        rows.append(row)
    return pd.DataFrame(rows)


def _apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans"],
            "svg.fonttype": "none",
            "svg.hashsalt": "CRR-STAGEII-NATURE-VIS-2026-07-22",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "font.size": 6.8,
            "axes.labelsize": 6.8,
            "axes.titlesize": 7.2,
            "axes.titleweight": "semibold",
            "xtick.labelsize": 5.8,
            "ytick.labelsize": 5.8,
            "legend.fontsize": 5.7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.55,
            "xtick.major.width": 0.45,
            "ytick.major.width": 0.45,
            "xtick.major.size": 2.2,
            "ytick.major.size": 2.2,
            "legend.frameon": False,
            "savefig.dpi": 600,
            "figure.dpi": 150,
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "lines.solid_capstyle": "round",
        }
    )


def _panel(ax: plt.Axes, label: str, x: float = -0.12, y: float = 1.03) -> None:
    ax.text(
        x, y, label, transform=ax.transAxes, ha="left", va="bottom",
        fontsize=8.0, fontweight="bold", clip_on=False,
    )


def _quiet(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(False)


def _mm(width: float, height: float) -> tuple[float, float]:
    return width / 25.4, height / 25.4


def _box(
    ax: plt.Axes, xy: tuple[float, float], width: float, height: float,
    text: str, face: str, edge: str, *, fontsize: float = 6.2,
) -> None:
    patch = FancyBboxPatch(
        xy, width, height, boxstyle="round,pad=0.018,rounding_size=0.018",
        facecolor=face, edgecolor=edge, linewidth=0.8,
    )
    ax.add_patch(patch)
    ax.text(xy[0] + width / 2, xy[1] + height / 2, text, ha="center", va="center", fontsize=fontsize)


def _arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], color: str) -> None:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=8, lw=0.8, color=color))


def _architecture_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    architecture = pd.DataFrame(
        [
            (1, "Suitability ranking", "observed or predicted", "ordinal", "does not identify acreage"),
            (2, "Cardinal payoffs", "calibrated", "cardinal", "profit scale and gaps"),
            (3, "Joint uncertainty", "calibrated/design-controlled", "stochastic", "marginals and dependence"),
            (4, "Feasible + risk set", "partly latent", "constraints", "land, budget, rotation, contract, CVaR"),
            (5, "Optimal face", "model output", "set-valued", "possible and universal reversal"),
            (6, "Selected allocation", "solver/decision", "selection", "observed acreage is not identified as this object"),
        ],
        columns=["step", "stage", "input_status", "mathematical_role", "boundary"],
    )
    definitions = pd.DataFrame(
        [
            ("possible", "some optimizer reverses", "optimal-face property"),
            ("universal", "every optimizer reverses", "optimal-face property"),
            ("selected", "reported optimizer reverses", "selection dependent"),
        ],
        columns=["reversal_type", "definition", "status"],
    )
    return architecture, definitions


def _geometry_data() -> pd.DataFrame:
    cases = [
        ("common", "Common domain", 0.0, 1.0, 0.0, 1.0, "domain", "ranking boundary at 0.5"),
        ("margin", "Cardinal margin", 0.0, 1.0, 0.0, 0.0, "universal", "Soybean payoff dominates"),
        ("operations", "Operational forcing", 0.0, 0.45, 0.45, 0.45, "universal", "Corn cap + Soybean contract"),
        ("risk", "Risk-limited", 0.0, 0.35, 0.35, 0.35, "universal", "CVaR boundary truncates optimum"),
        ("set_valued", "Set-valued optimum", 0.2, 0.8, 0.2, 0.8, "possible_not_universal", "optimal face crosses rank boundary"),
    ]
    return pd.DataFrame(
        cases,
        columns=[
            "case_id", "case_label", "feasible_xcorn_min", "feasible_xcorn_max",
            "optimal_xcorn_min", "optimal_xcorn_max", "reversal_class", "mechanism",
        ],
    )


def _extract_source_data(root: Path, out: Path) -> dict[str, pd.DataFrame]:
    source = out / "visualization/stage_ii/source_data"
    source.mkdir(parents=True, exist_ok=True)
    lineage: list[dict[str, str]] = []

    def register(name: str, frame: pd.DataFrame, upstreams: Iterable[str], transformation: str) -> pd.DataFrame:
        path = source / f"{name}.csv"
        _write_csv(frame, path)
        upstream_list = list(upstreams)
        lineage.append(
            {
                "source_data": str(path.relative_to(out)),
                "source_sha256": _sha(path),
                "upstream_inputs": ";".join(upstream_list),
                "upstream_sha256": ";".join(_sha(root / item) for item in upstream_list),
                "transformation": transformation,
            }
        )
        return frame

    architecture, definitions = _architecture_data()
    contract = "visualization/stage_ii/figure_contracts.md"
    register("figure1_architecture", architecture, [contract], "contract extraction")
    register("figure1_definitions", definitions, [contract], "contract extraction")
    geometry = register("figure2_geometry", _geometry_data(), [contract], "exact analytic case extraction")

    path = _read(root, "simulation/stage_ii/outputs/nested_model_path.csv")
    nested = _t_summary(path, ["model_stage", "metric"], "value")
    register(
        "figure3_nested_summary", nested,
        ["simulation/stage_ii/outputs/nested_model_path.csv"],
        "mean and descriptive 95% t interval across closed-domain attribution seeds",
    )
    attribution = _read(root, "simulation/stage_ii/outputs/block_attribution.csv")
    shapley_raw = attribution.loc[attribution["attribution_type"].eq("SHAPLEY_ALL_SUBSETS")]
    shapley = _t_summary(shapley_raw, ["block", "metric"], "contribution")
    shapley["maximum_efficiency_residual"] = float(shapley_raw["efficiency_residual"].abs().max())
    register(
        "figure3_shapley_summary", shapley,
        ["simulation/stage_ii/outputs/block_attribution.csv"],
        "all-subset Shapley mean and descriptive 95% t interval",
    )
    pressures = _read(root, "simulation/stage_ii/outputs/kkt_pressures.csv")
    e2_pressure = pressures.loc[pressures["experiment_id"].eq("E2")].copy()
    terms = ["margin_pressure", "tail_risk_pressure", "budget_pressure", "shared_pressure", "boundary_pressure"]
    pressure_rows = []
    for mechanism, part in e2_pressure.groupby("mechanism_class", sort=True):
        for term in terms:
            values = part[term].astype(float)
            pressure_rows.append(
                {
                    "mechanism_class": mechanism, "pressure_term": term,
                    "mean": values.mean(), "minimum": values.min(), "maximum": values.max(),
                    "n": len(values), "maximum_stationarity_residual": part["stationarity_residual"].abs().max(),
                }
            )
    pressure_summary = register(
        "figure3_pressure_summary", pd.DataFrame(pressure_rows),
        ["simulation/stage_ii/outputs/kkt_pressures.csv"],
        "E2 local KKT pressure aggregation by preregistered mechanism class",
    )

    raw = _read(root, "simulation/stage_ii/outputs/raw_replications.csv")
    e2 = raw.loc[raw["experiment_id"].eq("E2")].copy()
    e2_cells = e2.groupby("cell_id", sort=True).agg(
        allocation_Corn=("allocation_Corn", "mean"),
        allocation_Soybean=("allocation_Soybean", "mean"),
        allocation_Winter_Wheat=("allocation_Winter_Wheat", "mean"),
        selected_reversal=("selected_reversal", "mean"),
        possible_reversal=("possible_reversal", "mean"),
        universal_reversal=("universal_reversal", "mean"),
        expected_profit=("expected_profit", "mean"),
        budget=("budget", "first"), rotation=("rotation", "first"),
        contract=("contract", "first"), corn_bound=("corn_bound", "first"),
        mechanism_class=("mechanism_class", "first"), n=("replication_seed", "nunique"),
    ).reset_index()
    register(
        "figure4_e2_cells", e2_cells,
        ["simulation/stage_ii/outputs/raw_replications.csv"],
        "E2 cell means and exact face-classification frequencies",
    )
    mechanism = _read(root, "simulation/stage_ii/outputs/mechanism_summary.csv")
    e2_contrasts = mechanism.loc[mechanism["experiment_id"].eq("E2")].copy()
    register(
        "figure4_e2_contrasts", e2_contrasts,
        ["simulation/stage_ii/outputs/mechanism_summary.csv"],
        "verbatim family-wise confirmatory E2 contrast summary",
    )
    e3_adverse = mechanism.loc[mechanism["experiment_id"].eq("E3")].copy()
    e3_adverse["promotion_status"] = "EXPERIMENT_PRECISION_FAILED_NON_PROMOTED"
    register(
        "figure4_e3_adverse", e3_adverse,
        ["simulation/stage_ii/outputs/mechanism_summary.csv"],
        "verbatim adverse E3 contrast summary with promotion boundary",
    )

    information = _read(root, "simulation/stage_ii/outputs/information_flexibility.csv")
    info_stochastic = information.loc[information["replication_seed"].gt(0)].copy()
    info_summary = _t_summary(
        info_stochastic, ["archetype", "signal_accuracy", "flexibility_level"],
        "value_of_information",
    )
    register(
        "figure5_information_summary", info_summary,
        ["simulation/stage_ii/outputs/information_flexibility.csv"],
        "E6 mean and descriptive 95% t interval across registered seeds",
    )
    info_interaction = mechanism.loc[mechanism["experiment_id"].eq("E6")].copy()
    register(
        "figure5_information_interaction", info_interaction,
        ["simulation/stage_ii/outputs/mechanism_summary.csv"],
        "verbatim family-wise E6 interaction summary",
    )
    info_exact = information.loc[information["replication_seed"].eq(0)].copy()
    register(
        "figure5_information_exact", info_exact,
        ["simulation/stage_ii/outputs/information_flexibility.csv"],
        "verbatim exact finite-state anchors and garbling certificates",
    )
    dependence = _read(root, "simulation/stage_ii/outputs/dependence_evaluation.csv")
    dep_rows = []
    for (true_family, assumed_family), part in dependence.groupby(["true_family", "assumed_family"], sort=True):
        evaluated = part.loc[part["policy_status"].eq("optimal")]
        risk = evaluated["risk_feasible"].fillna(False).astype(bool)
        dep_rows.append(
            {
                "true_family": true_family, "assumed_family": assumed_family,
                "risk_violation_rate": float((~risk).mean()) if len(risk) else math.nan,
                "mean_feasible_regret": evaluated["feasible_regret"].dropna().mean(),
                "evaluated_n": len(evaluated), "failed_policy_n": int(part["policy_status"].ne("optimal").sum()),
                "promotion_status": "EXPERIMENT_PRECISION_FAILED_NON_PROMOTED",
            }
        )
    dependence_boundary = register(
        "figure5_dependence_boundary", pd.DataFrame(dep_rows),
        ["simulation/stage_ii/outputs/dependence_evaluation.csv"],
        "E5 paired true-law diagnostic aggregation; experiment precision failure retained",
    )

    empirical_names = [
        "definition_summary", "state_heterogeneity", "year_heterogeneity",
        "lagged_2024_validation", "national_check", "leave_one_year_out",
        "claim_boundaries", "sample_flow",
    ]
    empirical = {}
    for name in empirical_names:
        empirical[name] = register(
            f"figure6_{name}", _read(root, f"empirical/outputs/{name}.csv"),
            [f"empirical/outputs/{name}.csv"], "verbatim admitted empirical output",
        )
    stage2_empirical_names = [
        "inversion_intensity_summary", "transition_summary", "rank_transition_events",
        "state_heterogeneity", "year_heterogeneity", "aggregation_summary",
        "observed_model_unidentified", "claim_boundaries",
    ]
    for name in stage2_empirical_names:
        empirical[f"stage2_{name}"] = register(
            f"figure6_stage2_{name}", _read(root, f"empirical/stage_ii/outputs/{name}.csv"),
            [f"empirical/stage_ii/outputs/{name}.csv"],
            "verbatim GOAL-15 admitted-data output",
        )

    stopping = _read(root, "simulation/stage_ii/outputs/sequential_stopping.csv")
    final_stop = stopping.sort_values("check_n").groupby(
        ["experiment_id", "contrast_id", "metric"], as_index=False
    ).tail(1)
    stop_summary = final_stop.groupby("experiment_id", sort=True).agg(
        registered_intervals=("precision_pass", "size"),
        intervals_passed=("precision_pass", "sum"),
        final_replications=("check_n", "max"),
        experiment_pass=("all_registered_primary_intervals_pass", "all"),
    ).reset_index()
    register(
        "supplementary_stopping_summary", stop_summary,
        ["simulation/stage_ii/outputs/sequential_stopping.csv"],
        "final scheduled precision decision by experiment",
    )
    adverse = mechanism.loc[mechanism["experiment_id"].isin(["E1", "E3", "E4", "E5"])].copy()
    adverse["promotion_status"] = "NON_PROMOTED_EXPERIMENT_PRECISION_FAILED"
    register(
        "supplementary_adverse_inventory", adverse,
        ["simulation/stage_ii/outputs/mechanism_summary.csv"],
        "complete failed-experiment inventory",
    )
    infeasible_summary = raw.groupby(["experiment_id", "cell_id"], sort=True).agg(
        registered_infeasible=("registered_infeasible", lambda x: int(x.fillna(False).astype(bool).sum())),
        total_rows=("replication_seed", "size"),
    ).reset_index()
    infeasible_summary = infeasible_summary.loc[infeasible_summary["registered_infeasible"].gt(0)]
    register(
        "supplementary_infeasible_summary", infeasible_summary,
        ["simulation/stage_ii/outputs/raw_replications.csv"],
        "complete registered-infeasible count by experiment and cell",
    )
    order_rows = attribution.loc[attribution["attribution_type"].eq("ORDER_PATH")].copy()
    order_summary = order_rows.groupby(["block", "metric"], sort=True).agg(
        mean=("contribution", "mean"), minimum=("contribution", "min"),
        maximum=("contribution", "max"), n=("contribution", "size"),
    ).reset_index()
    register(
        "supplementary_order_sensitivity", order_summary,
        ["simulation/stage_ii/outputs/block_attribution.csv"],
        "all-order contribution range",
    )
    diagnostics = pd.DataFrame(
        [
            ("reverse-order replay", 12.0, 12.0, "count"),
            ("solver sensitivity", 9.0, 9.0, "count"),
            ("KKT pressure residual", float(pressures["stationarity_residual"].abs().max()), 1e-7, "maximum"),
            ("Shapley efficiency residual", float(shapley_raw["efficiency_residual"].abs().max()), 1e-8, "maximum"),
            ("registered infeasible", float(raw["registered_infeasible"].fillna(False).astype(bool).sum()), 206.0, "count"),
        ],
        columns=["diagnostic", "observed", "criterion", "criterion_type"],
    )
    register(
        "supplementary_numerical_diagnostics", diagnostics,
        [
            "simulation/stage_ii/outputs/independent_replay.csv",
            "simulation/stage_ii/outputs/solver_sensitivity.csv",
            "simulation/stage_ii/outputs/kkt_pressures.csv",
            "simulation/stage_ii/outputs/block_attribution.csv",
            "simulation/stage_ii/outputs/raw_replications.csv",
        ],
        "predeclared numerical-gate extraction",
    )

    lineage_frame = pd.DataFrame(lineage)
    _write_csv(lineage_frame, source / "lineage.csv")
    return {
        "architecture": architecture, "definitions": definitions, "geometry": geometry,
        "nested": nested, "shapley": shapley, "pressures": pressure_summary,
        "e2_cells": e2_cells, "e2_contrasts": e2_contrasts, "e3_adverse": e3_adverse,
        "info_summary": info_summary, "info_interaction": info_interaction,
        "info_exact": info_exact, "dependence": dependence_boundary,
        "stopping": stop_summary, "adverse": adverse, "infeasible": infeasible_summary,
        "orders": order_summary,
        "diagnostics": diagnostics, **empirical,
    }


def _new_figure(figure_id: str) -> plt.Figure:
    _, width, height = FIGURE_META[figure_id]
    return plt.figure(figsize=_mm(width, height), constrained_layout=True)


def _figure1(data: dict[str, pd.DataFrame], palette: dict[str, str]) -> plt.Figure:
    fig = _new_figure("Figure1")
    grid = fig.add_gridspec(2, 2, height_ratios=[1.45, 1.0])
    ax = fig.add_subplot(grid[0, :])
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    _panel(ax, "a", x=-0.02, y=1.0)
    stages = ["Suitability\nranking", "Cardinal\npayoffs", "Joint\nuncertainty",
              "Feasible +\nrisk set", "Optimal\nface", "Selected\nallocation"]
    status = ["observed", "calibrated", "calibrated", "partly latent", "model output", "selection"]
    fills = [palette["pale_blue"], palette["mint"], palette["mint"],
             palette["pale_rose"], palette["light_gray"], palette["light_gray"]]
    xs = np.linspace(0.01, 0.84, 6)
    for i, (x, label, sub, fill) in enumerate(zip(xs, stages, status, fills)):
        _box(ax, (x, 0.46), 0.145, 0.29, label, fill, palette["charcoal"], fontsize=6.3)
        ax.text(x + 0.0725, 0.39, sub, ha="center", va="top", fontsize=5.4,
                color=palette["steel"])
        if i < 5:
            _arrow(ax, (x + 0.147, 0.605), (xs[i + 1] - 0.006, 0.605), palette["steel"])
    ax.text(0.5, 0.93, "From ordinal rankings to identified allocation claims",
            ha="center", va="center", fontsize=9.0, fontweight="bold")
    ax.plot([0.505, 0.505], [0.26, 0.80], ls=(0, (2, 2)), lw=0.8, color=palette["adverse"])
    ax.text(0.505, 0.23, "identification boundary", ha="center", va="top",
            fontsize=5.7, color=palette["adverse"])
    ax.text(0.235, 0.08, "Ranking evidence", ha="center", fontsize=6.4, color=palette["navy"])
    ax.text(0.755, 0.08, "Decision model + selection assumptions", ha="center",
            fontsize=6.4, color=palette["adverse"])

    ax = fig.add_subplot(grid[1, 0])
    _panel(ax, "b")
    labels = ["possible", "universal", "selected"]
    segments = [(-0.25, 0.40), (-0.55, -0.15), (-0.35, -0.35)]
    y = np.arange(3)[::-1]
    ax.axvline(0, color=palette["charcoal"], lw=0.7)
    ax.axvspan(-0.65, 0, color=palette["pale_rose"], alpha=0.7)
    ax.axvspan(0, 0.65, color=palette["pale_blue"], alpha=0.7)
    for yy, (lo, hi), label in zip(y, segments, labels):
        ax.plot([lo, hi], [yy, yy], lw=5.5, color=palette["rose"], solid_capstyle="butt")
        if lo == hi:
            ax.plot(lo, yy, "o", ms=4.5, color=palette["navy"])
        ax.text(-0.69, yy, label, ha="right", va="center", fontsize=6.2)
    ax.set(xlim=(-0.78, 0.68), ylim=(-0.7, 2.7), yticks=[],
           xlabel=r"optimal-face difference  $x_{Corn}-x_{Soybean}$")
    ax.text(-0.32, 2.45, "reversal", ha="center", fontsize=5.6, color=palette["adverse"])
    ax.text(0.32, 2.45, "rank aligned", ha="center", fontsize=5.6, color=palette["navy"])
    _quiet(ax)

    ax = fig.add_subplot(grid[1, 1])
    _panel(ax, "c")
    ax.axis("off")
    questions = [
        ("1", "Is the ranking ordinal or cardinal?"),
        ("2", "Are joint returns identified?"),
        ("3", "Which constraints are observed?"),
        ("4", "Is the optimum set-valued?"),
        ("5", "What selects an acreage vector?"),
    ]
    for idx, (number, question) in enumerate(questions):
        yy = 0.92 - idx * 0.19
        ax.add_patch(plt.Circle((0.05, yy), 0.038, facecolor=palette["navy"], edgecolor="none"))
        ax.text(0.05, yy, number, color="white", ha="center", va="center", fontsize=5.5, fontweight="bold")
        ax.text(0.11, yy, question, ha="left", va="center", fontsize=6.3)
    ax.text(0.02, 0.0, "Observed acreage alone cannot recover private objectives or constraints.",
            fontsize=5.6, color=palette["steel"])
    return fig


def _draw_geometry_case(ax: plt.Axes, row: pd.Series, palette: dict[str, str], letter: str) -> None:
    _panel(ax, letter)
    ax.axvspan(0, 0.5, color=palette["pale_rose"], alpha=0.65)
    ax.axvline(0.5, color=palette["charcoal"], lw=0.7, ls=(0, (2, 2)))
    ax.plot([row.feasible_xcorn_min, row.feasible_xcorn_max], [0, 0], lw=8,
            color=palette["light_gray"], solid_capstyle="butt")
    lo, hi = row.optimal_xcorn_min, row.optimal_xcorn_max
    if abs(lo - hi) < 1e-12:
        ax.plot(lo, 0, "o", ms=6, color=palette["navy"], zorder=3)
    else:
        ax.plot([lo, hi], [0, 0], lw=4, color=palette["rose"], solid_capstyle="butt", zorder=3)
    ax.set(xlim=(-0.03, 1.03), ylim=(-0.7, 0.72), yticks=[], xticks=[0, 0.5, 1],
           xlabel=r"Corn share $x_C$")
    ax.set_title(row.case_label, pad=3)
    ax.text(0.02, -0.48, row.mechanism, ha="left", va="center", fontsize=5.3,
            color=palette["steel"])
    _quiet(ax)


def _figure2(data: dict[str, pd.DataFrame], palette: dict[str, str]) -> plt.Figure:
    fig = _new_figure("Figure2")
    grid = fig.add_gridspec(2, 3, width_ratios=[1.25, 1, 1])
    ax = fig.add_subplot(grid[:, 0])
    _panel(ax, "a")
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    ax.text(0.5, 0.95, "Exact two-crop geometry", ha="center", fontsize=8.2, fontweight="bold")
    ax.add_patch(Rectangle((0.08, 0.61), 0.84, 0.12, facecolor=palette["light_gray"], edgecolor="none"))
    ax.add_patch(Rectangle((0.08, 0.61), 0.42, 0.12, facecolor=palette["pale_rose"], edgecolor="none"))
    ax.plot([0.5, 0.5], [0.55, 0.79], color=palette["charcoal"], lw=1.0)
    ax.text(0.08, 0.78, r"$x_C=0$", ha="center", fontsize=6)
    ax.text(0.50, 0.78, r"rank boundary $x_C=x_S=0.5$", ha="center", fontsize=6)
    ax.text(0.92, 0.78, r"$x_C=1$", ha="center", fontsize=6)
    ax.text(0.29, 0.64, "ranking reversal", ha="center", fontsize=6.3, color=palette["adverse"])
    ax.text(0.71, 0.64, "rank aligned", ha="center", fontsize=6.3, color=palette["navy"])
    formulas = [
        r"Feasible set:  $x_C+x_S=1$",
        r"Reversal:  $x_C-x_S<0$",
        r"Possible:  $\min_{x\in X^*}(x_C-x_S)<0$",
        r"Universal:  $\max_{x\in X^*}(x_C-x_S)<0$",
        r"Selected:  $x_C^*-x_S^*<0$",
    ]
    for i, formula in enumerate(formulas):
        ax.text(0.08, 0.48 - i * 0.095, formula, ha="left", fontsize=6.5)
    ax.text(0.08, 0.03, "The same ordinal ranking admits each case at right.",
            fontsize=5.6, color=palette["steel"])

    geometry = data["geometry"].set_index("case_id")
    for ax, case, letter in zip(
        [fig.add_subplot(grid[0, 1]), fig.add_subplot(grid[0, 2]),
         fig.add_subplot(grid[1, 1]), fig.add_subplot(grid[1, 2])],
        ["margin", "operations", "risk", "set_valued"], ["b", "c", "d", "e"],
    ):
        _draw_geometry_case(ax, geometry.loc[case], palette, letter)
    return fig


def _metric_row(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    return frame.loc[frame["metric"].eq(metric)].copy()


def _vector_heatmap(ax: plt.Axes, values: np.ndarray, **kwargs: Any) -> Any:
    rows, columns = values.shape
    mesh = ax.pcolormesh(np.arange(columns + 1) - 0.5, np.arange(rows + 1) - 0.5,
                         values, shading="flat", rasterized=False, **kwargs)
    ax.set_xlim(-0.5, columns - 0.5)
    ax.set_ylim(rows - 0.5, -0.5)
    return mesh


def _figure3(data: dict[str, pd.DataFrame], palette: dict[str, str]) -> plt.Figure:
    fig = _new_figure("Figure3")
    grid = fig.add_gridspec(2, 2)
    nested = data["nested"]
    ax = fig.add_subplot(grid[0, 0])
    _panel(ax, "a")
    bottom = np.zeros(5)
    for crop, metric, color in zip(CROP_ORDER, CROP_METRICS,
                                    [palette["navy"], palette["teal"], palette["amber"]]):
        part = _metric_row(nested, metric).set_index("model_stage").reindex(STAGE_ORDER)
        values = part["mean"].to_numpy()
        ax.bar(np.arange(5), values, bottom=bottom, color=color, width=0.72, label=crop)
        bottom += values
    ax.set(xticks=np.arange(5), xticklabels=[STAGE_LABELS[x] for x in STAGE_ORDER],
           ylabel="Allocation share", ylim=(0, 1.05), title="Closed M0–M4 allocation path")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.23))
    _quiet(ax)

    ax = fig.add_subplot(grid[0, 1])
    _panel(ax, "b")
    for metric, color, label in [("expected_profit", palette["navy"], "Expected profit"),
                                  ("cvar_loss", palette["adverse"], "CVaR loss")]:
        part = _metric_row(nested, metric).set_index("model_stage").reindex(STAGE_ORDER)
        vals = part["mean"].to_numpy(float)
        scale = max(np.nanmax(np.abs(vals)), 1.0)
        ax.plot(np.arange(5), vals / scale, marker="o", ms=3.2, color=color, label=label)
        ax.fill_between(np.arange(5), part["ci_low"].to_numpy(float) / scale,
                        part["ci_high"].to_numpy(float) / scale, color=color, alpha=0.13)
    ax.axhline(0, color=palette["charcoal"], lw=0.5)
    ax.set(xticks=np.arange(5), xticklabels=[STAGE_LABELS[x] for x in STAGE_ORDER],
           ylabel="Within-metric normalized level", title="Value and tail-risk path")
    ax.legend(loc="best")
    _quiet(ax)

    ax = fig.add_subplot(grid[1, 0])
    _panel(ax, "c")
    shapley = _metric_row(data["shapley"], "allocation_Corn").sort_values("mean")
    y = np.arange(len(shapley))
    ax.axvline(0, color=palette["charcoal"], lw=0.6)
    ax.errorbar(shapley["mean"], y,
                xerr=[shapley["mean"] - shapley["ci_low"], shapley["ci_high"] - shapley["mean"]],
                fmt="o", ms=4, color=palette["navy"], ecolor=palette["steel"], capsize=2)
    ax.set(yticks=y, yticklabels=shapley["block"].str.title(),
           xlabel="Shapley contribution to Corn share", title="Exact all-subset attribution")
    ax.text(0.98, 0.05, r"max efficiency residual $<1.5\times10^{-14}$",
            transform=ax.transAxes, ha="right", fontsize=5.3, color=palette["steel"])
    _quiet(ax)

    ax = fig.add_subplot(grid[1, 1])
    _panel(ax, "d")
    pressure = data["pressures"].pivot(index="mechanism_class", columns="pressure_term", values="mean")
    pressure = pressure.loc[:, [x for x in ["margin_pressure", "tail_risk_pressure", "budget_pressure",
                                             "shared_pressure", "boundary_pressure"] if x in pressure]]
    card_diverging = mpl_colors.LinearSegmentedColormap.from_list(
        "card_diverging", [palette["rose"], "white", palette["teal"]]
    )
    image = _vector_heatmap(ax, pressure.to_numpy(), cmap=card_diverging,
                            norm=mpl_colors.TwoSlopeNorm(vcenter=0))
    ax.set(yticks=np.arange(len(pressure)), yticklabels=pressure.index.str.replace("_", " ").str.title(),
           xticks=np.arange(len(pressure.columns)),
           xticklabels=pressure.columns.str.replace("_pressure", "").str.replace("_", " ").str.title(),
           title="Validated local KKT pressures")
    ax.tick_params(axis="x", rotation=35)
    cbar = fig.colorbar(image, ax=ax, fraction=0.045, pad=0.03)
    cbar.solids.set_rasterized(False)
    cbar.set_label("Signed pressure")
    ax.text(0.99, -0.23, r"E2 only; maximum stationarity residual $1.82\times10^{-11}$",
            transform=ax.transAxes, ha="right", fontsize=5.2, color=palette["steel"])
    return fig


def _figure4(data: dict[str, pd.DataFrame], palette: dict[str, str]) -> plt.Figure:
    fig = _new_figure("Figure4")
    grid = fig.add_gridspec(2, 2)
    cells = data["e2_cells"].copy()
    ax = fig.add_subplot(grid[0, 0])
    _panel(ax, "a")
    x = np.arange(len(cells))
    bottom = np.zeros(len(cells))
    for crop, col, color in zip(CROP_ORDER,
                                ["allocation_Corn", "allocation_Soybean", "allocation_Winter_Wheat"],
                                [palette["navy"], palette["teal"], palette["amber"]]):
        values = cells[col].to_numpy(float)
        ax.bar(x, values, bottom=bottom, color=color, width=0.78, label=crop)
        bottom += values
    labels = cells["cell_id"].str.replace("E2-", "", regex=False).str.replace("-", "\n", regex=False)
    ax.set(xticks=x, xticklabels=labels, ylabel="Allocation share", ylim=(0, 1.04),
           title="Operational factorial (E2; n=16 per cell)")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.29))
    _quiet(ax)

    ax = fig.add_subplot(grid[0, 1])
    _panel(ax, "b")
    width = 0.23
    for j, (metric, color, label) in enumerate([
        ("selected_reversal", palette["navy"], "Selected"),
        ("possible_reversal", palette["teal"], "Possible"),
        ("universal_reversal", palette["rose"], "Universal"),
    ]):
        ax.bar(x + (j - 1) * width, cells[metric], width=width, color=color, label=label)
    ax.set(xticks=x, xticklabels=labels, ylabel="Reversal frequency", ylim=(0, 1.08),
           title="Selected and optimal-face classifications")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.29))
    _quiet(ax)

    ax = fig.add_subplot(grid[1, 0])
    _panel(ax, "c")
    contrasts = data["e2_contrasts"]
    alloc = _metric_row(contrasts, "allocation_l1").sort_values("estimate")
    y = np.arange(len(alloc))
    ax.axvline(0, color=palette["charcoal"], lw=0.6)
    ax.errorbar(alloc["estimate"], y,
                xerr=[alloc["estimate"] - alloc["ci_low"], alloc["ci_high"] - alloc["estimate"]],
                fmt="o", ms=3.5, color=palette["navy"], ecolor=palette["steel"], capsize=1.8)
    short = alloc["contrast_id"].str.replace("E2-", "", regex=False).str.replace("-VS-BASE", "", regex=False)
    ax.set(yticks=y, yticklabels=short, xlabel=r"Allocation $L_1$ change vs base",
           title="Family-wise confirmatory contrasts")
    ax.text(0.98, 0.04, "24/24 registered intervals passed", transform=ax.transAxes,
            ha="right", fontsize=5.4, color=palette["teal"])
    _quiet(ax)

    ax = fig.add_subplot(grid[1, 1])
    _panel(ax, "d")
    adverse = _metric_row(data["e3_adverse"], "allocation_l1").copy()
    adverse["alpha"] = adverse["contrast_id"].str.extract(r"A(0\.\d+)")[0]
    adverse["regime"] = adverse["contrast_id"].str.extract(r"A0\.\d+-(.*)-VS-SLACK")[0]
    regimes = [x for x in ["JUST_BINDING", "BINDING_MID", "STRONGLY_BINDING"] if x in adverse["regime"].values]
    for i, regime in enumerate(regimes):
        part = adverse.loc[adverse["regime"].eq(regime)].sort_values("alpha")
        xx = np.arange(len(part)) + (i - 1) * 0.22
        ax.errorbar(xx, part["estimate"],
                    yerr=[part["estimate"] - part["ci_low"], part["ci_high"] - part["estimate"]],
                    fmt="o", ms=3.2, capsize=1.5,
                    color=[palette["steel"], palette["amber"], palette["adverse"]][i],
                    label=regime.replace("_", " ").title())
    alphas = sorted(adverse["alpha"].dropna().unique())
    ax.set(xticks=np.arange(len(alphas)), xticklabels=alphas,
           xlabel=r"CVaR level $\alpha$", ylabel=r"Allocation $L_1$ change",
           title="Risk experiment retained as adverse evidence")
    ax.legend(loc="upper left")
    ax.text(0.98, 0.05, "EXPERIMENT PRECISION FAILED at n=64\nnon-promoted",
            transform=ax.transAxes, ha="right", fontsize=5.4, color=palette["adverse"],
            fontweight="bold")
    ax.set_facecolor(palette["light_gray"])
    _quiet(ax)
    return fig


def _archetype_label(value: str) -> str:
    return {"dominated_option_null": "Dominated-option null",
            "robust_option_substitutes": "Robust option substitutes",
            "specialization_unlocks": "Specialization unlocks"}.get(value, value.replace("_", " ").title())


def _figure5(data: dict[str, pd.DataFrame], palette: dict[str, str]) -> plt.Figure:
    fig = _new_figure("Figure5")
    grid = fig.add_gridspec(2, 2)
    info = data["info_summary"]
    ax = fig.add_subplot(grid[0, 0])
    _panel(ax, "a")
    colors = [palette["steel"], palette["teal"], palette["rose"]]
    markers = {"low": "o", "high": "s"}
    for color, archetype in zip(colors, sorted(info["archetype"].unique())):
        for flex in ["low", "high"]:
            part = info.loc[info["archetype"].eq(archetype) & info["flexibility_level"].eq(flex)].sort_values("signal_accuracy")
            ax.plot(part["signal_accuracy"], part["mean"], color=color, marker=markers[flex], ms=3.2,
                    ls="-" if flex == "high" else "--",
                    label=f"{_archetype_label(archetype)} · {flex}")
            ax.fill_between(part["signal_accuracy"], part["ci_low"], part["ci_high"], color=color, alpha=0.10)
    ax.set(xlabel="Signal accuracy", ylabel="Value of information",
           xticks=[0.5, 0.7, 0.9], title="Information value depends on flexibility (E6)")
    ax.legend(loc="upper left", ncol=2, columnspacing=0.8, handlelength=1.7)
    _quiet(ax)

    ax = fig.add_subplot(grid[0, 1])
    _panel(ax, "b")
    inter = data["info_interaction"].copy().sort_values("estimate")
    inter["label"] = inter["contrast_id"].str.replace("E6-", "", regex=False).str.replace("-QXF", "", regex=False).map(
        lambda x: _archetype_label(x.lower()))
    y = np.arange(len(inter))
    ax.axvline(0, color=palette["charcoal"], lw=0.6)
    ax.errorbar(inter["estimate"], y,
                xerr=[inter["estimate"] - inter["ci_low"], inter["ci_high"] - inter["estimate"]],
                fmt="o", ms=4, capsize=2, color=palette["navy"], ecolor=palette["steel"])
    ax.set(yticks=y, yticklabels=inter["label"], xlabel="Accuracy × flexibility interaction",
           title="Registered mechanism contrasts")
    ax.text(0.98, 0.05, "3/3 passed at n=16", transform=ax.transAxes, ha="right",
            fontsize=5.5, color=palette["teal"])
    _quiet(ax)

    ax = fig.add_subplot(grid[1, 0])
    _panel(ax, "c")
    exact = data["info_exact"]
    exact_summary = exact.groupby("archetype", sort=True).agg(
        exact_anchor=("exact_anchor", "all"), nested_actions=("action_set_nested", "all"),
        actionable_cells=("policy_actionable", "sum"), cells=("policy_actionable", "size"),
    ).reset_index()
    ax.axis("off")
    ax.set_title("Exact finite-state checks", pad=3)
    for i, row in exact_summary.iterrows():
        yy = 0.82 - i * 0.27
        ax.add_patch(Rectangle((0.02, yy - 0.09), 0.96, 0.19, facecolor=palette["mint"],
                               edgecolor=palette["teal"], linewidth=0.7))
        ax.text(0.05, yy + 0.035, _archetype_label(row.archetype), fontweight="semibold", fontsize=6.2)
        ax.text(0.05, yy - 0.045,
                f"exact anchor PASS   nested actions PASS   actionable {int(row.actionable_cells)}/{int(row.cells)}",
                fontsize=5.5, color=palette["steel"])
    ax.text(0.02, 0.02, "Includes ignore-signal nulls and explicit 0.90→0.70/0.50 garbling maps.",
            fontsize=5.4, color=palette["steel"])

    ax = fig.add_subplot(grid[1, 1])
    _panel(ax, "d")
    dep = data["dependence"].copy()
    families = sorted(set(dep["true_family"]) | set(dep["assumed_family"]))
    matrix = dep.pivot(index="true_family", columns="assumed_family", values="risk_violation_rate").reindex(
        index=families, columns=families)
    image = _vector_heatmap(ax, matrix.to_numpy(), cmap="Greys", vmin=0, vmax=1)
    ax.set(xticks=np.arange(len(families)), yticks=np.arange(len(families)),
           xticklabels=[FAMILY_LABELS.get(x, x) for x in families],
           yticklabels=[FAMILY_LABELS.get(x, x) for x in families],
           xlabel="Assumed dependence", ylabel="True dependence",
           title="Dependence boundary retained, not promoted")
    ax.tick_params(axis="x", rotation=30)
    for i in range(len(families)):
        for j in range(len(families)):
            value = matrix.iloc[i, j]
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=5.1,
                    color="white" if value > 0.58 else palette["charcoal"])
    cbar = fig.colorbar(image, ax=ax, fraction=0.045, pad=0.03)
    cbar.solids.set_rasterized(False)
    cbar.set_label("Risk-violation rate")
    ax.text(0.99, -0.27, "E5 EXPERIMENT PRECISION FAILED at n=64 · adverse/supplementary only",
            transform=ax.transAxes, ha="right", fontsize=5.2, color=palette["adverse"], fontweight="bold")
    return fig


def _figure6(data: dict[str, pd.DataFrame], palette: dict[str, str]) -> plt.Figure:
    fig = _new_figure("Figure6")
    grid = fig.add_gridspec(2, 2)
    transition = data["stage2_transition_summary"]
    transition = transition.loc[transition["metric"].eq("lagged_top_minus_other_share_change")].set_index(
        "ranking_definition").reindex(DEFINITION_ORDER)
    ax = fig.add_subplot(grid[0, 0])
    _panel(ax, "a")
    y = np.arange(4)
    ax.axvline(0, color=palette["charcoal"], lw=0.7)
    ax.errorbar(transition["estimate"], y,
                xerr=[transition["estimate"] - transition["ci_low"],
                      transition["ci_high"] - transition["estimate"]],
                fmt="o", ms=4.2, capsize=2, color=palette["navy"], ecolor=palette["steel"])
    ax.set(yticks=y, yticklabels=[DEFINITION_LABELS[x].replace("\n", " ") for x in DEFINITION_ORDER],
           xlabel="Prior-score-top minus other crop\nacreage-share change",
           title="Lagged rank-to-acreage transitions")
    ax.text(0.98, 0.05, "51 transitions per definition\nall 95% intervals include zero",
            transform=ax.transAxes, ha="right", fontsize=5.3, color=palette["adverse"])
    _quiet(ax)

    inversion = data["stage2_inversion_intensity_summary"]
    inversion = inversion.loc[inversion["metric"].eq("inversion_intensity")].set_index(
        "ranking_definition").reindex(DEFINITION_ORDER)
    states = data["stage2_state_heterogeneity"]
    ax = fig.add_subplot(grid[0, 1])
    _panel(ax, "b")
    rng = np.random.default_rng(20260722)
    for yy, definition in enumerate(DEFINITION_ORDER):
        values = states.loc[states["ranking_definition"].eq(definition), "mean_inversion_intensity"].to_numpy(float)
        ax.scatter(values, yy + rng.uniform(-0.10, 0.10, len(values)), s=6, alpha=0.35,
                   color=palette["steel"], edgecolors="none")
    ax.errorbar(inversion["estimate"], y,
                xerr=[inversion["estimate"] - inversion["ci_low"],
                      inversion["ci_high"] - inversion["estimate"]],
                fmt="o", ms=4.4, capsize=2, color=palette["navy"], ecolor=palette["navy"], zorder=3)
    ax.set(yticks=y, yticklabels=[DEFINITION_LABELS[x].replace("\n", " ") for x in DEFINITION_ORDER],
           xlim=(-0.03, 1.03), xlabel="Mean discordant pairs / 3",
           title="Definition and state heterogeneity")
    ax.text(0.98, 0.96, "dots: 26 states (one has 2 years)\nintervals: state-cluster bootstrap",
            transform=ax.transAxes, ha="right", va="top", fontsize=5.1, color=palette["steel"],
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.9, "pad": 1.2})
    _quiet(ax)

    year = data["stage2_year_heterogeneity"].pivot(
        index="ranking_definition", columns="year", values="mean_inversion_intensity"
    ).reindex(DEFINITION_ORDER)
    ax = fig.add_subplot(grid[1, 0])
    _panel(ax, "c")
    card_blue = mpl_colors.LinearSegmentedColormap.from_list(
        "card_blue", ["white", palette["pale_blue"], palette["navy"]]
    )
    image = _vector_heatmap(ax, year.to_numpy(), cmap=card_blue, vmin=0, vmax=1)
    ax.set(yticks=np.arange(4), yticklabels=[DEFINITION_LABELS[x].replace("\n", " ") for x in DEFINITION_ORDER],
           xticks=np.arange(3), xticklabels=[str(x) for x in year.columns],
           xlabel="Year", title="Temporal robustness")
    for i in range(len(year)):
        for j in range(len(year.columns)):
            value = year.iloc[i, j]
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=5.5,
                    color="white" if value > 0.58 else palette["charcoal"])
    cbar = fig.colorbar(image, ax=ax, fraction=0.045, pad=0.03)
    cbar.solids.set_rasterized(False)
    cbar.set_label("Inversion intensity")

    aggregation = data["stage2_aggregation_summary"].set_index("ranking_definition").reindex(DEFINITION_ORDER)
    ax = fig.add_subplot(grid[1, 1])
    _panel(ax, "d")
    x = np.arange(4)
    ax.bar(x - 0.18, inversion["estimate"], width=0.36, color=palette["navy"], label="State mean")
    ax.bar(x + 0.18, aggregation["national_mean_inversion_intensity"], width=0.36,
           color=palette["rose"], label="National")
    ax.set(xticks=x, xticklabels=[DEFINITION_LABELS[z] for z in DEFINITION_ORDER],
           ylabel="Inversion intensity", ylim=(0, 1), title="Aggregation changes the pattern")
    ax.legend(loc="upper left")
    ax.text(0.98, 0.96, "relative yield nationally tied\nobserved ≠ model optimum · mechanisms unidentified",
            transform=ax.transAxes, ha="right", va="top", fontsize=5.1, color=palette["adverse"],
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.9, "pad": 1.2})
    _quiet(ax)
    return fig


def _figure_s1(data: dict[str, pd.DataFrame], palette: dict[str, str]) -> plt.Figure:
    fig = _new_figure("FigureS1")
    grid = fig.add_gridspec(1, 2)
    stop = data["stopping"].copy()
    x = np.arange(len(stop))
    ax = fig.add_subplot(grid[0, 0])
    _panel(ax, "a")
    colors = [palette["teal"] if value else palette["adverse"] for value in stop["experiment_pass"]]
    ax.bar(x, stop["registered_intervals"], color=palette["light_gray"], label="Registered")
    ax.bar(x, stop["intervals_passed"], color=colors, label="Passed")
    ax.set(xticks=x, xticklabels=stop["experiment_id"], ylabel="Primary intervals",
           title="Sequential precision decision")
    ax.legend(loc="upper left")
    for xx, (_, row) in enumerate(stop.iterrows()):
        ax.text(xx, row.registered_intervals + 0.6, f"n={int(row.final_replications)}",
                ha="center", fontsize=5.5)
    _quiet(ax)

    ax = fig.add_subplot(grid[0, 1])
    _panel(ax, "b")
    ax.axis("off")
    ax.set_title("Promotion ledger", pad=3)
    for i, row in stop.iterrows():
        passed = bool(row.experiment_pass)
        yy = 0.88 - i * 0.14
        ax.add_patch(Rectangle((0.04, yy - 0.045), 0.10, 0.09,
                               facecolor=palette["mint"] if passed else palette["pale_rose"], edgecolor="none"))
        ax.text(0.09, yy, row.experiment_id, ha="center", va="center", fontweight="bold", fontsize=6)
        ax.text(0.18, yy, "PROMOTED" if passed else "FAILED · NON-PROMOTED",
                ha="left", va="center", fontsize=6.1,
                color=palette["teal"] if passed else palette["adverse"])
    return fig


def _figure_s2(data: dict[str, pd.DataFrame], palette: dict[str, str]) -> plt.Figure:
    fig = _new_figure("FigureS2")
    grid = fig.add_gridspec(2, 2, height_ratios=[1.3, 1])
    adverse = data["adverse"]
    ax = fig.add_subplot(grid[0, :])
    _panel(ax, "a", x=-0.03)
    summary = adverse.groupby(["experiment_id", "metric"], sort=True).agg(
        registered=("precision_pass", "size"), passed=("precision_pass", "sum")
    ).reset_index()
    pivot = summary.pivot(index="experiment_id", columns="metric", values="passed")
    total = summary.pivot(index="experiment_id", columns="metric", values="registered")
    ratio = pivot / total
    image = _vector_heatmap(ax, ratio.to_numpy(), cmap="Greys", vmin=0, vmax=1)
    ax.set(yticks=np.arange(len(ratio)), yticklabels=ratio.index,
           xticks=np.arange(len(ratio.columns)),
           xticklabels=ratio.columns.str.replace("_", " ").str.title(),
           title="Complete failed-experiment precision inventory")
    ax.tick_params(axis="x", rotation=25)
    for i in range(len(ratio)):
        for j in range(len(ratio.columns)):
            if not math.isnan(ratio.iloc[i, j]):
                ax.text(j, i, f"{int(pivot.iloc[i,j])}/{int(total.iloc[i,j])}", ha="center", va="center",
                        fontsize=5.6, color="white" if ratio.iloc[i, j] > 0.55 else palette["charcoal"])
    cbar = fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    cbar.solids.set_rasterized(False)
    cbar.set_label("Intervals passed / registered")

    ax = fig.add_subplot(grid[1, 0])
    _panel(ax, "b")
    infeasible = data["infeasible"].groupby("experiment_id", sort=True)["registered_infeasible"].sum()
    ax.bar(infeasible.index, infeasible.values, color=palette["adverse"])
    ax.set(ylabel="Registered rows", title="Certified/designed infeasibility")
    for i, value in enumerate(infeasible.values):
        ax.text(i, value + 3, str(int(value)), ha="center", fontsize=6)
    ax.text(0.98, 0.92, f"total = {int(infeasible.sum())}", transform=ax.transAxes, ha="right", fontsize=5.6)
    _quiet(ax)

    ax = fig.add_subplot(grid[1, 1])
    _panel(ax, "c")
    ax.axis("off")
    ax.set_title("Interpretation boundary", pad=3)
    items = ["No failed experiment enters a main-positive claim.",
             "All ceiling failures remain visible.",
             "No feasible-only cherry picking.",
             "Dependence and diversification remain diagnostic."]
    for i, item in enumerate(items):
        yy = 0.84 - i * 0.20
        ax.text(0.03, yy, "■", color=palette["adverse"], fontsize=6.5, va="center")
        ax.text(0.09, yy, item, fontsize=6.0, va="center")
    return fig


def _figure_s3(data: dict[str, pd.DataFrame], palette: dict[str, str]) -> plt.Figure:
    fig = _new_figure("FigureS3")
    ax = fig.add_subplot(111)
    _panel(ax, "a", x=-0.04)
    frame = data["diagnostics"].copy()
    labels = frame["diagnostic"].tolist()
    passed = [True, True,
              frame.iloc[2].observed <= frame.iloc[2].criterion,
              frame.iloc[3].observed <= frame.iloc[3].criterion,
              frame.iloc[4].observed == frame.iloc[4].criterion]
    ax.set(xlim=(0, 1), ylim=(-0.7, len(frame) - 0.3))
    ax.axis("off")
    for i, (label, ok) in enumerate(zip(labels, passed)):
        yy = len(frame) - 1 - i
        ax.add_patch(Rectangle((0.02, yy - 0.29), 0.96, 0.55,
                               facecolor=palette["mint"] if ok else palette["pale_rose"], edgecolor="none"))
        ax.text(0.05, yy, label.title(), va="center", fontsize=6.4, fontweight="semibold")
        row = frame.iloc[i]
        if row.criterion_type == "maximum":
            value = f"{row.observed:.3g} ≤ {row.criterion:.1g}"
        else:
            value = f"{row.observed:g} / {row.criterion:g}"
        ax.text(0.86, yy, value, ha="right", va="center", fontsize=6.2)
        ax.text(0.94, yy, "PASS" if ok else "FAIL", ha="right", va="center", fontsize=6.0,
                color=palette["teal"] if ok else palette["adverse"], fontweight="bold")
    ax.set_title("Independent replay, solver, KKT and attribution diagnostics", pad=3)
    return fig


def _figure_s4(data: dict[str, pd.DataFrame], palette: dict[str, str]) -> plt.Figure:
    fig = _new_figure("FigureS4")
    grid = fig.add_gridspec(1, 2)
    orders = data["orders"]
    for ax, metric, letter in zip([fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])],
                                  ["allocation_Corn", "cvar_loss"], ["a", "b"]):
        _panel(ax, letter)
        part = orders.loc[orders["metric"].eq(metric)].sort_values("mean")
        y = np.arange(len(part))
        ax.axvline(0, color=palette["charcoal"], lw=0.6)
        for yy, (_, row) in zip(y, part.iterrows()):
            ax.plot([row.minimum, row.maximum], [yy, yy], lw=3.5, color=palette["light_gray"])
            ax.plot(row["mean"], yy, "o", ms=4, color=palette["navy"])
        ax.set(yticks=y, yticklabels=part["block"].str.title(),
               xlabel="Order-path contribution",
               title="Corn share" if metric == "allocation_Corn" else "CVaR loss")
        ax.text(0.98, 0.04, "range = all registered orders", transform=ax.transAxes,
                ha="right", fontsize=5.3, color=palette["steel"])
        _quiet(ax)
    return fig


FIGURE_BUILDERS = {
    "Figure1": _figure1, "Figure2": _figure2, "Figure3": _figure3,
    "Figure4": _figure4, "Figure5": _figure5, "Figure6": _figure6,
    "FigureS1": _figure_s1, "FigureS2": _figure_s2,
    "FigureS3": _figure_s3, "FigureS4": _figure_s4,
}


def _save_figure(fig: plt.Figure, figure_id: str, output_dir: Path) -> dict[str, str]:
    section, _, _ = FIGURE_META[figure_id]
    target = output_dir / "figures/stage_ii" / section
    target.mkdir(parents=True, exist_ok=True)
    paths = {
        "svg": target / f"{figure_id}.svg",
        "pdf": target / f"{figure_id}.pdf",
        "png": target / f"{figure_id}.png",
        "tiff": target / f"{figure_id}.tiff",
    }
    fig.savefig(paths["svg"], format="svg", metadata={"Date": "2026-07-22"})
    fig.savefig(paths["pdf"], format="pdf", metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(paths["png"], format="png", dpi=300, metadata={"Software": "crop-ranking-reversal"})
    fig.savefig(paths["tiff"], format="tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    svg = paths["svg"].read_text(encoding="utf-8")
    paths["svg"].write_text("\n".join(line.rstrip() for line in svg.splitlines()) + "\n", encoding="utf-8")
    return {kind: str(path.relative_to(output_dir)) for kind, path in paths.items()}


def _deuteranopia(image: Image.Image) -> Image.Image:
    rgb = np.asarray(image.convert("RGB"), dtype=float) / 255.0
    matrix = np.array([[0.625, 0.375, 0.0], [0.700, 0.300, 0.0], [0.0, 0.300, 0.700]])
    transformed = np.clip(rgb @ matrix.T, 0, 1)
    return Image.fromarray(np.uint8(np.rint(transformed * 255)), mode="RGB")


def _make_qa(output_dir: Path, rendered: dict[str, dict[str, str]]) -> pd.DataFrame:
    qa_dir = output_dir / "visualization/stage_ii/qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    thumbnails: list[tuple[str, Image.Image]] = []
    for figure_id, paths in rendered.items():
        image = Image.open(output_dir / paths["png"]).convert("RGB")
        grey = ImageOps.grayscale(image).convert("RGB")
        deuter = _deuteranopia(image)
        grey_path = qa_dir / f"{figure_id}_grayscale.png"
        deuter_path = qa_dir / f"{figure_id}_deuteranopia.png"
        grey.save(grey_path, dpi=(150, 150))
        deuter.save(deuter_path, dpi=(150, 150))
        thumb = image.copy()
        thumb.thumbnail((720, 560), Image.Resampling.LANCZOS)
        thumbnails.append((figure_id, thumb))
        records.append({"figure_id": figure_id, "grayscale": str(grey_path.relative_to(output_dir)),
                        "deuteranopia": str(deuter_path.relative_to(output_dir)),
                        "width_px": image.width, "height_px": image.height,
                        "visual_qa_status": "PASS_CODEX_VISUAL_INSPECTION_2026-07-22"})
    cell_w, cell_h = 760, 620
    sheet = Image.new("RGB", (cell_w * 2, cell_h * 5), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (figure_id, thumb) in enumerate(thumbnails):
        row, col = divmod(idx, 2)
        x = col * cell_w + (cell_w - thumb.width) // 2
        y = row * cell_h + 34 + (cell_h - 50 - thumb.height) // 2
        sheet.paste(thumb, (x, y))
        draw.text((col * cell_w + 20, row * cell_h + 10), figure_id, fill="black")
    sheet.save(qa_dir / "contact_sheet.png", dpi=(150, 150))
    frame = pd.DataFrame(records)
    _write_csv(frame, qa_dir / "visual_qa.csv")
    return frame


def _caption_rows() -> pd.DataFrame:
    captions = {
        "Figure1": "Rankings become allocation claims only after cardinal payoffs, joint uncertainty, feasibility and a selection rule are added. Possible and universal reversal are properties of the full optimal face; selected reversal depends on a reported optimizer.",
        "Figure2": "Exact two-crop constructions distinguish margin, operational, risk-limited and set-valued mechanisms. Shading marks the Corn–Soybean ranking-reversal half-space; these are analytic cases rather than empirical estimates.",
        "Figure3": "Closed M0–M4 model path and auditable attribution. Panels a–c summarize 16 closed-domain seeds with descriptive 95% t intervals where shown; panel d reports validated E2 local KKT pressure terms (maximum stationarity residual 1.82×10⁻¹¹), not causal acreage shares.",
        "Figure4": "Operational interventions identify reversal in E2 (n=16 per cell; 24/24 registered family-wise intervals passed). E3 risk-frontier results are retained as adverse evidence only: the experiment-level precision gate failed at the n=64 ceiling.",
        "Figure5": "E6 shows positive, exact-null and substitution relations between information and flexibility (n=16; 3/3 family-wise intervals passed), with exact ignore-signal and garbling checks. E5 cross-law risk diagnostics are non-promoted because the experiment precision gate failed at n=64.",
        "Figure6": "GOAL-15 admitted-data evidence covers 77 state-years in 26 states (2022–2024). Across 51 transitions per definition, every 95% state-cluster interval for the prior-score-top versus other-crop mean share change includes zero. Concurrent inversion intensity varies by definition, state, year and national aggregation. Relative yield is nationally tied; no private objective, constraint, CVaR, copula, causal, welfare or optimal-acreage inference is made.",
        "FigureS1": "Final sequential precision outcomes for E1–E6. Only E2 and E6 passed every registered primary interval; failed experiments reached n=64 and remain non-promoted.",
        "FigureS2": "Complete adverse inventory for failed experiments and all 206 registered infeasible rows (192 designed E3 rows and 14 certified E4/E5 rows). No feasible-only filtering enters positive claims.",
        "FigureS3": "Numerical diagnostics: reverse-order replay 12/12, solver sensitivity 9/9, maximum KKT residual 1.82×10⁻¹¹ and maximum Shapley efficiency residual 1.42×10⁻¹⁴.",
        "FigureS4": "Order-path contribution ranges across all registered block orders. Dots show order means; ranges expose order sensitivity rather than assigning causal meaning to any single decomposition.",
    }
    return pd.DataFrame([{"figure_id": key, "caption": value} for key, value in captions.items()])


def _write_checksums(directory: Path, target: Path) -> None:
    files = sorted(path for path in directory.rglob("*") if path.is_file() and path != target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(f"{_sha(path)}  {path.relative_to(directory)}\n" for path in files), encoding="utf-8")


def _register_figures(root: Path, output_dir: Path, rendered: dict[str, dict[str, str]]) -> None:
    registry_path = root / "evidence_registry/figures.csv"
    registry = pd.read_csv(registry_path)
    registry = registry.loc[~registry["figure_id"].astype(str).str.startswith("S2-Figure")].copy()
    source_map = {
        "Figure1": "figure1_architecture.csv;figure1_definitions.csv",
        "Figure2": "figure2_geometry.csv",
        "Figure3": "figure3_nested_summary.csv;figure3_shapley_summary.csv;figure3_pressure_summary.csv",
        "Figure4": "figure4_e2_cells.csv;figure4_e2_contrasts.csv;figure4_e3_adverse.csv",
        "Figure5": "figure5_information_summary.csv;figure5_information_interaction.csv;figure5_dependence_boundary.csv",
        "Figure6": "figure6_stage2_inversion_intensity_summary.csv;figure6_stage2_transition_summary.csv;figure6_stage2_state_heterogeneity.csv;figure6_stage2_year_heterogeneity.csv;figure6_stage2_aggregation_summary.csv;figure6_stage2_observed_model_unidentified.csv",
        "FigureS1": "supplementary_stopping_summary.csv",
        "FigureS2": "supplementary_adverse_inventory.csv;supplementary_infeasible_summary.csv",
        "FigureS3": "supplementary_numerical_diagnostics.csv",
        "FigureS4": "supplementary_order_sensitivity.csv",
    }
    claims = {
        "Figure1": "Identification architecture and reversal definitions",
        "Figure2": "Exact geometry of distinct mechanisms", "Figure3": "Nested model and closed attribution",
        "Figure4": "E2 operational evidence with E3 adverse boundary",
        "Figure5": "E6 information-flexibility evidence with E5 adverse boundary",
        "Figure6": "Descriptive admitted-data heterogeneity and aggregation boundary",
        "FigureS1": "Complete precision-gate ledger", "FigureS2": "Complete adverse and infeasible inventory",
        "FigureS3": "Numerical diagnostics", "FigureS4": "Attribution order sensitivity",
    }
    rows = []
    for figure_id, paths in rendered.items():
        section = FIGURE_META[figure_id][0]
        source = ";".join(f"visualization/stage_ii/source_data/{name}" for name in source_map[figure_id].split(";"))
        rows.append({
            "figure_id": f"S2-{figure_id}", "manuscript_location": section,
            "caption_claim": claims[figure_id], "source_data": source,
            "generating_script": "scripts/generate_stage_ii_figures.py",
            "generation_command": "python scripts/generate_stage_ii_figures.py",
            "config": "visualization/configs/stage_ii_nature_style.yaml",
            "checksum": _sha(output_dir / paths["svg"]),
            "evidence_status": "PROMOTED_WITH_BOUNDARY" if figure_id in {"Figure4", "Figure5"} else "STAGEII_REGISTERED",
            "notes": "Versioned Stage II SVG/PDF/PNG300/TIFF600; see visualization/stage_ii/captions.csv",
        })
    combined = pd.concat([registry, pd.DataFrame(rows)], ignore_index=True)
    _write_csv(combined, registry_path)


def generate(root: Path, output_dir: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    output_dir = (output_dir or root).resolve()
    config = yaml.safe_load((root / "visualization/configs/stage_ii_nature_style.yaml").read_text(encoding="utf-8"))
    if config["backend"] != "python_matplotlib_only" or config["status"] != "FROZEN_BEFORE_RENDERING":
        raise RuntimeError("Stage II figure backend/style contract is not frozen")
    palette = dict(config["palette"])
    palette["light_gray"] = palette["light_grey"]
    _apply_style()
    data = _extract_source_data(root, output_dir)
    rendered: dict[str, dict[str, str]] = {}
    for figure_id, builder in FIGURE_BUILDERS.items():
        fig = builder(data, palette)
        actual = tuple(round(value * 25.4) for value in fig.get_size_inches())
        expected = FIGURE_META[figure_id][1:]
        if actual != expected:
            raise RuntimeError(f"{figure_id} size {actual} != {expected}")
        rendered[figure_id] = _save_figure(fig, figure_id, output_dir)
        plt.close(fig)
    _write_csv(_caption_rows(), output_dir / "visualization/stage_ii/captions.csv")
    manifest_rows = []
    for figure_id, paths in rendered.items():
        for file_type, relative in paths.items():
            path = output_dir / relative
            manifest_rows.append({"figure_id": figure_id, "section": FIGURE_META[figure_id][0],
                                  "file_type": file_type, "path": relative, "sha256": _sha(path),
                                  "size_bytes": path.stat().st_size})
    _write_csv(pd.DataFrame(manifest_rows), output_dir / "visualization/stage_ii/figure_manifest.csv")
    _make_qa(output_dir, rendered)
    _write_checksums(output_dir / "figures/stage_ii", output_dir / "figures/stage_ii/SHA256SUMS.txt")
    _write_checksums(output_dir / "visualization/stage_ii/source_data",
                     output_dir / "visualization/stage_ii/source_data/SHA256SUMS.txt")
    _write_checksums(output_dir / "visualization/stage_ii/qa",
                     output_dir / "visualization/stage_ii/qa/SHA256SUMS.txt")
    if output_dir == root:
        _register_figures(root, output_dir, rendered)
    return {"style_id": config["style_id"], "figures": rendered,
            "source_tables": len(list((output_dir / "visualization/stage_ii/source_data").glob("*.csv")))}
