#!/usr/bin/env python3
"""Render two final-size visual concepts for each GOAL-17 main figure group."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from visualization.style.nature_style import CARD, CROP_COLORS, apply_nature_style  # noqa: E402


SRC = ROOT / "visualization" / "stage_ii" / "source_data"
OUT = ROOT / "audits" / "goal17_visual_candidates"
WIDTH_MM = 183
HEIGHT_MM = {1: 122, 2: 122, 3: 142, 4: 145, 5: 138, 6: 150}
STAGES = ["M0", "M1", "M2", "M3", "M4"]
DEFS = ["relative_yield", "standardized_revenue", "operating_margin", "total_cost_margin"]
DEF_LABELS = {
    "relative_yield": "Relative yield",
    "standardized_revenue": "Standardized revenue",
    "operating_margin": "Operating margin",
    "total_cost_margin": "Total-cost margin",
}
ARCH_LABELS = {
    "dominated_option_null": "Dominated option",
    "robust_option_substitutes": "Robust option",
    "specialization_unlocks": "Specialization unlocks",
}
STATE_TO_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC",
}


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(SRC / name)


def mm(width: float, height: float) -> tuple[float, float]:
    return width / 25.4, height / 25.4


def clean(ax: plt.Axes, *, grid: bool = False) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    if grid:
        ax.grid(True, axis="y", color=CARD["adverse"], alpha=0.18, linewidth=0.45)
    else:
        ax.grid(False)
    ax.set_axisbelow(True)


def quiet(ax: plt.Axes) -> None:
    ax.set_axis_off()


def panel(ax: plt.Axes, letter: str, title: str) -> None:
    ax.text(-0.08, 1.055, letter, transform=ax.transAxes, fontsize=8, fontweight="bold", va="bottom")
    ax.set_title(title, loc="left", pad=8, fontsize=7.2, fontweight="semibold")


def box(ax: plt.Axes, x: float, y: float, w: float, h: float, label: str, face: str = "white",
        edge: str | None = None, fontsize: float = 6.1) -> None:
    edge = edge or CARD["charcoal"]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.015",
                                facecolor=face, edgecolor=edge, linewidth=0.7))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=fontsize)


def arrow(ax: plt.Axes, a: tuple[float, float], b: tuple[float, float], color: str | None = None) -> None:
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=7, linewidth=0.7,
                                color=color or CARD["charcoal"]))


def vector_matrix(ax: plt.Axes, values: np.ndarray, colours) -> None:
    """Draw a small matrix as editable vector rectangles instead of raster imshow."""
    nrows, ncols = values.shape
    for row in range(nrows):
        for col in range(ncols):
            face = colours(values[row, col]) if callable(colours) else colours[int(values[row, col])]
            ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor=face,
                                   edgecolor=CARD["charcoal"], linewidth=0.45))
    ax.set_xlim(-0.5, ncols - 0.5)
    ax.set_ylim(nrows - 0.5, -0.5)


def allocation_colour(value: float) -> tuple[float, float, float]:
    """White-blended card colour for a Corn-share response cell."""
    base_hex = CARD["soybean"] if value <= 0.5 else CARD["corn"]
    alpha = 1 - 2 * value if value <= 0.5 else 2 * value - 1
    base = np.array(matplotlib.colors.to_rgb(base_hex))
    return tuple(alpha * base + (1 - alpha) * np.ones(3))


def base_figure(group: int, concept: str, subtitle: str) -> plt.Figure:
    apply_nature_style()
    fig = plt.figure(figsize=mm(WIDTH_MM, HEIGHT_MM[group]), constrained_layout=False)
    fig.suptitle(f"Figure {group} · concept {concept}  |  {subtitle}", x=0.04, y=0.985,
                 ha="left", va="top", fontsize=8.4, fontweight="bold", color=CARD["charcoal"])
    return fig


def allocation_frame() -> pd.DataFrame:
    frame = read("figure3_nested_summary.csv")
    alloc = frame[frame.metric.str.startswith("allocation_")].copy()
    alloc["crop"] = alloc.metric.str.replace("allocation_", "", regex=False).str.replace("_", " ")
    return alloc


def fig1a() -> plt.Figure:
    fig = base_figure(1, "A", "allocation fan + identification boundary")
    gs = fig.add_gridspec(2, 12, left=0.045, right=0.975, bottom=0.09, top=0.88,
                          height_ratios=[1.45, 1], hspace=0.38, wspace=0.75)
    ax = fig.add_subplot(gs[0, :]); quiet(ax); panel(ax, "a", "Structure added between an ordinal list and a cardinal decision")
    ax.set(xlim=(0, 1), ylim=(0, 1))
    items = [("Rank", "ordinal\norder"), ("Payoffs", "levels +\ngaps"), ("Uncertainty", "joint\nlaw"),
             ("Feasibility", "polyhedral\nset"), ("Optimal face", "set of\nsolutions"), ("Selection", "reported\nallocation")]
    xs = np.linspace(0.01, 0.845, len(items))
    faces = ["white", "white", "white", CARD["winter_wheat"] + "55", CARD["promoted"] + "33", "white"]
    for i, ((head, tail), x) in enumerate(zip(items, xs)):
        box(ax, x, 0.37, 0.13, 0.34, f"{head}\n{tail}", faces[i], fontsize=5.9)
        if i < len(xs) - 1:
            arrow(ax, (x + 0.132, 0.54), (xs[i + 1] - 0.006, 0.54))
    ax.plot([0.66, 0.66], [0.18, 0.83], color=CARD["adverse"], linestyle="--", linewidth=1.1)
    ax.text(0.66, 0.12, "identification boundary", ha="center", fontsize=6.1, color=CARD["adverse"])
    ax.text(0.255, 0.82, "observed / calibrated inputs", ha="center", fontsize=6.0)
    ax.text(0.825, 0.82, "model output + decision rule", ha="center", fontsize=6.0)

    ax2 = fig.add_subplot(gs[1, :7]); quiet(ax2); panel(ax2, "b", "One optimal face supports three distinct reversal claims")
    ax2.set(xlim=(-0.08, 1.08), ylim=(-0.05, 1.05))
    ax2.add_patch(Rectangle((0, 0.24), 0.5, 0.16, facecolor="white", edgecolor=CARD["charcoal"], linewidth=0.7))
    ax2.add_patch(Rectangle((0.5, 0.24), 0.5, 0.16, facecolor=CARD["promoted"] + "44", edgecolor=CARD["charcoal"], linewidth=0.7))
    ax2.plot([0.23, 0.82], [0.58, 0.58], color=CARD["charcoal"], linewidth=4, solid_capstyle="butt")
    ax2.scatter([0.32, 0.68], [0.58, 0.58], s=25, facecolors=["white", CARD["promoted"]],
                edgecolors=CARD["charcoal"], linewidths=0.7, zorder=3)
    ax2.text(0.25, 0.82, "optimal face crosses boundary", ha="center", fontsize=6.2)
    ax2.text(0.75, 0.82, "selected solution may reverse", ha="center", fontsize=6.2)
    ax2.text(0.25, 0.12, "rank-consistent region", ha="center", fontsize=5.8)
    ax2.text(0.75, 0.12, "reversal region", ha="center", fontsize=5.8)

    ax3 = fig.add_subplot(gs[1, 7:]); quiet(ax3); panel(ax3, "c", "Claim strength rises with assumptions")
    ax3.set(xlim=(0, 1), ylim=(0, 1))
    for i, (lab, col) in enumerate([("discordance", "white"), ("possible", CARD["winter_wheat"] + "55"),
                                     ("universal", CARD["promoted"] + "33"), ("selected", "white")]):
        y = 0.76 - i * 0.2
        ax3.plot([0.08, 0.22], [y, y], color=CARD["charcoal"], linewidth=0.8)
        box(ax3, 0.25, y - 0.07, 0.62, 0.14, lab, col, fontsize=6.0)
    return fig


def fig1b() -> plt.Figure:
    fig = base_figure(1, "B", "inference architecture + optimal-face geometry")
    gs = fig.add_gridspec(2, 12, left=0.072, right=0.965, bottom=0.085, top=0.87,
                          height_ratios=[1.45, 0.82], hspace=0.48, wspace=0.9)

    ax = fig.add_subplot(gs[0, :8]); quiet(ax)
    panel(ax, "a", "Observed discordance and the hidden decision system are different objects")
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.add_patch(Rectangle((0.01, 0.10), 0.20, 0.78, facecolor=CARD["corn"] + "18", edgecolor="none"))
    ax.add_patch(Rectangle((0.25, 0.10), 0.43, 0.78, facecolor=CARD["winter_wheat"] + "28", edgecolor="none"))
    ax.add_patch(Rectangle((0.72, 0.10), 0.27, 0.78, facecolor=CARD["promoted"] + "18", edgecolor="none"))
    ax.text(0.03, 0.82, "OBSERVED", fontsize=6.0, fontweight="bold", color=CARD["corn"])
    ax.text(0.27, 0.82, "DECISION SYSTEM", fontsize=6.0, fontweight="bold", color=CARD["charcoal"])
    ax.text(0.74, 0.82, "MODEL-IMPLIED", fontsize=6.0, fontweight="bold", color=CARD["promoted"])

    ax.scatter([0.10, 0.10], [0.61, 0.31], s=[180, 180], facecolor="white",
               edgecolor=CARD["charcoal"], linewidth=0.8)
    ax.text(0.10, 0.61, "crop\nrank", ha="center", va="center", fontsize=6.0)
    ax.text(0.10, 0.31, "acreage\norder", ha="center", va="center", fontsize=6.0)
    ax.plot([0.10, 0.10], [0.43, 0.49], color=CARD["adverse"], lw=1.0, ls="--")
    ax.text(0.10, 0.15, "discordance is\ndescriptive", ha="center", fontsize=5.6, color=CARD["adverse"])

    system_items = [(0.35, 0.62, "cardinal\nmargins", CARD["corn"]),
                    (0.56, 0.62, "joint\nuncertainty", CARD["adverse"]),
                    (0.35, 0.32, "feasible\nset", CARD["soybean"]),
                    (0.56, 0.32, "selection\nrule", CARD["winter_wheat"])]
    for x0, y0, label, colour in system_items:
        ax.add_patch(Ellipse((x0, y0), 0.17, 0.19, facecolor="white", edgecolor=colour, lw=1.1))
        ax.text(x0, y0, label, ha="center", va="center", fontsize=5.8)
    ax.text(0.465, 0.15, "assumed, assigned or estimated", ha="center", fontsize=5.6,
            color=CARD["adverse"])
    arrow(ax, (0.675, 0.49), (0.75, 0.49), CARD["charcoal"])

    ax.plot([0.77, 0.94], [0.62, 0.62], color=CARD["charcoal"], lw=5.5, solid_capstyle="butt")
    ax.scatter([0.85], [0.62], s=28, facecolor=CARD["promoted"], edgecolor=CARD["charcoal"], lw=0.6, zorder=3)
    ax.text(0.855, 0.75, "optimal face", ha="center", fontsize=6.1, fontweight="semibold")
    ax.text(0.855, 0.47, "selected optimizer", ha="center", fontsize=5.8)
    ax.text(0.855, 0.24, "possible / universal\n/ selected claims", ha="center", fontsize=5.8,
            color=CARD["promoted"])

    ax2 = fig.add_subplot(gs[0, 8:]); quiet(ax2)
    panel(ax2, "b", "Claim strength is nested")
    ax2.set(xlim=(0, 1), ylim=(0, 1))
    ax2.add_patch(Ellipse((0.50, 0.48), 0.88, 0.73, facecolor=CARD["winter_wheat"] + "28",
                          edgecolor=CARD["adverse"], lw=0.8))
    ax2.add_patch(Ellipse((0.50, 0.48), 0.62, 0.50, facecolor="white",
                          edgecolor=CARD["corn"], lw=0.9, ls="--"))
    ax2.add_patch(Ellipse((0.50, 0.48), 0.35, 0.27, facecolor=CARD["promoted"] + "44",
                          edgecolor=CARD["promoted"], lw=1.0))
    ax2.text(0.50, 0.80, "POSSIBLE", ha="center", fontsize=6.2, fontweight="bold")
    ax2.text(0.50, 0.65, "SELECTED", ha="center", fontsize=6.1, fontweight="bold", color=CARD["corn"])
    ax2.text(0.50, 0.48, "UNIVERSAL", ha="center", va="center", fontsize=6.1,
             fontweight="bold", color=CARD["promoted"])
    ax2.text(0.50, 0.08, "universal  >  selected  >  possible", ha="center", fontsize=5.7)

    ax3 = fig.add_subplot(gs[1, :]); quiet(ax3)
    panel(ax3, "c", "The full optimal face determines set-valued reversal")
    ax3.set(xlim=(0, 1), ylim=(0, 1))
    ax3.add_patch(Rectangle((0.07, 0.21), 0.43, 0.15, facecolor="white",
                            edgecolor=CARD["charcoal"], lw=0.7))
    ax3.add_patch(Rectangle((0.50, 0.21), 0.43, 0.15, facecolor=CARD["promoted"] + "44",
                            edgecolor=CARD["charcoal"], lw=0.7))
    ax3.plot([0.24, 0.80], [0.58, 0.58], color=CARD["charcoal"], lw=5.2, solid_capstyle="butt")
    ax3.scatter([0.35, 0.70], [0.58, 0.58], s=28, facecolors=["white", CARD["promoted"]],
                edgecolor=CARD["charcoal"], linewidth=0.7, zorder=3)
    ax3.text(0.29, 0.79, "possible  YES", ha="center", fontsize=6.2, fontweight="semibold")
    ax3.text(0.52, 0.79, "universal  NO", ha="center", fontsize=6.2, fontweight="semibold")
    ax3.text(0.76, 0.79, "selected  RULE-DEPENDENT", ha="center", fontsize=6.2, fontweight="semibold")
    ax3.text(0.29, 0.10, "rank-consistent allocations", ha="center", fontsize=5.8)
    ax3.text(0.72, 0.10, "reversal allocations", ha="center", fontsize=5.8)
    ax3.plot([0.50, 0.50], [0.16, 0.70], color=CARD["charcoal"], lw=0.8, ls="--")
    ax3.text(0.50, 0.03, "common rank boundary", ha="center", fontsize=5.6, color=CARD["adverse"])
    return fig


def draw_geometry(ax: plt.Axes, row: pd.Series, mode: str) -> None:
    ax.set(xlim=(-0.05, 1.05), ylim=(-0.32, 0.42), xticks=[0, 0.5, 1], yticks=[])
    ax.axvspan(0, 0.5, color=CARD["promoted"], alpha=0.16, zorder=0)
    ax.axvline(0.5, color=CARD["charcoal"], lw=0.7, ls="--")
    f0, f1 = row.feasible_xcorn_min, row.feasible_xcorn_max
    o0, o1 = row.optimal_xcorn_min, row.optimal_xcorn_max
    ax.plot([0, 1], [0, 0], color=CARD["adverse"], lw=1.2)
    ax.plot([f0, f1], [0, 0], color=CARD["charcoal"], lw=5, solid_capstyle="butt")
    if abs(o1 - o0) < 1e-9:
        ax.scatter([o0], [0], s=30, color=CARD["promoted"], edgecolor=CARD["charcoal"], lw=0.6, zorder=3)
    else:
        ax.plot([o0, o1], [0.12, 0.12], color=CARD["promoted"], lw=4, solid_capstyle="butt")
    if mode == "atlas" and row.case_id in {"margin", "operations", "risk"}:
        start = 0.88 if row.case_id == "margin" else 0.72
        ax.annotate("", xy=(o0, 0.24), xytext=(start, 0.24),
                    arrowprops=dict(arrowstyle="-|>", color=CARD["charcoal"], lw=0.7))
    ax.set_xlabel("Corn share  (Soybean share = 1 − Corn)")
    clean(ax)


def fig2a() -> plt.Figure:
    fig = base_figure(2, "A", "coordinated feasible-set atlas")
    data = read("figure2_geometry.csv").query("case_id != 'common'").reset_index(drop=True)
    gs = fig.add_gridspec(2, 2, left=0.075, right=0.97, bottom=0.11, top=0.86, hspace=0.62, wspace=0.28)
    titles = ["Cardinal margin rotates the objective", "Operations remove rank-consistent land",
              "Downside risk truncates the feasible set", "A crossing face makes reversal selection-dependent"]
    for i, (row, title) in enumerate(zip(data.itertuples(), titles)):
        ax = fig.add_subplot(gs[i // 2, i % 2]); panel(ax, chr(97 + i), title); draw_geometry(ax, row, "atlas")
    return fig


def fig2b() -> plt.Figure:
    fig = base_figure(2, "B", "shared-coordinate mechanism atlas")
    gs = fig.add_gridspec(2, 2, left=0.095, right=0.97, bottom=0.11, top=0.84,
                          hspace=0.54, wspace=0.32)
    fig.text(0.50, 0.915,
             "Shared encoding: pale teal = reversal region   ·   dashed = rank boundary   ·   arrow = objective   ·   point / thick edge = optimum",
             ha="center", va="center", fontsize=5.7, color=CARD["adverse"])
    specs = [
        ("a", "Cardinal margin", "Objective rotates toward Soybean"),
        ("b", "Operational displacement", "Corn cap + Soybean floor clip the domain"),
        ("c", "Downside-risk displacement", "Risk boundary removes the Corn-heavy corner"),
        ("d", "Set-valued optimum", "An optimal face crosses the rank boundary"),
    ]

    def simplex_axes(ax: plt.Axes, letter: str, title: str, subtitle: str) -> None:
        panel(ax, letter, title)
        ax.set(xlim=(-0.03, 1.03), ylim=(-0.04, 1.04), aspect="equal",
               xticks=[0, .5, 1], yticks=[0, .5, 1])
        ax.add_patch(Polygon([[0, 0], [1, 0], [0, 1]], closed=True,
                             facecolor="white", edgecolor=CARD["charcoal"], lw=0.9, zorder=0))
        ax.add_patch(Polygon([[0, 0], [0, 1], [.5, .5]], closed=True,
                             facecolor=CARD["promoted"] + "22", edgecolor="none", zorder=0.1))
        ax.plot([0, .5], [0, .5], color=CARD["charcoal"], lw=0.75, ls="--", zorder=2)
        ax.text(.97, .92, subtitle.replace(" toward ", "\ntoward ")
                .replace(" + ", " +\n").replace(" removes ", "\nremoves ")
                .replace(" crosses ", "\ncrosses "), transform=ax.transAxes,
                ha="right", va="top", fontsize=5.6, color=CARD["adverse"], linespacing=1.25)
        ax.spines[:].set_visible(False)
        ax.tick_params(length=2, pad=2)

    axes = [fig.add_subplot(gs[i // 2, i % 2]) for i in range(4)]
    for ax, (letter, title, subtitle) in zip(axes, specs):
        simplex_axes(ax, letter, title, subtitle)

    # Cardinal margins: the feasible simplex is unchanged; only the objective rotates.
    a = axes[0]
    a.add_patch(FancyArrowPatch((.72, .18), (.30, .70), arrowstyle="-|>", mutation_scale=8,
                                color=CARD["corn"], lw=1.2, zorder=4))
    a.scatter([0], [1], s=44, color=CARD["promoted"], edgecolor=CARD["charcoal"], lw=.7, zorder=5)

    # Operations: the same simplex is clipped by transparent, directly interpretable bounds.
    b = axes[1]
    operational = np.array([[0, .35], [.42, .35], [.42, .58], [0, 1]])
    b.add_patch(Polygon(operational, closed=True, facecolor=CARD["winter_wheat"] + "66",
                        edgecolor=CARD["soybean"], lw=1.2, zorder=1.5))
    b.plot([.42, .42], [.35, .58], color=CARD["soybean"], lw=1.5)
    b.plot([0, .42], [.35, .35], color=CARD["soybean"], lw=1.5)
    b.add_patch(FancyArrowPatch((.18, .70), (.68, .28), arrowstyle="-|>", mutation_scale=8,
                                color=CARD["corn"], lw=1.2, zorder=4))
    b.scatter([.42], [.58], s=44, color=CARD["promoted"], edgecolor=CARD["charcoal"], lw=.7, zorder=5)
    b.annotate("forced optimum", xy=(.42, .58), xytext=(.58, .72), fontsize=5.6,
               arrowprops=dict(arrowstyle="-", color=CARD["charcoal"], lw=.6))

    # Risk: a curved loss-CVaR boundary truncates the objective's preferred corner.
    c = axes[2]
    xcurve = np.linspace(0, .48, 80)
    ycurve = .30 + .95 * xcurve ** 2
    feasible = np.column_stack([np.r_[xcurve, 0], np.r_[ycurve, 1]])
    c.add_patch(Polygon(feasible, closed=True, facecolor=CARD["adverse"] + "38",
                        edgecolor=CARD["adverse"], lw=1.1, zorder=1.5))
    c.plot(xcurve, ycurve, color=CARD["adverse"], lw=1.4, zorder=3)
    c.add_patch(FancyArrowPatch((.17, .70), (.70, .22), arrowstyle="-|>", mutation_scale=8,
                                color=CARD["corn"], lw=1.2, zorder=4))
    c.scatter([.48], [1 - .48], s=44, color=CARD["promoted"], edgecolor=CARD["charcoal"], lw=.7, zorder=5)
    c.annotate("boundary optimum", xy=(.48, .52), xytext=(.60, .68), fontsize=5.6,
               arrowprops=dict(arrowstyle="-", color=CARD["charcoal"], lw=.6))

    # Set-valued: a flat objective exposes the full face and the selector's role.
    d = axes[3]
    d.add_patch(FancyArrowPatch((.20, .18), (.53, .51), arrowstyle="-|>", mutation_scale=8,
                                color=CARD["corn"], lw=1.2, zorder=4))
    d.plot([0, .5], [1, .5], color=CARD["promoted"], lw=4.2, solid_capstyle="butt", zorder=4)
    d.plot([.5, 1], [.5, 0], color=CARD["adverse"], lw=4.2, solid_capstyle="butt", zorder=4)
    d.scatter([.35, .65], [.65, .35], s=[28, 38], facecolors=[CARD["promoted"], "white"],
              edgecolor=CARD["charcoal"], lw=.7, zorder=5)
    for y0, claim in [(.73, "possible  YES"), (.65, "universal  NO"),
                      (.57, "selected"), (.49, "rule-dependent")]:
        d.text(.97, y0, claim, transform=d.transAxes, ha="right", va="top",
               fontsize=5.5, fontweight="semibold")

    for i, ax in enumerate(axes):
        ax.set_xlabel("Corn share" if i >= 2 else "")
        ax.set_ylabel("Soybean share" if i % 2 == 0 else "")
        if i < 2:
            ax.tick_params(labelbottom=False)
        if i % 2:
            ax.tick_params(labelleft=False)
    return fig


def stage_values(metric: str) -> pd.DataFrame:
    frame = read("figure3_nested_summary.csv")
    return frame[frame.metric.eq(metric)].set_index("model_stage").loc[STAGES].reset_index()


def fig3a() -> plt.Figure:
    fig = base_figure(3, "A", "allocation river + native-unit outcome tracks")
    gs = fig.add_gridspec(3, 12, left=0.10, right=0.965, bottom=0.08, top=0.88,
                          height_ratios=[1.45, 0.82, 0.95], hspace=0.62, wspace=0.8)
    ax = fig.add_subplot(gs[0, :8]); panel(ax, "a", "Allocation composition across M0–M4 (n = 16 seeds)")
    alloc = allocation_frame(); x = np.arange(5); base = np.zeros(5)
    hatches = {"Corn": "///", "Soybean": "\\\\", "Winter Wheat": "..."}
    for crop in ["Corn", "Soybean", "Winter Wheat"]:
        vals = alloc[alloc.crop.eq(crop)].set_index("model_stage").loc[STAGES, "mean"].to_numpy()
        ax.fill_between(x, base, base + vals, color=CROP_COLORS[crop], alpha=0.9, linewidth=0.45,
                        edgecolor=CARD["charcoal"], hatch=hatches[crop], label=crop)
        base += vals
    ax.set(xticks=x, xticklabels=STAGES, ylabel="Land share", ylim=(0, 1), xlim=(0, 4))
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.2)); clean(ax)
    axh = fig.add_subplot(gs[0, 8:]); panel(axh, "b", "Concentration")
    hhi = stage_values("hhi")
    axh.plot(x, hhi["mean"], color=CARD["charcoal"], marker="o", ms=3, lw=1.2)
    axh.set(xticks=x, xticklabels=STAGES, ylabel="HHI", ylim=(0, 1.05)); clean(axh)
    for j, (metric, title, ylabel) in enumerate([("expected_profit", "Expected margin", "Value units"),
                                                 ("cvar_loss", "Loss-CVaR", "Loss units")]):
        a = fig.add_subplot(gs[1, j * 6:(j + 1) * 6]); panel(a, chr(99 + j), title)
        d = stage_values(metric); xx = np.arange(5)
        a.errorbar(xx, d["mean"], yerr=[d["mean"] - d["ci_low"], d["ci_high"] - d["mean"]],
                   fmt="o-", color=CARD["promoted"] if j == 0 else CARD["adverse"], lw=1, ms=3, capsize=2)
        a.set(xticks=xx, xticklabels=STAGES, ylabel=ylabel); clean(a)
    shap = read("figure3_shapley_summary.csv").query("metric == 'allocation_Corn'").sort_values("mean")
    a = fig.add_subplot(gs[2, :6]); panel(a, "e", "All-subset accounting of Corn-share change")
    y = np.arange(len(shap)); a.errorbar(shap["mean"], y, xerr=[shap["mean"]-shap["ci_low"], shap["ci_high"]-shap["mean"]],
                                         fmt="o", color=CARD["charcoal"], capsize=2)
    a.axvline(0, color=CARD["adverse"], lw=0.7); a.set(yticks=y, yticklabels=shap.block.str.replace("_", " ").str.title(), xlabel="Corn-share contribution")
    clean(a)
    p = read("figure3_pressure_summary.csv").groupby("pressure_term", as_index=False)["mean"].mean().sort_values("mean")
    b = fig.add_subplot(gs[2, 6:]); panel(b, "f", "Mean local KKT pressure (not causal)")
    yy = np.arange(len(p)); b.barh(yy, p["mean"], color=[CARD["adverse"] if v == 0 else CARD["promoted"] for v in p["mean"]])
    b.set(yticks=yy, yticklabels=p.pressure_term.str.replace("_pressure", "").str.replace("_", " ").str.title(), xlabel="Pressure units")
    clean(b)
    return fig


def fig3b() -> plt.Figure:
    fig = base_figure(3, "B", "stage columns + mechanism ledger")
    gs = fig.add_gridspec(3, 10, left=0.06, right=0.97, bottom=0.08, top=0.82,
                          height_ratios=[1.25, 0.85, 1], hspace=0.62, wspace=0.65)
    fig.text(0.047, 0.865, "a", fontsize=8, fontweight="bold", va="center")
    fig.text(0.065, 0.865, "Each model stage exposes composition and concentration",
             fontsize=7.2, fontweight="semibold", va="center")
    alloc = allocation_frame()
    for i, stage in enumerate(STAGES):
        ax = fig.add_subplot(gs[0, i * 2:(i + 1) * 2]);
        ax.set_title(stage, fontsize=7.2, fontweight="semibold", pad=8)
        vals = alloc[alloc.model_stage.eq(stage)].set_index("crop").loc[["Corn", "Soybean", "Winter Wheat"], "mean"]
        bottom = 0
        for crop, v in vals.items():
            ax.bar(0, v, bottom=bottom, color=CROP_COLORS[crop], width=0.65, edgecolor="white", lw=0.6)
            bottom += v
        hhi = float(stage_values("hhi").set_index("model_stage").loc[stage, "mean"])
        ax.set(xlim=(-0.7, 0.7), ylim=(0, 1), xticks=[], yticks=[0, 0.5, 1] if i == 0 else [])
        ax.text(0, -0.16, f"HHI {hhi:.2f}", transform=ax.transData, ha="center", va="top", fontsize=5.8)
        clean(ax)
    for j, (metric, title, ylabel) in enumerate([("expected_profit", "Expected margin", "Value units"), ("cvar_loss", "Loss-CVaR", "Loss units")]):
        ax = fig.add_subplot(gs[1, j * 5:(j + 1) * 5]); panel(ax, chr(98 + j), title)
        d = stage_values(metric); x = np.arange(5)
        ax.errorbar(x, d["mean"], yerr=[d["mean"]-d["ci_low"], d["ci_high"]-d["mean"]], fmt="o",
                    color=CARD["promoted"] if j == 0 else CARD["adverse"], capsize=2)
        ax.plot(x, d["mean"], color=CARD["charcoal"], lw=0.7)
        ax.set(xticks=x, xticklabels=STAGES, ylabel=ylabel); clean(ax)
    shap = read("figure3_shapley_summary.csv").query("metric in ['allocation_Corn','cvar_loss']")
    ax = fig.add_subplot(gs[2, :]); panel(ax, "d", "Model-block contributions remain metric-specific accounting quantities")
    blocks = sorted(shap.block.unique()); offsets = [-0.12, 0.12]
    for k, (metric, lab, col) in enumerate([("allocation_Corn", "Corn share", CARD["corn"]), ("cvar_loss", "Loss-CVaR", CARD["adverse"]) ]):
        d = shap[shap.metric.eq(metric)].set_index("block").loc[blocks]
        scaled = d["mean"] if metric == "allocation_Corn" else d["mean"] / 10
        ax.scatter(np.arange(len(blocks)) + offsets[k], scaled, s=18, color=col, label=lab)
    ax.axhline(0, color=CARD["charcoal"], lw=0.65); ax.set(xticks=np.arange(len(blocks)), xticklabels=[b.title() for b in blocks], ylabel="Native share; loss ÷ 10")
    ax.legend(ncol=2, loc="upper right"); clean(ax)
    return fig


def treatment_label(row: pd.Series) -> str:
    active = []
    if row.budget: active.append("Budget")
    if row.rotation: active.append("Rotation")
    if row.contract: active.append("Soy contract")
    if row.corn_bound: active.append("Corn cap")
    if not active:
        return "Baseline"
    label = " + ".join(active)
    return label.replace("Budget + Rotation + Soy contract", "Budget + Rotation\n+ Soy contract")


def fig4a() -> plt.Figure:
    fig = base_figure(4, "A", "assigned design + allocation response + confirmatory effects")
    cells = read("figure4_e2_cells.csv"); cells["label"] = [
        "Baseline", "Soy contract", "Rotation", "Rotation + contract", "Budget",
        "Budget + contract", "Budget + rotation", "Budget + both", "Corn cap",
    ]
    cells["profit_delta"] = cells.expected_profit - float(cells.iloc[0].expected_profit)
    y = np.arange(len(cells))
    gs = fig.add_gridspec(3, 12, left=0.145, right=0.965, bottom=0.075, top=0.87,
                          height_ratios=[1.58, 1.00, 0.82], hspace=0.72, wspace=1.18)

    factors = fig.add_subplot(gs[0, :3]); panel(factors, "a", "Assigned intervention design")
    fmat = cells[["budget", "rotation", "contract", "corn_bound"]].to_numpy()
    vector_matrix(factors, fmat, ["white", CARD["winter_wheat"]])
    factors.set(yticks=y, yticklabels=cells.label, xticks=np.arange(4),
                xticklabels=["Budget", "Rotation", "Soy\ncontract", "Corn\ncap"])
    factors.tick_params(length=0, pad=3)

    alloc = fig.add_subplot(gs[0, 3:7], sharey=factors); alloc.set_title("Allocation response", loc="left", pad=8, fontsize=7.2, fontweight="semibold")
    alloc.axvspan(0, 0.5, color=CARD["promoted"], alpha=0.16); alloc.axvline(0.5, color=CARD["charcoal"], lw=0.8, ls="--")
    alloc.hlines(y, cells.allocation_Corn, 1, color=CARD["adverse"], lw=0.65)
    alloc.scatter(cells.allocation_Corn, y, c=[CARD["corn"] if i == 0 else CARD["promoted"] for i in range(len(cells))],
                  s=30, edgecolor=CARD["charcoal"], lw=0.5, zorder=3)
    for yy, u in zip(y, cells.universal_reversal):
        alloc.text(1.03, yy, "U" if u else "—", ha="left", va="center", fontsize=5.6,
                   color=CARD["promoted"] if u else CARD["adverse"])
    alloc.set(xlim=(0, 1.11), xticks=[0, .5, 1], xlabel="Corn share   ·   shaded = reversal   ·   U = universal")
    alloc.tick_params(axis="y", labelleft=False, length=0); clean(alloc)

    profit = fig.add_subplot(gs[0, 7:9], sharey=factors); profit.set_title("Δ margin", loc="left", pad=8, fontsize=7.2, fontweight="semibold")
    profit.axvline(0, color=CARD["charcoal"], lw=0.7); profit.scatter(cells.profit_delta, y, s=22, color=CARD["soybean"], edgecolor=CARD["charcoal"], lw=.4)
    profit.set(xlim=(-5.4, .45), xticks=[-5, -2.5, 0], xlabel="Value units"); profit.tick_params(axis="y", labelleft=False, length=0); clean(profit)

    mech = fig.add_subplot(gs[0, 9:], sharey=factors); mech.set_title("Local balance", loc="left", pad=8, fontsize=7.2, fontweight="semibold")
    mechanism = []
    for row in cells.itertuples():
        if row.corn_bound: mechanism.append("Boundary")
        elif row.mechanism_class == "DIRECT_FORCING": mechanism.append("Direct")
        elif row.mechanism_class == "MARGINAL_PRESSURE": mechanism.append("Marginal")
        else: mechanism.append("Baseline")
    cats = ["Baseline", "Marginal", "Direct", "Boundary"]
    mx = [cats.index(v) for v in mechanism]
    mech_colors = {"Baseline": CARD["adverse"], "Marginal": CARD["corn"],
                   "Direct": CARD["promoted"], "Boundary": CARD["soybean"]}
    mech.scatter(mx, y, s=25, color=[mech_colors[v] for v in mechanism],
                 edgecolor=CARD["charcoal"], lw=.4)
    mech.set(xlim=(-.45, 3.45), xticks=np.arange(4), xticklabels=["Base", "Margin", "Forcing", "Bound"], xlabel="Pressure class")
    mech.tick_params(axis="x", rotation=0, labelsize=5.5); mech.tick_params(axis="y", labelleft=False, length=0); clean(mech)

    contrasts = read("figure4_e2_contrasts.csv").copy()
    treated_labels = ["Contract", "Rotation", "Both", "Budget", "Budget + contract", "Budget + rotation", "Budget + both", "Corn cap"]
    metrics = [("allocation_l1", "Allocation L1", "L1 share change"),
               ("expected_profit", "Margin change", "Value units"),
               ("selected_reversal_change", "Reversal change", "Probability change")]
    for j, (metric, title, xlabel) in enumerate(metrics):
        ax = fig.add_subplot(gs[1, j * 4:(j + 1) * 4]);
        if j == 0:
            panel(ax, "b", "Family-wise contrasts · " + title)
        else:
            ax.set_title(title, loc="left", pad=8, fontsize=7.2, fontweight="semibold")
        d = contrasts[contrasts.metric.eq(metric)].reset_index(drop=True); yy = np.arange(8)
        ax.errorbar(d.estimate, yy, xerr=[d.estimate-d.ci_low, d.ci_high-d.estimate], fmt="o", color=CARD["promoted"], capsize=2, ms=3)
        ax.axvline(0, color=CARD["charcoal"], lw=.65)
        ax.set(yticks=yy, yticklabels=treated_labels if j == 0 else [], xlabel=xlabel); ax.invert_yaxis(); clean(ax)
        if metric == "selected_reversal_change":
            ax.set_xlim(-0.05, 1.08); ax.set_xticks([0, 0.5, 1.0])

    pressure = read("figure3_pressure_summary.csv")
    pclasses = ["INACTIVE_IN_CELL", "MARGINAL_PRESSURE", "DIRECT_FORCING"]
    pterms = ["margin_pressure", "budget_pressure", "shared_pressure", "boundary_pressure", "tail_risk_pressure"]
    p = pressure.pivot(index="mechanism_class", columns="pressure_term", values="mean").loc[pclasses, pterms]
    axp = fig.add_subplot(gs[2, :8]); panel(axp, "c", "Local KKT pressure fingerprint (accounting, not causal)")
    for iy, cls in enumerate(pclasses):
        for ix, term in enumerate(pterms):
            value = float(p.loc[cls, term]); axp.scatter(ix, iy, s=10 + 95 * value / max(1, p.to_numpy().max()),
                                                        facecolor=CARD["promoted"] if value > 0 else "white",
                                                        edgecolor=CARD["charcoal"], lw=.45)
    axp.set(xticks=np.arange(5), xticklabels=["Margin", "Budget", "Shared", "Boundary", "Tail risk"],
            yticks=np.arange(3), yticklabels=["Baseline / bound", "Marginal pressure", "Direct forcing"], xlim=(-.5,4.5), ylim=(2.5,-.5))
    axp.tick_params(length=0); axp.spines[:].set_visible(False)

    summary = fig.add_subplot(gs[2, 8:]); quiet(summary); panel(summary, "d", "Confirmatory facts")
    summary.set(xlim=(0, 1), ylim=(0, 1))
    for i, (value, label) in enumerate([("24 / 24", "intervals met precision criterion"), ("n = 16", "seeds in every cell"),
                                        ("0", "tail-risk pressure in the intervention")]):
        yy = .76 - i*.29; summary.text(.03, yy, value, fontsize=8.2, fontweight="bold", color=CARD["promoted"])
        summary.text(.31, yy, label, fontsize=5.7, va="center")
    return fig


def fig4b() -> plt.Figure:
    fig = base_figure(4, "B", "factorial response surfaces + feasible-set mechanism")
    cells = read("figure4_e2_cells.csv"); base = float(cells.iloc[0].expected_profit)
    gs = fig.add_gridspec(3, 12, left=0.09, right=0.96, bottom=0.075, top=0.88,
                          height_ratios=[1.05, 1.0, .95], hspace=0.68, wspace=0.85)
    factorial = cells.iloc[:8].copy()
    for j, budget in enumerate([0, 1]):
        ax = fig.add_subplot(gs[0, j*4:(j+1)*4]); panel(ax, chr(97+j), "No budget intervention" if budget == 0 else "Budget intervention")
        d = factorial[factorial.budget.eq(budget)].sort_values(["rotation", "contract"])
        mat = d.pivot(index="rotation", columns="contract", values="allocation_Corn").loc[[1,0],[0,1]]
        vector_matrix(ax, mat.to_numpy(), allocation_colour)
        ax.set(xticks=[0,1], xticklabels=["No contract", "Soy contract"], yticks=[0,1], yticklabels=["Rotation", "No rotation"])
        ax.tick_params(length=0)
        for iy in range(2):
            for ix in range(2):
                value=float(mat.iloc[iy,ix]); row=d[(d.rotation.eq([1,0][iy])) & (d.contract.eq(ix))].iloc[0]
                ax.text(ix, iy-.08, f"Corn {value:.3f}", ha="center", va="center", fontsize=5.7, fontweight="semibold")
                ax.text(ix, iy+.15, f"Δmargin {row.expected_profit-base:.2f}", ha="center", va="center", fontsize=5.5)
    anchor = fig.add_subplot(gs[0, 8:]); panel(anchor, "c", "Corn-bound anchor")
    anchor.axvspan(0,.5,color=CARD["promoted"],alpha=.13); anchor.axvline(.5,color=CARD["charcoal"],ls="--",lw=.7)
    anchor.plot([0,.45],[0,0],color=CARD["charcoal"],lw=6,solid_capstyle="butt"); anchor.scatter([.45],[0],s=30,color=CARD["promoted"],edgecolor=CARD["charcoal"],zorder=3)
    anchor.set(xlim=(-.03,1.03),ylim=(-.2,.2),yticks=[],xticks=[0,.5,1],xlabel="Corn share"); clean(anchor)

    axd = fig.add_subplot(gs[1, :7]); panel(axd, "d", "Budget shifts the selected allocation beyond contract and rotation effects")
    combos=[(0,0,"Neither"),(0,1,"Contract"),(1,0,"Rotation"),(1,1,"Both")]
    for rot,con,label in combos:
        q=factorial[(factorial.rotation.eq(rot))&(factorial.contract.eq(con))].sort_values("budget")
        axd.plot(q.budget,q.allocation_Corn,marker="o",ms=3,lw=1,label=label)
    axd.axhline(.5,color=CARD["charcoal"],ls="--",lw=.7); axd.set(xticks=[0,1],xticklabels=["No budget", "Budget"],ylabel="Selected Corn share",ylim=(.25,1.05))
    axd.legend(ncol=2,loc="upper right"); clean(axd)
    axe = fig.add_subplot(gs[1, 7:]); panel(axe, "e", "Margin–allocation frontier across cells")
    for cls,marker,col in [("INACTIVE_IN_CELL","o",CARD["adverse"]),("MARGINAL_PRESSURE","s",CARD["corn"]),("DIRECT_FORCING","^",CARD["promoted"])]:
        q=cells[cells.mechanism_class.eq(cls)]; axe.scatter(q.allocation_Corn,q.expected_profit,s=25,marker=marker,color=col,edgecolor=CARD["charcoal"],lw=.4,label=cls.split("_")[0].title())
    axe.axvline(.5,color=CARD["charcoal"],ls="--",lw=.7); axe.set(xlabel="Corn share",ylabel="Expected margin"); axe.legend(loc="lower right"); clean(axe)

    contrasts=read("figure4_e2_contrasts.csv")
    axf=fig.add_subplot(gs[2,:]); panel(axf,"f","The 24 pre-specified estimates separate allocation, margin and reversal estimands")
    positions={"allocation_l1":0,"expected_profit":1,"selected_reversal_change":2}; labels=["Allocation L1", "Expected margin", "Reversal probability"]
    for metric,x0 in positions.items():
        q=contrasts[contrasts.metric.eq(metric)]; values=q.estimate.to_numpy(); scaled=(values-values.mean())/(values.std() if values.std()>0 else 1)
        jitter=np.linspace(-.22,.22,len(values)); axf.scatter(np.full(len(values),x0)+jitter,scaled,s=22,color=CARD["promoted"],edgecolor=CARD["charcoal"],lw=.35)
        axf.plot([x0-.26,x0+.26],[0,0],color=CARD["charcoal"],lw=.7)
    axf.set(xticks=[0,1,2],xticklabels=labels,ylabel="Within-estimand standardized estimate",xlim=(-.5,2.5)); clean(axf)
    return fig


def fig5a() -> plt.Figure:
    fig = base_figure(5, "A", "three archetype columns + interaction forest")
    data = read("figure5_information_summary.csv")
    order = ["specialization_unlocks", "dominated_option_null", "robust_option_substitutes"]
    gs = fig.add_gridspec(2, 12, left=0.065, right=0.975, bottom=0.09, top=0.87,
                          height_ratios=[1.25, 0.9], hspace=0.62, wspace=0.7)
    display_tolerance = 1e-12
    for i, arch in enumerate(order):
        ax = fig.add_subplot(gs[0, i * 4:(i + 1) * 4]); panel(ax, chr(97+i), ARCH_LABELS[arch])
        d = data[data.archetype.eq(arch)].copy()
        d["display_mean"] = np.where(d["mean"].abs() < display_tolerance, 0.0, d["mean"])
        for level, col, marker, style in [("low", CARD["corn"], "o", "--"), ("high", CARD["soybean"], "s", "-")]:
            s = d[d.flexibility_level.eq(level)].sort_values("signal_accuracy")
            ax.plot(s.signal_accuracy, s["display_mean"], color=col, marker=marker, linestyle=style, ms=3, lw=1.1, label=f"{level.title()} flexibility")
        ax.set(xlabel="Signal accuracy", ylabel="Value of information" if i == 0 else "", xticks=[0.5, 0.7, 0.9])
        if arch == "dominated_option_null":
            ax.set_ylim(-0.05, 0.05)
            ax.set_yticks([0], ["0"])
            ax.axhline(0, color=CARD["charcoal"], lw=0.75, zorder=0)
            ax.text(0.52, 0.82, "exact null (|v| < 1e-12)", transform=ax.transAxes,
                    fontsize=5.6, color=CARD["adverse"])
        clean(ax)
        if i == 0: ax.legend(loc="upper left")
    inter = read("figure5_information_interaction.csv").copy()
    inter["arch"] = inter.contrast_id.str.extract(r"E6-(.*)-QXF")[0].str.lower().str.replace("-", "_")
    inter["label"] = inter.arch.map(ARCH_LABELS)
    inter = inter.set_index("arch").loc[order].reset_index()
    ax4 = fig.add_subplot(gs[1, :8]); panel(ax4, "d", "Information × flexibility interaction")
    inter[["estimate", "ci_low", "ci_high"]] = inter[["estimate", "ci_low", "ci_high"]].mask(
        inter[["estimate", "ci_low", "ci_high"]].abs() < display_tolerance, 0.0)
    y = np.arange(3); ax4.errorbar(inter.estimate, y, xerr=[inter.estimate-inter.ci_low, inter.ci_high-inter.estimate], fmt="o",
                                   color=CARD["promoted"], capsize=2)
    ax4.axvline(0, color=CARD["charcoal"], lw=0.7); ax4.set(yticks=y, yticklabels=["Unlocks", "Dominated", "Robust"], xlabel="Interaction in value units")
    ax4.text(0.02, 0.06, "Dominated option = exact zero at display tolerance 1e-12",
             transform=ax4.transAxes, fontsize=5.6, color=CARD["adverse"])
    clean(ax4)
    ax5 = fig.add_subplot(gs[1, 8:]); quiet(ax5); panel(ax5, "e", "Exact finite-state checks")
    ax5.set(xlim=(0, 1), ylim=(0, 1))
    for i, text in enumerate(["Signal can be ignored", "Action sets are nested", "Exact-null tolerance  1e-12"]):
        y0 = 0.73 - i*0.27; ax5.scatter([0.10], [y0], s=24, color=CARD["promoted"], marker="o")
        ax5.text(0.20, y0, text, va="center", fontsize=5.9)
    return fig


def fig5b() -> plt.Figure:
    fig = base_figure(5, "B", "decision timing + archetype action tiles")
    gs = fig.add_gridspec(3, 12, left=0.06, right=0.975, bottom=0.08, top=0.88,
                          height_ratios=[0.7, 1.1, 0.9], hspace=0.62, wspace=0.75)
    ax = fig.add_subplot(gs[0, :]); quiet(ax); panel(ax, "a", "Information arrives before the action; flexibility changes the available set")
    ax.set(xlim=(0, 1), ylim=(0, 1))
    for x, lab in [(0.04, "State\nuncertain"), (0.29, "Signal\nq = 0.50–0.90"), (0.55, "Choose from\nrestricted / flexible set"), (0.82, "Payoff")]:
        box(ax, x, 0.30, 0.15, 0.38, lab, CARD["promoted"] + "22", fontsize=5.9)
    for x in [0.19, 0.44, 0.70]: arrow(ax, (x, 0.49), (x+0.09, 0.49))
    data = read("figure5_information_summary.csv")
    order = ["specialization_unlocks", "dominated_option_null", "robust_option_substitutes"]
    signs = ["complement", "unrelated", "substitute"]
    for i, (arch, sign) in enumerate(zip(order, signs)):
        a = fig.add_subplot(gs[1, i*4:(i+1)*4]); panel(a, chr(98+i), f"{ARCH_LABELS[arch]} · {sign}")
        d = data[data.archetype.eq(arch)]
        for level, col, off in [("low", CARD["corn"], -0.015), ("high", CARD["soybean"], 0.015)]:
            s = d[d.flexibility_level.eq(level)].sort_values("signal_accuracy")
            a.plot(s.signal_accuracy+off, s["mean"], color=col, marker="o", ms=3, lw=1)
        a.set(xlabel="Signal accuracy", ylabel="VOI" if i == 0 else "", xticks=[0.5,0.7,0.9]); clean(a)
    inter = read("figure5_information_interaction.csv").copy()
    inter["arch"] = inter.contrast_id.str.extract(r"E6-(.*)-QXF")[0].str.lower().str.replace("-", "_")
    inter = inter.set_index("arch").loc[order].reset_index()
    ax5 = fig.add_subplot(gs[2, :8]); panel(ax5, "e", "Registered interaction estimates")
    yy=np.arange(3); ax5.errorbar(inter.estimate, yy, xerr=[inter.estimate-inter.ci_low, inter.ci_high-inter.estimate], fmt="o", color=CARD["promoted"], capsize=2)
    ax5.axvline(0,color=CARD["charcoal"],lw=.7); ax5.set(yticks=yy,yticklabels=[ARCH_LABELS[x] for x in order],xlabel="Interaction in value units"); clean(ax5)
    ax6=fig.add_subplot(gs[2,8:]); quiet(ax6); panel(ax6,"f","Verification")
    ax6.set(xlim=(0,1),ylim=(0,1))
    ax6.text(0.03,.72,"PASS  information value ≥ 0",fontsize=6.1)
    ax6.text(0.03,.46,"PASS  ignore-signal policy available",fontsize=6.1)
    ax6.text(0.03,.20,"PASS  exact garbling map",fontsize=6.1)
    return fig


def geo_polygons() -> dict[str, list[np.ndarray]]:
    document = json.loads((ROOT / "data/goal17/raw/census_states_2024_5m.geojson").read_text())
    result: dict[str, list[np.ndarray]] = {}
    for feature in document["features"]:
        abbr = feature["properties"]["STUSAB"]
        geom = feature["geometry"]
        if not geom:
            continue
        groups = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        result[abbr] = [np.asarray(poly[0], dtype=float) for poly in groups]
    return result


def draw_us_map(ax: plt.Axes, values: dict[str, float], title: str) -> None:
    patches, colors = [], []
    for abbr, polys in geo_polygons().items():
        if abbr in {"AK", "HI", "PR", "GU", "VI", "MP", "AS"}: continue
        for poly in polys:
            patches.append(Polygon(poly, closed=True))
            colors.append(values.get(abbr, np.nan))
    pc = PatchCollection(patches, cmap=matplotlib.colors.LinearSegmentedColormap.from_list("goal17map", ["white", CARD["promoted"]]),
                         edgecolor=CARD["charcoal"], linewidth=0.25)
    masked = np.ma.masked_invalid(np.asarray(colors)); pc.set_array(masked); pc.set_clim(0, 1)
    pc.cmap.set_bad("#FFFFFF"); ax.add_collection(pc)
    ax.set(xlim=(-125, -66), ylim=(24, 50), aspect="equal"); quiet(ax); ax.set_title(title, loc="left", fontsize=7.2, fontweight="semibold", pad=8)


def empirical_map_values(definition: str = "operating_margin") -> dict[str, float]:
    states = read("figure6_goal16_state_summary.csv").query("ranking_definition == @definition")
    return {STATE_TO_ABBR[row.state]: float(row.mean_inversion_intensity) for row in states.itertuples() if row.state in STATE_TO_ABBR}


def lagged_forest(ax: plt.Axes) -> None:
    temp = read("figure6_goal16_temporal_model.csv").query("specification == 'primary_top'").set_index("ranking_definition").loc[DEFS].reset_index()
    y=np.arange(4); ax.errorbar(100*temp.estimate,y,xerr=[100*(temp.estimate-temp.ci_low),100*(temp.ci_high-temp.estimate)],fmt="o",color=CARD["adverse"],capsize=2)
    short = {"relative_yield": "Yield", "standardized_revenue": "Revenue",
             "operating_margin": "Op. margin", "total_cost_margin": "Cost margin"}
    ax.axvline(0,color=CARD["charcoal"],lw=.7); ax.set(yticks=y,yticklabels=[short[d] for d in DEFS],xlabel="Next-year share change (percentage points)"); clean(ax)


def fig6a() -> plt.Figure:
    fig=base_figure(6,"A","map-led empirical composite")
    gs=fig.add_gridspec(3,12,left=.075,right=.975,bottom=.075,top=.89,height_ratios=[1.45,.82,.9],hspace=.6,wspace=1.05)
    ax=fig.add_subplot(gs[0,:8]); panel(ax,"a","Operating-margin inversion intensity by state"); draw_us_map(ax,empirical_map_values(),"")
    ax.text(.01,-.09,"White states are outside the complete-case panel; colour is descriptive, not causal.",transform=ax.transAxes,fontsize=5.7,va="top")
    ax2=fig.add_subplot(gs[0,8:]); panel(ax2,"b","Definition sensitivity across states")
    states=read("figure6_goal16_state_summary.csv")
    for i,d in enumerate(DEFS):
        vals=states[states.ranking_definition.eq(d)].mean_inversion_intensity.to_numpy(); yy=np.full(len(vals),i)
        ax2.scatter(vals,yy,s=8,facecolor="white",edgecolor=CARD["charcoal"],lw=.4,alpha=.75)
        ax2.scatter([vals.mean()],[i],s=24,color=CARD["promoted"],zorder=3)
    ax2.set(yticks=np.arange(4),yticklabels=[DEF_LABELS[d] for d in DEFS],xlabel="Mean inversion intensity",xlim=(0,1)); clean(ax2)
    ax3=fig.add_subplot(gs[1,:7]); panel(ax3,"c","Strictly lagged association: all intervals include zero"); lagged_forest(ax3)
    ax4=fig.add_subplot(gs[1,7:]); panel(ax4,"d","Score and acreage leader transitions")
    trans=read("figure6_goal16_persistence_transition_summary.csv").groupby("transition_category",as_index=False).share.mean()
    order=["neither","score_only","acreage_only","both"]; trans=trans.set_index("transition_category").loc[order].reset_index()
    ax4.bar(np.arange(4),trans.share,color=["white",CARD["corn"],CARD["soybean"],CARD["promoted"]],edgecolor=CARD["charcoal"],lw=.5)
    ax4.set(xticks=np.arange(4),xticklabels=["Neither","Score\nonly","Acreage\nonly","Both"],ylabel="Mean transition share"); clean(ax4)
    ax5=fig.add_subplot(gs[2,:7]); panel(ax5,"e","Year-by-year inversion intensity")
    yrs=read("figure6_goal16_year_summary.csv")
    for d,col,mark in zip(DEFS,[CARD["corn"],CARD["promoted"],CARD["soybean"],CARD["adverse"]],["o","s","^","D"]):
        q=yrs[yrs.ranking_definition.eq(d)].sort_values("year"); ax5.plot(q.year,q.mean_inversion_intensity,color=col,marker=mark,ms=2.8,lw=.9,label=DEF_LABELS[d])
    ax5.set(xlabel="Year",ylabel="Mean inversion intensity",xticks=[2016,2018,2020,2022,2024],ylim=(0,1)); ax5.legend(ncol=2,loc="upper left"); clean(ax5)
    ax6=fig.add_subplot(gs[2,7:]); panel(ax6,"f","State versus national aggregation")
    agg=read("figure6_goal16_aggregation_boundary.csv").set_index("ranking_definition").loc[DEFS].reset_index(); y=np.arange(4)
    for i,row in agg.iterrows():
        if row.informative_years>0: ax6.plot([row.state_mean_inversion_intensity,row.national_mean_inversion_intensity],[i,i],color=CARD["charcoal"],lw=.7)
    ax6.scatter(agg.state_mean_inversion_intensity,y,color=CARD["soybean"],s=20,label="State mean")
    nat=agg.national_mean_inversion_intensity.where(agg.informative_years>0,np.nan); ax6.scatter(nat,y,facecolor="white",edgecolor=CARD["charcoal"],s=20,label="National")
    ax6.set(yticks=y,yticklabels=["Yield", "Revenue", "Operating", "Total cost"],xlabel="Inversion intensity",xlim=(0,1)); ax6.legend(ncol=2,loc="upper right"); clean(ax6)
    return fig


def fig6b() -> plt.Figure:
    fig=base_figure(6,"B","distribution-led empirical composite")
    gs=fig.add_gridspec(3,12,left=.085,right=.965,bottom=.075,top=.89,height_ratios=[1.2,.95,.8],hspace=.62,wspace=1.0)
    states=read("figure6_goal16_state_summary.csv")
    ax=fig.add_subplot(gs[0,:7]); panel(ax,"a","Ranked state distributions reveal definition sensitivity")
    for i,d in enumerate(DEFS):
        vals=np.sort(states[states.ranking_definition.eq(d)].mean_inversion_intensity.to_numpy())
        ax.plot(np.linspace(0,1,len(vals)),vals,color=[CARD["corn"],CARD["promoted"],CARD["soybean"],CARD["adverse"]][i],lw=1.2,label=DEF_LABELS[d])
    ax.set(xlabel="State quantile",ylabel="Mean inversion intensity",ylim=(0,1)); ax.legend(ncol=2,loc="upper left"); clean(ax)
    ax2=fig.add_subplot(gs[0,7:]); panel(ax2,"b","Spatial context"); draw_us_map(ax2,empirical_map_values(),"")
    ax2.text(.01,-.12,"Operating-margin definition; white = outside panel",transform=ax2.transAxes,fontsize=5.6,va="top")
    ax3=fig.add_subplot(gs[1,:7]); panel(ax3,"c","Annual paths are not stable across definitions")
    yrs=read("figure6_goal16_year_summary.csv")
    for i,d in enumerate(DEFS):
        q=yrs[yrs.ranking_definition.eq(d)].sort_values("year"); ax3.plot(q.year,q.mean_inversion_intensity,color=[CARD["corn"],CARD["promoted"],CARD["soybean"],CARD["adverse"]][i],lw=1,marker=["o","s","^","D"][i],ms=2.6)
    ax3.set(xlabel="Year",ylabel="Mean inversion intensity",xticks=[2016,2018,2020,2022,2024],ylim=(0,1)); clean(ax3)
    ax4=fig.add_subplot(gs[1,7:]); panel(ax4,"d","Lagged associations remain unresolved"); lagged_forest(ax4)
    ax4.set_yticklabels([])
    ax4.set_xlim(-1.35, 1.35)
    for yy, label in enumerate(["Yield", "Revenue", "Op. margin", "Cost margin"]):
        ax4.text(1.08, yy, label, ha="left", va="center", fontsize=5.8)
    ax5=fig.add_subplot(gs[2,:7]); panel(ax5,"e","Transition structure (217 events per definition)")
    trans=read("figure6_goal16_persistence_transition_summary.csv"); piv=trans.pivot(index="ranking_definition",columns="transition_category",values="share").loc[DEFS, ["neither","score_only","acreage_only","both"]]
    left=np.zeros(4)
    for cat,col in zip(piv.columns,["white",CARD["corn"],CARD["soybean"],CARD["promoted"]]):
        ax5.barh(np.arange(4),piv[cat],left=left,color=col,edgecolor=CARD["charcoal"],lw=.35,label=cat.replace("_"," ").title()); left+=piv[cat].to_numpy()
    ax5.set(yticks=np.arange(4),yticklabels=["Yield", "Revenue", "Op. margin", "Cost margin"],xlabel="Share of transitions",xlim=(0,1)); ax5.legend(ncol=4,loc="upper center",bbox_to_anchor=(.5,-.24)); clean(ax5)
    ax6=fig.add_subplot(gs[2,7:]); quiet(ax6); panel(ax6,"f","Sample and interpretation boundary")
    ax6.set(xlim=(0,1),ylim=(0,1))
    for i,(big,small) in enumerate([("31 states","2016–2024"),("248 state-years","complete cases"),("651 crop transitions","per definition")]):
        x=.02+i*.33; ax6.text(x,.64,big,fontsize=6.6,fontweight="semibold"); ax6.text(x,.43,small,fontsize=5.7,color=CARD["adverse"])
    ax6.text(.02,.13,"Descriptive compatibility ≠ identified mechanism",fontsize=6.1,fontweight="semibold")
    return fig


BUILDERS = {(1,"A"):fig1a,(1,"B"):fig1b,(2,"A"):fig2a,(2,"B"):fig2b,
            (3,"A"):fig3a,(3,"B"):fig3b,(4,"A"):fig4a,(4,"B"):fig4b,
            (5,"A"):fig5a,(5,"B"):fig5b,(6,"A"):fig6a,(6,"B"):fig6b}


def sha(path: Path) -> str:
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def normalize_svg(path: Path) -> None:
    """Remove renderer-only line-end spaces so generated vectors are diff-clean."""
    text = path.read_text(encoding="utf-8")
    path.write_text("\n".join(line.rstrip() for line in text.splitlines()) + "\n", encoding="utf-8")


def save(fig: plt.Figure, group: int, concept: str) -> dict[str,str]:
    stem=f"Figure{group}_concept{concept}"
    paths={ext:OUT/f"{stem}.{ext}" for ext in ["png","pdf","svg"]}
    fig.savefig(paths["png"],dpi=300,metadata={"Software":"crop-ranking-reversal GOAL17 candidate"})
    fig.savefig(paths["pdf"],metadata={"CreationDate":None,"ModDate":None})
    fig.savefig(paths["svg"],metadata={"Date":"2026-07-22"})
    normalize_svg(paths["svg"])
    plt.close(fig)
    return {k:str(v.relative_to(ROOT)) for k,v in paths.items()}


def accessible(image: Image.Image, mode: str) -> Image.Image:
    if mode == "full":
        return image.convert("RGB")
    if mode == "grayscale":
        return ImageOps.grayscale(image).convert("RGB")
    matrices = {
        "deuteranopia": np.array([[0.625, 0.375, 0.000], [0.700, 0.300, 0.000], [0.000, 0.300, 0.700]]),
        "protanopia": np.array([[0.567, 0.433, 0.000], [0.558, 0.442, 0.000], [0.000, 0.242, 0.758]]),
    }
    rgb = np.asarray(image.convert("RGB"), dtype=float) / 255.0
    transformed = np.clip(rgb @ matrices[mode].T, 0, 1)
    return Image.fromarray(np.uint8(np.rint(transformed * 255)))


def contact_sheet(records: list[dict[str,str]], mode: str) -> None:
    cell_w,cell_h,cols=1000,760,2; rows=6
    sheet=Image.new("RGB",(cell_w*cols,cell_h*rows),"white"); draw=ImageDraw.Draw(sheet)
    for idx,rec in enumerate(records):
        im=accessible(Image.open(ROOT/rec["png"]), mode); im.thumbnail((940,690),Image.Resampling.LANCZOS)
        row,col=divmod(idx,2); x=col*cell_w+(cell_w-im.width)//2; y=row*cell_h+50+(cell_h-60-im.height)//2
        sheet.paste(im,(x,y)); draw.text((col*cell_w+18,row*cell_h+16),f"Figure {rec['group']} · concept {rec['concept']}",fill=CARD["charcoal"])
    suffix = "" if mode == "full" else f"_{mode}"
    sheet.save(OUT/f"contact_sheet{suffix}.png",dpi=(150,150))


def main() -> int:
    OUT.mkdir(parents=True,exist_ok=True); records=[]
    for (group,concept),builder in BUILDERS.items():
        paths=save(builder(),group,concept)
        records.append({"group":str(group),"concept":concept,"width_mm":str(WIDTH_MM),"height_mm":str(HEIGHT_MM[group]),
                        **paths,"png_sha256":sha(ROOT/paths["png"]),"status":"RENDERED_FINAL_SIZE"})
    for mode in ["full", "grayscale", "deuteranopia", "protanopia"]:
        contact_sheet(records, mode)
    with (OUT/"candidate_manifest.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(records[0]),lineterminator="\n"); writer.writeheader(); writer.writerows(records)
    files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!="SHA256SUMS.txt")
    (OUT/"SHA256SUMS.txt").write_text("".join(f"{sha(p)}  {p.name}\n" for p in files),encoding="utf-8")
    print(json.dumps({"candidates":len(records),"contact_sheet":str((OUT/'contact_sheet.png').relative_to(ROOT))},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
