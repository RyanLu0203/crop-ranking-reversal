"""Shared publication figure style for the Nature Food submission figures."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt


MM_PER_INCH = 25.4
SINGLE_COLUMN_MM = 89
DOUBLE_COLUMN_MM = 183
MAX_HEIGHT_MM = 170

SCI_COLORS: Mapping[str, str] = {
    "deep_blue": "#45728F",
    "blue_violet": "#8B84A3",
    "lavender": "#8CD1B2",
    "blush": "#8CD1B2",
    "apricot": "#0F9EA8",
    "coral": "#008B82",
    "terracotta": "#3D3539",
    "warm_grey": "#D6D6D6",
    "sand": "#DDEBE6",
    "teal": "#008B82",
    "charcoal": "#3D3539",
}

PALETTE: Mapping[str, str] = {
    "neutral": "#3F3F3F",
    "light_neutral": "#ECEAE7",
    "suitability": SCI_COLORS["deep_blue"],
    "expected_yield": SCI_COLORS["blue_violet"],
    "profit": SCI_COLORS["lavender"],
    "cost": SCI_COLORS["terracotta"],
    "placebo": SCI_COLORS["blush"],
    "universal": SCI_COLORS["deep_blue"],
    "possible": SCI_COLORS["apricot"],
    "none": SCI_COLORS["blush"],
    "risk": SCI_COLORS["terracotta"],
    "accent": SCI_COLORS["coral"],
    "feasible_fill": "#EEF1F3",
    "paper": "#FFFFFF",
}

METHOD_COLORS: Mapping[str, str] = {
    "N1_random": SCI_COLORS["blush"],
    "N2_suitability": SCI_COLORS["deep_blue"],
    "N3_expected_yield": SCI_COLORS["blue_violet"],
    "N4_expected_profit": SCI_COLORS["lavender"],
    "N5_cost_aware": SCI_COLORS["terracotta"],
}

CROP_COLORS: Mapping[str, str] = {
    "Corn": SCI_COLORS["deep_blue"],
    "Soybean": SCI_COLORS["lavender"],
    "Winter Wheat": SCI_COLORS["terracotta"],
}

POLICY_COLORS: Mapping[str, str] = {
    "CVaR": SCI_COLORS["deep_blue"],
    "EO": SCI_COLORS["blue_violet"],
    "MV": SCI_COLORS["lavender"],
    "SU": SCI_COLORS["terracotta"],
}

# Stable policy vocabulary for the complete visual system. A decision rule must
# retain the same hue, label and marker in every figure.
DECISION_POLICY_ORDER: Sequence[str] = (
    "equal_share_feasible",
    "lagged_acreage_persistence",
    "suitability_proportional",
    "suitability_rank_greedy",
    "expected_profit_rank_greedy",
    "cost_aware_rank_greedy",
    "constrained_expected_profit",
    "expost_feasible_oracle",
)

DECISION_POLICY_LABELS: Mapping[str, str] = {
    "equal_share_feasible": "Equal share",
    "lagged_acreage_persistence": "Lagged acreage",
    "suitability_proportional": "Yield-proxy proportional",
    "suitability_rank_greedy": "Yield-proxy greedy",
    "expected_profit_rank_greedy": "Expected-profit greedy",
    "cost_aware_rank_greedy": "Cost-aware greedy",
    "constrained_expected_profit": "Constrained expected profit",
    "expost_feasible_oracle": "Ex-post oracle",
}

DECISION_POLICY_SHORT_LABELS: Mapping[str, str] = {
    "equal_share_feasible": "Equal share",
    "lagged_acreage_persistence": "Lagged acreage",
    "suitability_proportional": "Yield-proxy prop.",
    "suitability_rank_greedy": "Yield-proxy greedy",
    "expected_profit_rank_greedy": "Profit greedy",
    "cost_aware_rank_greedy": "Cost-aware greedy",
    "constrained_expected_profit": "Constrained profit",
    "expost_feasible_oracle": "Ex-post oracle",
}

DECISION_POLICY_COLORS: Mapping[str, str] = {
    "equal_share_feasible": "#AFAFAF",
    "lagged_acreage_persistence": "#8CD1B2",
    "suitability_proportional": "#45728F",
    "suitability_rank_greedy": "#0F9EA8",
    "expected_profit_rank_greedy": "#008B82",
    "cost_aware_rank_greedy": "#8B84A3",
    "constrained_expected_profit": "#3D3539",
    "expost_feasible_oracle": "#111111",
}

DECISION_POLICY_MARKERS: Mapping[str, str] = {
    "equal_share_feasible": "o",
    "lagged_acreage_persistence": "s",
    "suitability_proportional": "D",
    "suitability_rank_greedy": "^",
    "expected_profit_rank_greedy": "v",
    "cost_aware_rank_greedy": "P",
    "constrained_expected_profit": "X",
    "expost_feasible_oracle": "*",
}

RANKING_COLORS: Mapping[str, str] = {
    "exact_permutation": "#555555",
    "yield_proxy": "#45728F",
    "expected_profit": "#008B82",
    "cost_aware": "#8B84A3",
}

METHOD_LABELS: Mapping[str, str] = {
    "N1_random": "Random placebo",
    "N2_suitability": "Yield proxy",
    "N3_expected_yield": "Expected yield",
    "N4_expected_profit": "Expected profit",
    "N5_cost_aware": "Cost-aware",
    "N6_feasibility_aware": "Feasibility screen",
}

UNIT_LABELS: Mapping[str, str] = {
    "policy_row": "county-year-policy row",
    "crop_pair_row": "event-crop-pair row",
    "event_id": "unique decision event",
    "normalized_gap": "normalized acreage gap",
}


def mm_to_inches(width_mm: float, height_mm: float) -> tuple[float, float]:
    return width_mm / MM_PER_INCH, height_mm / MM_PER_INCH


def apply_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
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
            "axes.edgecolor": "#4A4A4A",
            "axes.labelcolor": "#303030",
            "xtick.color": "#4A4A4A",
            "ytick.color": "#4A4A4A",
            "xtick.major.width": 0.45,
            "ytick.major.width": 0.45,
            "xtick.major.size": 2.2,
            "ytick.major.size": 2.2,
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.dpi": 600,
            "figure.dpi": 150,
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "axes.titlepad": 6.0,
            "lines.solid_capstyle": "round",
            "patch.linewidth": 0.55,
        }
    )


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.120,
        1.040,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=7.8,
        fontweight="bold",
        clip_on=False,
    )


def save_figure(fig: plt.Figure, stem: Path) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    svg_path = stem.with_suffix(".svg")
    fig.savefig(svg_path, bbox_inches="tight")
    # Matplotlib emits trailing spaces in path-data lines; normalize the
    # editable source so generated figures also pass repository diff checks.
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text("\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n", encoding="utf-8")
    fig.savefig(stem.with_suffix(".png"), bbox_inches="tight", dpi=600)
