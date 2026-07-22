"""Single source of truth for the user-supplied six-colour card."""

from __future__ import annotations

import matplotlib.pyplot as plt


CARD = {
    "charcoal": "#3D3539",
    "promoted": "#0F9EA8",
    "soybean": "#008B82",
    "corn": "#45728F",
    "winter_wheat": "#8CD1B2",
    "adverse": "#8B84A3",
}
CROP_COLORS = {"Corn": CARD["corn"], "Soybean": CARD["soybean"], "Winter Wheat": CARD["winter_wheat"]}
SEMANTIC_COLORS = {
    "text_axes": CARD["charcoal"],
    "positive_supported": CARD["promoted"],
    "adverse_unresolved": CARD["adverse"],
    "observed_acreage": CARD["charcoal"],
    "calibrated_model": CARD["corn"],
}
ALLOWED_HEX = {value.lower() for value in CARD.values()} | {"#ffffff"}


def palette() -> dict[str, str]:
    """Return semantic names plus compatibility aliases, all on the fixed card."""
    return {
        **CARD,
        "navy": CARD["corn"],
        "teal": CARD["soybean"],
        "amber": CARD["winter_wheat"],
        "steel": CARD["adverse"],
        "rose": CARD["adverse"],
        "pale_blue": CARD["corn"],
        "pale_rose": CARD["adverse"],
        "mint": CARD["winter_wheat"],
        "light_gray": CARD["adverse"],
        "paper": "#FFFFFF",
    }


def apply_nature_style() -> None:
    charcoal = CARD["charcoal"]
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans"],
            "svg.fonttype": "none",
            "svg.hashsalt": "CRR-GOAL16-NATURE-VIS-2026-07-22",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "font.size": 6.8,
            "axes.labelsize": 6.8,
            "axes.titlesize": 7.2,
            "axes.titleweight": "semibold",
            "xtick.labelsize": 5.8,
            "ytick.labelsize": 5.8,
            "legend.fontsize": 5.7,
            "text.color": charcoal,
            "axes.labelcolor": charcoal,
            "axes.edgecolor": charcoal,
            "xtick.color": charcoal,
            "ytick.color": charcoal,
            "axes.prop_cycle": plt.cycler(color=[CARD["corn"], CARD["soybean"], CARD["winter_wheat"]]),
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
            "savefig.facecolor": "white",
            "lines.solid_capstyle": "round",
        }
    )
