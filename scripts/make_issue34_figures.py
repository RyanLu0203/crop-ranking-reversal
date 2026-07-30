#!/usr/bin/env python3
"""Generate the six final manuscript figures from solver-generated outputs."""

from __future__ import annotations

import os
import csv
import hashlib
import json
import re
from pathlib import Path
import shutil

# Matplotlib's PDF backend otherwise embeds the wall-clock creation time.
os.environ.setdefault("SOURCE_DATE_EPOCH", "1785081600")

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import (
    BoundaryNorm,
    LinearSegmentedColormap,
    ListedColormap,
    TwoSlopeNorm,
)
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Patch, Rectangle
import numpy as np
import pandas as pd
from matplotlib.text import Text
from PIL import Image, ImageDraw, ImageOps
from scipy.stats import gaussian_kde

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["svg.hashsalt"] = "issue34-scientific-reconstruction"
plt.rcParams["pdf.fonttype"] = 42

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "reconstruction" / "issue34" / "outputs"
OUT = ROOT / "figures" / "issue34"
SRC = OUT / "source_data"
QA = ROOT / "audits" / "issue40_visual_qa"
OUT.mkdir(parents=True, exist_ok=True)
SRC.mkdir(parents=True, exist_ok=True)
QA.mkdir(parents=True, exist_ok=True)

# User-approved Nature reference palette (27 July 2026).
INK = "#024E52"
GREY = "#8F9092"
LIGHT = "#F3F3F3"
CORNF = "#32A4B4"
SOY = "#33C5B2"
WHEAT = "#8A83A0"
PURPLE = "#8A83A0"
RED = "#776F76"
TEAL = "#33C5B2"
PALE_GREEN = "#D5EADA"
PALE_TEAL = "#9AD8C8"
PALE_BLUE = "#B2C9CE"
PALE_GREY = "#D9DBDD"
SAGE_GREY = "#A3B1AE"
CROP_COLORS = {"Corn": CORNF, "Soybean": SOY, "Winter Wheat": WHEAT}
INFO_CMAP = LinearSegmentedColormap.from_list(
    "issue34_information",
    [LIGHT, PALE_GREEN, PALE_TEAL, SOY, CORNF, INK],
)
CROSS_CMAP = LinearSegmentedColormap.from_list(
    "issue36_cross_difference",
    [PURPLE, PALE_GREY, LIGHT, PALE_GREEN, TEAL],
)


def style() -> None:
    mpl.rcParams.update(
        {
            "font.size": 6.3,
            "axes.labelsize": 6.3,
            "axes.titlesize": 7.0,
            "xtick.labelsize": 5.7,
            "ytick.labelsize": 5.7,
            "legend.fontsize": 5.8,
            "legend.title_fontsize": 6.0,
            "axes.linewidth": 0.65,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.major.size": 2.5,
            "ytick.major.size": 2.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": INK,
            "axes.labelcolor": INK,
            "legend.frameon": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "text.color": INK,
            "xtick.color": INK,
            "ytick.color": INK,
        }
    )


def panel(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.08, 1.10, label, transform=ax.transAxes,
        weight="bold", fontsize=8, va="bottom",
    )


FIGURE_RECORDS: list[dict[str, object]] = []
RENDERER_RECORDS: list[dict[str, object]] = []


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def renderer_qa(fig: plt.Figure, stem: str) -> None:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    canvas = fig.bbox
    bounds: list[str] = []
    headings: list[tuple[str, object]] = []
    for item in fig.findobj(match=Text):
        value = item.get_text().strip()
        if not value or not item.get_visible():
            continue
        box = item.get_window_extent(renderer=renderer)
        if (
            box.x0 < canvas.x0 - 2
            or box.y0 < canvas.y0 - 2
            or box.x1 > canvas.x1 + 2
            or box.y1 > canvas.y1 + 2
        ):
            bounds.append(value[:80])
        if (
            item in fig.texts
            or item in [axis.title for axis in fig.axes]
            or item in [axis._left_title for axis in fig.axes]
        ):
            headings.append((value, box))
    collisions: list[str] = []
    for index, (left_text, left_box) in enumerate(headings):
        for right_text, right_box in headings[index + 1:]:
            overlap_x = min(left_box.x1, right_box.x1) - max(left_box.x0, right_box.x0)
            overlap_y = min(left_box.y1, right_box.y1) - max(left_box.y0, right_box.y0)
            if overlap_x > 2 and overlap_y > 2:
                collisions.append(f"{left_text[:40]} | {right_text[:40]}")
    RENDERER_RECORDS.append({
        "figure_id": stem,
        "bounds_failure_count": len(bounds),
        "bounds_failures": "; ".join(bounds),
        "title_collision_count": len(collisions),
        "title_collisions": "; ".join(collisions),
    })


def save(fig: plt.Figure, stem: str) -> None:
    renderer_qa(fig, stem)
    svg_path = OUT / f"{stem}.svg"
    fig.savefig(svg_path, metadata={"Date": "2026-07-28"})
    # Matplotlib writes path-data lines with trailing spaces.  Normalize the
    # text export so repository checks remain clean and deterministic.
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )
    fig.savefig(
        OUT / f"{stem}.pdf",
        metadata={"CreationDate": None, "ModDate": None},
    )
    fig.savefig(
        OUT / f"{stem}.png",
        dpi=300,
        metadata={"Software": "crop-ranking-reversal final figures"},
    )
    fig.savefig(
        OUT / f"{stem}.tiff",
        dpi=600,
        pil_kwargs={"compression": "tiff_lzw"},
    )
    png = Image.open(OUT / f"{stem}.png").convert("RGB")
    for width_mm in (89, 183):
        target = QA / f"{width_mm}mm"
        target.mkdir(parents=True, exist_ok=True)
        width_px = int(round(width_mm / 25.4 * 300))
        height_px = int(round(png.height * width_px / png.width))
        png.resize((width_px, height_px), Image.Resampling.LANCZOS).save(
            target / f"{stem}.png", dpi=(300, 300)
        )
    width_mm, height_mm = (
        float(value * 25.4) for value in fig.get_size_inches()
    )
    record = {
        "figure_id": stem,
        "width_mm": round(width_mm, 3),
        "height_mm": round(height_mm, 3),
    }
    for extension in ("svg", "pdf", "png", "tiff"):
        path = OUT / f"{stem}.{extension}"
        record[f"{extension}_path"] = str(path.relative_to(ROOT))
        record[f"{extension}_sha256"] = sha256(path)
    FIGURE_RECORDS.append(record)
    plt.close(fig)


def copy_source(name: str) -> pd.DataFrame:
    src = DATA / name
    shutil.copy2(src, SRC / name)
    return pd.read_csv(src)


def copy_empirical_source(name: str) -> pd.DataFrame:
    src = ROOT / "empirical" / "goal16" / "outputs" / name
    shutil.copy2(src, SRC / name)
    return pd.read_csv(src)


def horizontal_raincloud(
    ax: plt.Axes,
    values: np.ndarray,
    y: float,
    estimate: float,
    interval_low: float,
    interval_high: float,
    color: str,
    seed: int,
    support: tuple[float, float],
) -> None:
    """Draw a compact, deterministic half-density + raw-draw uncertainty glyph."""
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    grid = np.linspace(support[0], support[1], 240)
    density = gaussian_kde(finite)(grid)
    density = 0.27 * density / density.max()
    ax.fill_between(
        grid, y, y + density,
        facecolor=color, alpha=0.72, edgecolor=INK, linewidth=0.45,
        zorder=1,
    )

    rng = np.random.default_rng(seed)
    display_n = min(72, finite.size)
    draw_index = np.sort(rng.choice(finite.size, size=display_n, replace=False))
    rain_y = y - 0.09 - 0.16 * rng.random(display_n)
    ax.scatter(
        finite[draw_index], rain_y,
        s=5.2, facecolor=color, edgecolor=INK, linewidth=0.22,
        alpha=0.62, zorder=2,
    )

    q25, median, q75 = np.quantile(finite, [0.25, 0.50, 0.75])
    ax.plot(
        [q25, q75], [y, y], color=GREY, linewidth=3.4,
        solid_capstyle="butt", zorder=3,
    )
    ax.plot(
        [median, median], [y - 0.045, y + 0.045],
        color="white", linewidth=1.0, zorder=4,
    )
    ax.errorbar(
        [estimate], [y],
        xerr=[[estimate - interval_low], [interval_high - estimate]],
        fmt="D", color=INK, ecolor=INK, elinewidth=0.8,
        capsize=1.8, markersize=3.2, markeredgewidth=0.3, zorder=5,
    )


def figure1() -> None:
    cal = copy_source("score_and_margin_calibration.csv").set_index("crop").loc[
        ["Corn", "Soybean", "Winter Wheat"]
    ].reset_index()
    pol = copy_source("policy_comparison.csv")
    full = pol.loc[pol["policy"] == "full_CVaR_operational"].iloc[0]
    crops = list(cal["crop"])
    fig = plt.figure(figsize=(7.205, 4.25))
    gs = fig.add_gridspec(
        1, 2, width_ratios=[1.34, 1.0],
        left=0.055, right=0.98, bottom=0.12, top=0.84, wspace=0.30,
    )

    ax = fig.add_subplot(gs[0, 0])
    ax.axis("off")
    ax.text(
        -0.03, 1.02, "a", transform=ax.transAxes,
        weight="bold", fontsize=8, va="bottom",
    )
    boxes = [
        (0.02, 0.76, "External performance index\nhistorical relative yield $s$", PALE_GREEN),
        (0.54, 0.76, "Cardinal evidence\nprice × yield − cost", PALE_TEAL),
        (0.54, 0.45, "Joint uncertainty\nmargins + dependence", PALE_BLUE),
        (0.02, 0.45, "Operational feasibility\nland, budget, rotation,\ncontract, capacities", PALE_GREY),
        (0.18, 0.09, "Selected allocation $x^*$\nexpected profit subject to loss-CVaR", LIGHT),
    ]
    for x, y, text, color in boxes:
        patch = FancyBboxPatch(
            (x, y), 0.42 if y > 0.2 else 0.62,
            0.15 if y > 0.2 else 0.18,
            boxstyle="round,pad=0.02",
            facecolor=color, edgecolor=INK, linewidth=0.7,
        )
        ax.add_patch(patch)
        ax.text(
            x + (0.21 if y > 0.2 else 0.31),
            y + (0.075 if y > 0.2 else 0.09),
            text, ha="center", va="center", fontsize=6.3,
        )
    arrows = [
        ((0.75, 0.76), (0.75, 0.63)),
        ((0.23, 0.46), (0.37, 0.28)),
        ((0.75, 0.46), (0.62, 0.28)),
    ]
    for start, end in arrows:
        ax.add_patch(
            FancyArrowPatch(
                start, end, arrowstyle="-|>", mutation_scale=8,
                color=GREY, linewidth=0.8,
            )
        )
    ax.add_patch(
        FancyArrowPatch(
            (0.23, 0.76), (0.42, 0.28), arrowstyle="-|>",
            mutation_scale=7, color=PURPLE, linewidth=0.75,
            linestyle=(0, (2, 2)), connectionstyle="arc3,rad=0.18",
        )
    )
    ax.text(
        0.19, 0.61, "rank comparison", rotation=-57,
        ha="center", va="center", fontsize=5.8, color=PURPLE,
    )

    right = gs[0, 1].subgridspec(3, 1, hspace=0.98)
    y = np.arange(len(crops))

    ax = fig.add_subplot(right[0, 0])
    panel(ax, "b")
    ax.barh(
        y, cal["historical_yield_potential_score"],
        color=[CROP_COLORS[c] for c in crops],
        edgecolor=INK, linewidth=0.35,
    )
    ax.set_yticks(y, crops)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Historical relative-yield index $s$")
    ax.set_title("Performance index", loc="left", pad=3)
    ax.invert_yaxis()
    for yi, value in zip(y, cal["historical_yield_potential_score"]):
        ax.text(value + 0.015, yi, f"{value:.3f}", va="center", fontsize=5.8)

    ax = fig.add_subplot(right[1, 0])
    panel(ax, "c")
    ax.errorbar(
        cal["mean_margin_real_2024_usd_per_acre"], y,
        xerr=cal["sd_margin_real_2024_usd_per_acre"], fmt="none",
        ecolor=GREY, elinewidth=1.2, capsize=2,
    )
    for yi, c, mean in zip(y, crops, cal["mean_margin_real_2024_usd_per_acre"]):
        ax.scatter(
            mean, yi, s=38, marker={"Corn": "o", "Soybean": "s",
                                   "Winter Wheat": "^"}[c],
            color=CROP_COLORS[c], edgecolor=INK, linewidth=0.4, zorder=3,
        )
    ax.set_yticks(y, [])
    ax.invert_yaxis()
    ax.set_xlabel("Mean margin ± s.d. (US\\$ acre$^{-1}$)")
    ax.set_title("Cardinal margins", loc="left", pad=3)

    ax = fig.add_subplot(right[2, 0])
    panel(ax, "d")
    alloc = np.array([full[f"acres_{c}"] for c in crops])
    ax.barh(
        y, alloc, color=[CROP_COLORS[c] for c in crops],
        edgecolor=INK, linewidth=0.35,
    )
    ax.set_yticks(y, [])
    ax.invert_yaxis()
    ax.set_xlim(0, 0.7)
    ax.set_xlabel("Selected land share $x^*$")
    ax.set_title("Selected allocation: complete rank reversal", loc="left", pad=3)
    for yi, value in zip(y, alloc):
        ax.text(value + 0.012, yi, f"{value:.3f}", va="center", fontsize=5.8)
    fig.suptitle(
        "Ranking becomes allocation only through margins, joint risk and operations",
        x=0.055, ha="left", fontsize=9.0, weight="bold",
    )
    save(fig, "Figure1")


def figure2() -> None:
    phase = copy_source("reversal_phase_diagram.csv")
    front = copy_source("reversal_frontier_summary.csv")
    fams = ["gaussian", "student_t", "clayton"]
    fig, axes = plt.subplots(
        1, 4, figsize=(7.205, 2.95),
        gridspec_kw={"width_ratios": [1, 1, 1, 1.18]},
    )
    cmap = ListedColormap([PALE_GREY, PALE_TEAL, INK])
    family_labels = {
        "gaussian": "Gaussian",
        "student_t": "Student-$t$",
        "clayton": "Clayton",
    }
    for j, fam in enumerate(fams):
        ax = axes[j]
        sub = phase[phase["copula_family"] == fam]
        piv = sub.pivot(index="kendall_tau", columns="risk_tolerance", values="classification")
        code = piv.replace({
            "no_reversal": 0,
            "selected_pairwise_reversal": 1,
            "selected_complete_rank_reversal": 2,
            "selected_strong_reversal": 2,
        }).to_numpy(dtype=float)
        ax.imshow(code, origin="lower", aspect="auto", vmin=0, vmax=2, cmap=cmap)
        ax.set_xticks(np.arange(len(piv.columns))[::2], [f"{v:.1f}" for v in piv.columns[::2]])
        ax.set_yticks(np.arange(len(piv.index)), [f"{v:.2f}" for v in piv.index])
        ax.set_xlabel("Risk-tolerance index")
        if j == 0:
            ax.set_ylabel("Kendall's $\\tau$")
        ax.set_title(family_labels[fam], loc="left")
        panel(ax, chr(ord("a") + j))
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.5)
    ax = axes[3]
    for fam, color, marker in zip(fams, [INK, PURPLE, TEAL], ["o", "s", "^"]):
        sub = front[front["copula_family"] == fam].sort_values("kendall_tau")
        ax.plot(sub["kendall_tau"], sub["first_selected_reversal_risk_tolerance"],
                marker=marker, color=color, lw=1.3, label=family_labels[fam])
    ax.set_xlabel("Kendall's $\\tau$")
    ax.set_ylabel("First reversal\nrisk-tolerance index")
    ax.set_ylim(-0.03, 1.03)
    ax.legend(title="Copula family", handlelength=1.6)
    ax.set_title("Selected-reversal boundary", loc="left")
    panel(ax, "d")
    legend_handles = [
        Patch(facecolor=PALE_GREY, edgecolor=GREY, label="No reversal"),
        Patch(facecolor=PALE_TEAL, edgecolor=GREY, label="Pairwise only"),
        Patch(facecolor=INK, edgecolor=INK, label="Complete rank"),
        Patch(
            facecolor="white", edgecolor=PURPLE, hatch="///",
            label="Strong exclusion unavailable†",
        ),
    ]
    fig.legend(
        handles=legend_handles, loc="lower left", bbox_to_anchor=(0.06, 0.015),
        ncol=4, frameon=False, handlelength=1.4, columnspacing=1.4,
    )
    fig.text(
        0.94, 0.028,
        "† positive lower bounds",
        ha="right", va="bottom", fontsize=5.5, color=PURPLE,
    )
    fig.suptitle(
        "Ranking reversal occupies a family- and risk-dependent phase",
        x=0.06, ha="left", fontsize=9.0, weight="bold",
    )
    fig.subplots_adjust(top=0.80, bottom=0.24, wspace=0.42)
    save(fig, "Figure2")


def figure3() -> None:
    div = copy_source("diversification_failure.csv")
    copy_source("diversification_sensitivity.csv")
    policies = div[div["row_type"] == "registered_policy"].drop_duplicates("policy")
    order = [
        "x0_expected_profit_under_matched_gaussian",
        "xMV_variance_target_selected",
        "xT_CVaR_under_student_t_evaluation",
    ]
    rows = policies.set_index("policy").loc[order].reset_index()
    frontier = div[div["row_type"] == "mean_variance_frontier"].sort_values("gamma")
    fig = plt.figure(figsize=(7.205, 4.35))
    grid = fig.add_gridspec(
        2, 2, height_ratios=[1.35, 1.0],
        left=0.085, right=0.94, bottom=0.19, top=0.84,
        hspace=0.58, wspace=0.36,
    )
    ax = fig.add_subplot(grid[0, :])
    ax.plot(
        frontier["gaussian_profit_variance"],
        frontier["gaussian_expected_profit"],
        color=GREY, lw=1.0, label="301-point Gaussian frontier",
    )
    strong = frontier["strong_diversification_failure"].fillna(False).to_numpy()
    ax.plot(
        frontier.loc[strong, "gaussian_profit_variance"],
        frontier.loc[strong, "gaussian_expected_profit"],
        color=TEAL, lw=2.4, solid_capstyle="round",
        label="Student-$t$ failure interval",
    )
    x0 = rows.iloc[0]
    xmv = rows.iloc[1]
    xt = rows.iloc[2]
    target = 100 * float(xmv["variance_reduction_target"])
    target_variance = float(x0["gaussian_profit_variance"]) * (1 - target / 100)
    ax.axvline(
        target_variance, color=PURPLE, lw=0.9, ls=(0, (2, 2)),
        label=f"{target:.0f}% variance target",
    )
    ax.scatter(
        [x0["gaussian_profit_variance"], xt["gaussian_profit_variance"]],
        [x0["gaussian_expected_profit"], xt["gaussian_expected_profit"]],
        color=[PURPLE, INK], marker="o", edgecolor=INK, linewidth=0.45,
        s=30, zorder=4,
    )
    ax.scatter(
        [xmv["gaussian_profit_variance"]],
        [xmv["gaussian_expected_profit"]],
        color=TEAL, marker="*", edgecolor=INK, linewidth=0.45,
        s=68, zorder=5, label="Selected Gaussian mean–variance policy",
    )
    for row, label, offset in [
        (x0, "$x^0$", (5, -12)),
        (xmv, "$x^{MV}$", (5, 5)),
        (xt, "$x^T$", (-24, 5)),
    ]:
        ax.annotate(
            label,
            (row["gaussian_profit_variance"], row["gaussian_expected_profit"]),
            xytext=offset, textcoords="offset points", fontsize=5.8,
        )
    ax.set_xlabel("Gaussian profit variance (US\\$${}^{2}$ acre$^{-2}$)")
    ax.set_ylabel("Gaussian expected profit (US\\$ acre$^{-1}$)")
    ax.set_xlim(2400, 6600)
    ax.set_xticks([3000, 4000, 5000, 6000])
    ax.set_title("Gaussian construction space", loc="left")
    ax.legend(loc="lower right", ncol=2, handlelength=1.5, columnspacing=1.2)
    panel(ax, "a")

    ax = fig.add_subplot(grid[1, 0])
    bottom = np.zeros(len(rows))
    x = np.arange(len(rows))
    hatches = {"Corn": "///", "Soybean": "\\\\\\", "Winter Wheat": "..."}
    for crop in ["Corn", "Soybean", "Winter Wheat"]:
        vals = rows[f"allocation_{crop.replace(' ', '_')}"].to_numpy()
        ax.bar(
            x, vals, bottom=bottom, color=CROP_COLORS[crop], label=crop,
            edgecolor=INK, linewidth=0.35, hatch=hatches[crop],
        )
        bottom += vals
    ax.set_xticks(
        x, ["benchmark\n$x^0$", "Gaussian\n$x^{MV}$", "tail-aware\n$x^T$"],
        fontsize=5.8,
    )
    ax.set_ylabel("Land share")
    ax.set_ylim(0, 1.0)
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.32))
    ax.set_title("Optimized policy allocations", loc="left")
    panel(ax, "b")

    ax = fig.add_subplot(grid[1, 1])
    values = rows["evaluation_loss_CVaR"].to_numpy()
    y = np.arange(len(values))
    ceiling = float(rows["risk_ceiling"].iloc[0])
    ax.axvline(ceiling, color=RED, ls="--", lw=1.1)
    ax.scatter(
        values, y, s=52, color=[PURPLE, TEAL, INK],
        marker="o", edgecolor=INK, linewidth=0.4, zorder=3,
    )
    for yi, value in zip(y, values):
        ax.text(value + 0.25, yi, f"{value:.1f}", va="center", fontsize=5.8)
    ax.set_yticks(y, ["$x^0$", "$x^{MV}$", "$x^T$"], fontsize=5.8)
    ax.invert_yaxis()
    ax.set_xlim(min(values.min(), ceiling) - 0.8, values.max() + 1.8)
    ax.set_xlabel(
        "Student-$t$ evaluation-law loss-CVaR\n"
        "(US\\$ acre$^{-1}$; larger is worse)"
    )
    ax.text(
        ceiling - 0.4, 1.95, f"ceiling {ceiling:.1f}",
        ha="right", va="bottom", fontsize=5.8, color=RED,
    )
    ax.set_title("Heavy-tail evaluation", loc="left")
    panel(ax, "c")
    reduction = 100 * float(xmv["gaussian_variance_reduction_fraction"])
    fig.suptitle(
        f"Gaussian variance falls {reduction:.1f}%, but Student-$t$ tail safety fails",
        x=0.055, ha="left", fontsize=9.0, weight="bold",
    )
    save(fig, "Figure3")


def figure4() -> None:
    margin = copy_source("margin_mechanism.csv")
    risk = copy_source("risk_induced_reversal.csv")
    sensitivity = copy_source("risk_shock_sensitivity.csv")
    operation = copy_source("operational_mechanism.csv")
    fig, axes = plt.subplots(
        2, 2, figsize=(7.205, 4.65),
        gridspec_kw={"height_ratios": [1.0, 1.0]},
    )
    ax = axes[0, 0]
    for _, row in margin.iterrows():
        crop = row["crop"]
        ax.scatter(
            row["score"], row["mean_margin_real_2024_usd_per_acre"],
            s=50, marker={"Corn": "o", "Soybean": "s",
                          "Winter Wheat": "^"}[crop],
            color=CROP_COLORS[crop], edgecolor=INK, linewidth=0.4,
        )
        ax.annotate(crop.replace("Winter ", ""), (
            row["score"], row["mean_margin_real_2024_usd_per_acre"]
        ), xytext=(4, 3), textcoords="offset points", fontsize=5.8)
    ax.set_xlabel("Historical relative-yield score")
    ax.set_ylabel("Mean margin (US\\$ acre$^{-1}$)")
    ax.set_xlim(0.74, 0.905)
    ax.set_title("Margin-induced signature", loc="left")
    panel(ax, "a")

    ax = axes[0, 1]
    risk = risk.sort_values("risk_tolerance")
    ax.plot(
        risk["risk_tolerance"], risk["allocation_high"],
        color=SOY, marker="o", ms=3.2, lw=1.0, ls="-", label="Soybean",
    )
    ax.plot(
        risk["risk_tolerance"], risk["allocation_low"],
        color=CORNF, marker="s", ms=3.2, lw=1.0, ls="--", label="Corn",
    )
    ax.fill_between(
        risk["risk_tolerance"], risk["allocation_low"], risk["allocation_high"],
        where=risk["allocation_high"] < risk["allocation_low"],
        color=PALE_GREEN, alpha=0.8,
    )
    ax.set_xlabel("Risk-tolerance index (tight $\\rightarrow$ loose)")
    ax.set_ylabel("Land share")
    ax.set_xlim(-0.02, 1.02)
    ax.set_xticks(np.linspace(0, 1, 6))
    ax.set_title("Focal risk-induced crossing", loc="left")
    ax.legend()
    panel(ax, "b")

    ax = axes[1, 0]
    probabilities = sorted(
        sensitivity["adverse_event_probability_target"].unique()
    )
    magnitudes = sorted(
        sensitivity["shock_share_of_mean_real_gross_revenue"].unique()
    )
    class_code = {"no_crossing": 0, "crossing": 1, "infeasible": 2}
    matrix = (
        sensitivity.assign(code=sensitivity["classification"].map(class_code))
        .pivot(
            index="shock_share_of_mean_real_gross_revenue",
            columns="adverse_event_probability_target",
            values="code",
        )
        .reindex(index=magnitudes, columns=probabilities)
    )
    ax.imshow(
        matrix.to_numpy(), origin="lower", aspect="auto",
        cmap=ListedColormap([PALE_GREY, PALE_TEAL, RED]), vmin=-0.5, vmax=2.5,
    )
    ax.set_xticks(
        np.arange(len(probabilities)),
        [f"{100 * value:.1f}" for value in probabilities],
    )
    ax.set_yticks(
        np.arange(len(magnitudes)),
        [f"{100 * value:.1f}" for value in magnitudes],
    )
    ax.set_xlabel("Adverse-event probability (%)")
    ax.set_ylabel("Shock magnitude (% of mean gross revenue)")
    ax.set_title("Downside-stress classification", loc="left")
    for row_index, magnitude in enumerate(magnitudes):
        for column_index, probability in enumerate(probabilities):
            row = sensitivity.loc[
                np.isclose(
                    sensitivity["shock_share_of_mean_real_gross_revenue"],
                    magnitude,
                )
                & np.isclose(
                    sensitivity["adverse_event_probability_target"],
                    probability,
                )
            ].iloc[0]
            focal_case = bool(row["focal_case"])
            if row["classification"] == "crossing":
                ax.scatter(
                    column_index, row_index, marker="o", s=8,
                    facecolor="none", edgecolor=INK, linewidth=0.45,
                )
            elif row["classification"] == "infeasible":
                ax.scatter(
                    column_index, row_index, marker="x", s=10,
                    color="white", linewidth=0.55,
                )
            if focal_case:
                ax.add_patch(
                    Rectangle(
                        (column_index - 0.43, row_index - 0.43), 0.86, 0.86,
                        fill=False, edgecolor=PURPLE, linewidth=0.75,
                        linestyle=(0, (2, 1)),
                    )
                )
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.5)
    panel(ax, "c")
    ax.legend(
        handles=[
            Patch(facecolor=PALE_GREY, edgecolor=GREY, label="No crossing"),
            Line2D(
                [0], [0], marker="o", linestyle="none", markerfacecolor=PALE_TEAL,
                markeredgecolor=INK, markersize=4, label="Crossing",
            ),
            Line2D(
                [0], [0], marker="x", linestyle="none", color=RED,
                markersize=4, label="Infeasible",
            ),
            Patch(
                facecolor="white", edgecolor=PURPLE, linestyle="--",
                label="Focal stress",
            ),
        ],
        loc="upper left", bbox_to_anchor=(0, -0.26), ncol=2,
        handlelength=1.4, columnspacing=1.2,
    )

    ax = axes[1, 1]
    rotation = operation[
        operation["operational_path"] == "soybean_rotation_tightening"
    ].sort_values("soybean_rotation_cap", ascending=False)
    ax.plot(
        rotation["soybean_rotation_cap"], rotation["allocation_high"],
        color=SOY, marker="o", ms=3.2, lw=1.0, ls="-", label="Soybean",
    )
    ax.plot(
        rotation["soybean_rotation_cap"], rotation["allocation_low"],
        color=CORNF, marker="s", ms=3.2, lw=1.0, ls="--", label="Corn",
    )
    ax.axvline(
        rotation["first_operational_crossing_cap"].iloc[0],
        color=GREY, ls="--", lw=0.9,
    )
    ax.invert_xaxis()
    ax.set_xlim(0.68, 0.07)
    ax.set_ylim(0.08, 0.72)
    ax.set_yticks([0.2, 0.4, 0.6])
    ax.set_xlabel("Soybean rotation cap (loose $\\rightarrow$ tight)")
    ax.set_ylabel("Land share")
    ax.set_title("Operational illustration: rotation cap", loc="left")
    ax.legend()
    panel(ax, "d")
    fig.suptitle(
        "Margin, downside risk and operations leave distinct reversal signatures",
        x=0.055, ha="left", fontsize=9.0, weight="bold",
    )
    fig.subplots_adjust(
        top=0.84, bottom=0.18, left=0.11, right=0.95,
        hspace=0.88, wspace=0.36,
    )
    save(fig, "Figure4")


def figure5() -> None:
    info = copy_source("information_flexibility.csv")
    paths = ["post_signal_acreage_reallocation", "state_shock_buffering_recourse"]
    fig, axes = plt.subplots(
        2, 2, figsize=(7.205, 4.55),
    )
    vmax = max(0.1, info["value_of_information"].max())
    value_images = []
    for column, path in enumerate(paths):
        ax = axes[0, column]
        sub = info[info["flexibility_path"] == path]
        piv = sub.pivot(
            index="signal_accuracy", columns="flexibility_level",
            values="value_of_information",
        )
        image = ax.imshow(
            piv.to_numpy(), origin="lower", aspect="auto",
            cmap=INFO_CMAP, vmin=0, vmax=vmax,
        )
        value_images.append(image)
        ax.set_xticks(
            np.arange(len(piv.columns)), [f"{value:.1f}" for value in piv.columns]
        )
        ax.set_yticks(
            np.arange(len(piv.index)), [f"{value:.1f}" for value in piv.index]
        )
        ax.set_xlabel("Flexibility level")
        if column == 0:
            ax.set_ylabel("Signal accuracy")
        ax.set_title(
            "Information value: acreage reallocation"
            if column == 0
            else "Information value: shock buffering",
            loc="left",
        )
        panel(ax, chr(ord("a") + column))
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.5)

    finite_cross = info["discrete_cross_difference"].dropna()
    cross_abs = max(0.01, float(finite_cross.abs().max()))
    cross_norm = TwoSlopeNorm(vmin=-cross_abs, vcenter=0.0, vmax=cross_abs)
    cross_map = CROSS_CMAP.copy()
    cross_map.set_bad("white")
    cross_images = []
    for column, path in enumerate(paths):
        ax = axes[1, column]
        sub = info[info["flexibility_path"] == path]
        piv = sub.pivot(
            index="signal_accuracy", columns="flexibility_level",
            values="discrete_cross_difference",
        )
        cross_im = ax.imshow(
            piv.to_numpy(), origin="lower", aspect="auto",
            cmap=cross_map, norm=cross_norm,
        )
        cross_images.append(cross_im)
        ax.set_xticks(
            np.arange(len(piv.columns)), [f"{value:.1f}" for value in piv.columns]
        )
        ax.set_yticks(
            np.arange(len(piv.index)), [f"{value:.1f}" for value in piv.index]
        )
        ax.set_xlabel("Upper flexibility $\\phi_2$")
        if column == 0:
            ax.set_ylabel("Upper accuracy $\\xi_2$")
        ax.set_title(
            "Interaction: reallocation $\\Delta_{\\xi,\\phi}V$"
            if column == 0
            else "Interaction: buffering $\\Delta_{\\xi,\\phi}V$",
            loc="left",
        )
        panel(ax, chr(ord("c") + column))
        values = piv.to_numpy()
        for row_index in range(values.shape[0]):
            for column_index in range(values.shape[1]):
                value = values[row_index, column_index]
                if not np.isfinite(value):
                    continue
                if abs(value) <= 1e-7:
                    symbol = "0"
                elif abs(value) >= 0.15 * cross_abs:
                    symbol = "+" if value > 0 else "−"
                else:
                    continue
                ax.text(
                    column_index, row_index, symbol,
                    ha="center", va="center", fontsize=5.4,
                    color=INK if abs(value) < 0.65 * cross_abs else "white",
                )
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.5)
    fig.subplots_adjust(
        top=0.84, bottom=0.12, left=0.08, right=0.89,
        hspace=0.60, wspace=0.32,
    )
    value_cax = fig.add_axes([0.915, 0.57, 0.012, 0.22])
    value_cb = fig.colorbar(value_images[-1], cax=value_cax)
    value_cb.set_label("Information value (US\\$ acre$^{-1}$)")
    cross_cax = fig.add_axes([0.915, 0.18, 0.012, 0.22])
    cross_cb = fig.colorbar(cross_images[-1], cax=cross_cax)
    cross_cb.set_label("Adjacent-grid cross-difference")
    cross_cb.set_ticks([-cross_abs, 0.0, cross_abs])
    fig.suptitle(
        "Information remains valuable, but its interaction with flexibility changes sign",
        x=0.055, ha="left", fontsize=9.0, weight="bold",
    )
    save(fig, "Figure5")


def figure6() -> None:
    ext = copy_source("external_descriptive_evidence.csv")
    copy_source("bootstrap_replications.csv")
    uncertainty = copy_source("uncertainty_summary.csv")
    rank_draws = copy_empirical_source("rank_metric_bootstrap_draws.csv")
    temporal_draws = copy_empirical_source("temporal_model_bootstrap_draws.csv")
    fig, axes = plt.subplots(
        1, 3, figsize=(7.205, 3.8),
        gridspec_kw={"width_ratios": [1.35, 0.92, 1.08]},
    )
    ax = axes[0]
    rates = ext.dropna(subset=["top_rank_reversal_rate"]).copy()
    y = np.arange(len(rates))
    for index, row in rates.reset_index(drop=True).iterrows():
        values = rank_draws.loc[
            rank_draws["ranking_definition"].eq(row["ranking_definition"]),
            "top_rank_disagreement",
        ].to_numpy()
        horizontal_raincloud(
            ax, values, index,
            float(row["top_rank_reversal_rate"]),
            float(row["top_rank_reversal_rate_ci_low"]),
            float(row["top_rank_reversal_rate_ci_high"]),
            PALE_TEAL, 400 + index, (0.0, 1.0),
        )
    definition_labels = {
        "operating_margin": "operating margin",
        "relative_yield": "relative yield",
        "standardized_revenue": "revenue",
        "total_cost_margin": "total-cost margin",
    }
    ax.set_yticks(
        y, [definition_labels[value] for value in rates["ranking_definition"]]
    )
    ax.set_xlim(0, 1)
    ax.set_xlabel("Top-rank disagreement rate")
    ax.set_ylim(-0.36, len(rates) - 0.58)
    ax.set_title("State-cluster bootstrap distributions", loc="left")
    panel(ax, "a")

    ax = axes[1]
    pair = uncertainty[
        uncertainty["metric"] == "selected_pairwise_reversal_frequency"
    ].iloc[0]
    rate = float(pair["estimate_mean"])
    low = float(pair["exact_binomial_95_low"])
    high = float(pair["exact_binomial_95_high"])
    ax.errorbar(
        [rate], [0], xerr=[[rate - low], [high - rate]],
        fmt="o", color=INK, ecolor=SAGE_GREY, elinewidth=0.9,
        capsize=2.5, markersize=4,
    )
    ax.set_xlim(0.8, 1.005)
    ax.set_ylim(-0.6, 0.6)
    ax.set_yticks([0], [f"{int(pair['event_count'])}/{int(pair['bootstrap_replications'])}"])
    ax.set_xlabel("Resample frequency")
    ax.set_title("Exact binomial interval", loc="left")
    panel(ax, "b")

    ax = axes[2]
    lagged = ext.loc[ext["evidence_layer"].eq("leakage_free_2024")].iloc[0]
    estimate = 100 * float(lagged["lagged_score_leader_acreage_share_effect"])
    low = 100 * float(lagged["lagged_effect_ci_low"])
    high = 100 * float(lagged["lagged_effect_ci_high"])
    lagged_draws = 100 * temporal_draws.loc[
        temporal_draws["ranking_definition"].eq("relative_yield")
        & temporal_draws["specification"].eq("primary_top"),
        "coefficient",
    ].to_numpy()
    ax.axvline(0, color=PURPLE, ls=(0, (2, 2)), lw=0.9)
    support = (
        min(float(np.quantile(lagged_draws, 0.001)), low) - 0.08,
        max(float(np.quantile(lagged_draws, 0.999)), high) + 0.08,
    )
    horizontal_raincloud(
        ax, lagged_draws, 0.0, estimate, low, high,
        PALE_BLUE, 406, support,
    )
    ax.set_xlim(*support)
    ax.set_ylim(-0.34, 0.46)
    ax.set_yticks([0], ["lagged effect"])
    ax.set_xlabel("Lagged change (percentage points)")
    ax.set_title("State-cluster bootstrap distribution", loc="left")
    panel(ax, "c")
    fig.suptitle(
        "External disagreement is descriptive and sensitive to definition and record length",
        x=0.055, ha="left", fontsize=9.0, weight="bold",
    )
    fig.subplots_adjust(
        top=0.79, bottom=0.25, left=0.13, right=0.96, wspace=0.60,
    )
    fig.legend(
        handles=[
            Patch(facecolor=PALE_TEAL, edgecolor=INK, label="bootstrap density"),
            Line2D(
                [0], [0], marker="o", linestyle="none", markersize=3.3,
                markerfacecolor=PALE_TEAL, markeredgecolor=INK,
                label="displayed bootstrap draws",
            ),
            Line2D(
                [0], [0], marker="D", color=INK, linewidth=0.8,
                markersize=3.3, label="estimate + 95% interval",
            ),
        ],
        loc="lower center", bbox_to_anchor=(0.55, 0.075),
        ncol=3, columnspacing=1.2, handlelength=1.6,
    )
    save(fig, "Figure6")


def supplementary_figure1() -> None:
    """Visualize the admissible-exclusion sensitivity without forcing a result."""
    summary = copy_source("strong_reversal_lower_bound_summary.csv")
    primary = summary.loc[np.isclose(summary["near_zero_tolerance"], 1e-4)].copy()
    order = [
        "principal_positive_lower_bounds",
        "all_zero_lower_bounds",
        "highest_ranked_crop_zero_lower_bound",
    ]
    primary = primary.set_index("lower_bound_specification").loc[order].reset_index()
    labels = ["Positive minima", "All minima zero", "Highest-ranked zero"]
    colors = [GREY, TEAL, PURPLE]
    markers = ["o", "s", "^"]
    fig, axes = plt.subplots(1, 2, figsize=(7.205, 2.55))

    ax = axes[0]
    y = np.arange(len(primary))
    ax.axvline(0, color=RED, lw=0.8, ls=(0, (2, 2)))
    for index, row in primary.iterrows():
        value = float(row["minimum_optimal_face_top_crop_allocation"])
        ax.plot(
            [0, value], [index, index], color=PALE_GREY, lw=1.2,
            solid_capstyle="round",
        )
        ax.scatter(
            value, index, color=colors[index], marker=markers[index],
            s=28, edgecolor=INK, linewidth=0.4, zorder=3,
        )
        ax.text(value + 0.002, index, f"{value:.3f}", va="center", fontsize=5.8)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(
        -0.005,
        max(primary["minimum_optimal_face_top_crop_allocation"]) + 0.025,
    )
    ax.set_xlabel("Minimum highest-ranked crop share on the optimal face")
    ax.set_title("Exit remains unused when admissible", loc="left")
    panel(ax, "a")

    ax = axes[1]
    categories = ["Pairwise", "Complete rank", "Strong exclusion"]
    x = np.arange(len(categories))
    width = 0.22
    for index, row in primary.iterrows():
        values = [
            row["selected_pairwise_reversal_cells"],
            row["selected_complete_rank_reversal_cells"],
            row["selected_strong_reversal_cells"],
        ]
        bars = ax.bar(
            x + (index - 1) * width, values, width,
            color=colors[index], edgecolor=INK, linewidth=0.35,
            hatch="///" if index == 0 else None, label=labels[index],
        )
        for bar, value in zip(bars, values):
            if value > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2, value + 2,
                    f"{int(value)}", ha="center", va="bottom", fontsize=5.5,
                )
    ax.set_xticks(x, categories)
    ax.set_ylim(0, 165)
    ax.set_ylabel("Selected cells (of 165)")
    ax.set_title("Reversal classifications at $10^{-4}$", loc="left")
    ax.legend(loc="upper right", handlelength=1.4)
    panel(ax, "b")
    fig.suptitle(
        "Relaxing crop lower bounds leaves strong exclusion at zero",
        x=0.055, ha="left", fontsize=9.0, weight="bold",
    )
    fig.subplots_adjust(
        top=0.77, bottom=0.22, left=0.13, right=0.96, wspace=0.48,
    )
    save(fig, "SupplementaryFigure1")


def accessibility_transform(image: Image.Image, mode: str) -> Image.Image:
    rgb = image.convert("RGB")
    if mode == "full":
        return rgb
    if mode == "grayscale":
        return ImageOps.grayscale(rgb).convert("RGB")
    matrices = {
        "deuteranopia": np.array(
            [[0.625, 0.375, 0.000],
             [0.700, 0.300, 0.000],
             [0.000, 0.300, 0.700]]
        ),
        "protanopia": np.array(
            [[0.567, 0.433, 0.000],
             [0.558, 0.442, 0.000],
             [0.000, 0.242, 0.758]]
        ),
    }
    pixels = np.asarray(rgb, dtype=float) / 255.0
    transformed = np.clip(pixels @ matrices[mode].T, 0.0, 1.0)
    return Image.fromarray(np.uint8(np.rint(transformed * 255.0)))


def contact_sheet(
    records: list[tuple[str, Image.Image]],
    target: Path,
    *,
    mode: str = "full",
    columns: int = 2,
) -> None:
    cell_width, cell_height = 1050, 760
    rows = int(np.ceil(len(records) / columns))
    sheet = Image.new(
        "RGB", (columns * cell_width, rows * cell_height), "white"
    )
    draw = ImageDraw.Draw(sheet)
    for index, (label, source) in enumerate(records):
        image = accessibility_transform(source, mode)
        image.thumbnail(
            (cell_width - 50, cell_height - 70), Image.Resampling.LANCZOS
        )
        row, column = divmod(index, columns)
        x0 = column * cell_width
        y0 = row * cell_height
        x = x0 + (cell_width - image.width) // 2
        y = y0 + 40 + (cell_height - 50 - image.height) // 2
        sheet.paste(image, (x, y))
        draw.text((x0 + 18, y0 + 14), label, fill=INK)
    sheet.save(target, dpi=(150, 150))


def finalize_outputs() -> None:
    manifest = OUT / "figure_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(FIGURE_RECORDS[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(FIGURE_RECORDS)
    renderer_path = QA / "renderer_qa.csv"
    with renderer_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(RENDERER_RECORDS[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(RENDERER_RECORDS)

    final_records = [
        (f"Figure {index}", Image.open(OUT / f"Figure{index}.png").convert("RGB"))
        for index in range(1, 7)
    ]
    for mode in ("full", "grayscale", "deuteranopia", "protanopia"):
        contact_sheet(
            final_records, QA / f"figure_contact_{mode}.png", mode=mode
        )
    for width_mm in (89, 183):
        records = [
            (
                f"Figure {index} · {width_mm} mm",
                Image.open(QA / f"{width_mm}mm" / f"Figure{index}.png").convert("RGB"),
            )
            for index in range(1, 7)
        ]
        contact_sheet(records, QA / f"figure_contact_{width_mm}mm.png")

    minimum_font = np.inf
    maximum_font = -np.inf
    for stem in [f"Figure{index}" for index in range(1, 7)] + [
        "SupplementaryFigure1"
    ]:
        svg = (OUT / f"{stem}.svg").read_text(encoding="utf-8")
        sizes = [
            float(value)
            for value in re.findall(
                r"font:\s*(?:(?:normal|bold|[0-9]+)\s+)*([0-9.]+)px",
                svg,
            )
        ]
        if sizes:
            minimum_font = min(minimum_font, min(sizes))
            maximum_font = max(maximum_font, max(sizes))
    report = {
        "backend": "Python/Matplotlib",
        "figure_count": len(FIGURE_RECORDS),
        "approved_palette": "ISSUE34_NATURE_REFERENCE_2026_07_27",
        "final_width_mm": 183,
        "readability_widths_mm": [89, 183],
        "accessibility_modes": [
            "full", "grayscale", "deuteranopia", "protanopia"
        ],
        "renderer_bounds_failures": sum(
            int(row["bounds_failure_count"]) for row in RENDERER_RECORDS
        ),
        "renderer_title_collisions": sum(
            int(row["title_collision_count"]) for row in RENDERER_RECORDS
        ),
        "minimum_svg_font_px": (
            None if not np.isfinite(minimum_font) else float(minimum_font)
        ),
        "maximum_svg_font_px": (
            None if not np.isfinite(maximum_font) else float(maximum_font)
        ),
        "declared_ordinary_font_range_px": [5.4, 7.0],
        "panel_label_font_px": 8.0,
        "figure_title_font_px": 9.0,
        "minimum_svg_font_note": (
            "Values below 5 pt are automatic mathematical super/subscripts; "
            "ordinary text is constrained to the declared 5.4--7.0 pt range."
        ),
        "manual_review_status": "PENDING_PAGE_AND_CONTACT_SHEET_INSPECTION",
    }
    (QA / "generation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    files = sorted(
        path for path in OUT.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS"
    )
    (OUT / "SHA256SUMS").write_text(
        "".join(
            f"{sha256(path)}  {path.relative_to(OUT).as_posix()}\n"
            for path in files
        ),
        encoding="utf-8",
    )


def main() -> None:
    style()
    figure1()
    figure2()
    figure3()
    figure4()
    figure5()
    figure6()
    supplementary_figure1()
    finalize_outputs()
    print(f"Wrote figures and source data to {OUT}")


if __name__ == "__main__":
    main()
