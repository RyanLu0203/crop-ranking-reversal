#!/usr/bin/env python3
"""Generate the six Issue #34 manuscript figures from registered outputs."""

from __future__ import annotations

import os
from pathlib import Path
import shutil

# Matplotlib's PDF backend otherwise embeds the wall-clock creation time.
os.environ.setdefault("SOURCE_DATE_EPOCH", "1785081600")

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import pandas as pd

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["svg.hashsalt"] = "issue34-scientific-reconstruction"
plt.rcParams["pdf.fonttype"] = 42

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "reconstruction" / "issue34" / "outputs"
OUT = ROOT / "figures" / "issue34"
SRC = OUT / "source_data"
OUT.mkdir(parents=True, exist_ok=True)
SRC.mkdir(parents=True, exist_ok=True)

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
            "font.size": 7.2,
            "axes.labelsize": 7.2,
            "axes.titlesize": 8,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "legend.fontsize": 6.3,
            "axes.linewidth": 0.7,
            "xtick.major.width": 0.7,
            "ytick.major.width": 0.7,
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
    ax.text(-0.13, 1.12, label, transform=ax.transAxes, weight="bold", fontsize=8, va="bottom")


def save(fig: plt.Figure, stem: str) -> None:
    svg_path = OUT / f"{stem}.svg"
    fig.savefig(svg_path, bbox_inches="tight")
    # Matplotlib writes path-data lines with trailing spaces.  Normalize the
    # text export so repository checks remain clean and deterministic.
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(
        OUT / f"{stem}.tiff",
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)


def copy_source(name: str) -> pd.DataFrame:
    src = DATA / name
    shutil.copy2(src, SRC / name)
    return pd.read_csv(src)


def figure1() -> None:
    cal = copy_source("score_and_margin_calibration.csv")
    pol = copy_source("policy_comparison.csv")
    full = pol.loc[pol["policy"] == "full_CVaR_operational"].iloc[0]
    crops = list(cal["crop"])
    fig = plt.figure(figsize=(7.205, 4.75))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.14, 1], height_ratios=[1, 1], hspace=0.48, wspace=0.42)

    ax = fig.add_subplot(gs[:, 0])
    ax.axis("off")
    ax.text(-0.03, 1.01, "a", transform=ax.transAxes, weight="bold", fontsize=8, va="bottom")
    boxes = [
        (0.02, 0.78, "Pre-decision\nagronomic score", PALE_GREEN),
        (0.56, 0.78, "Stochastic margin\nprice × yield − cost", PALE_TEAL),
        (0.56, 0.48, "Joint law\nmargins + dependence", PALE_BLUE),
        (0.02, 0.48, "Operational set\nland, budget, rotation,\ncontract, shared capacity", PALE_GREY),
        (0.20, 0.13, "Expected-profit optimum\nunder a loss-CVaR ceiling", LIGHT),
    ]
    for x, y, text, color in boxes:
        patch = FancyBboxPatch((x, y), 0.42 if y > 0.2 else 0.58, 0.14 if y > 0.2 else 0.16,
                               boxstyle="round,pad=0.02", facecolor=color, edgecolor=INK, linewidth=0.7)
        ax.add_patch(patch)
        ax.text(x + (0.21 if y > 0.2 else 0.29), y + (0.07 if y > 0.2 else 0.08),
                text, ha="center", va="center", fontsize=7)
    arrows = [
        ((0.44, 0.85), (0.56, 0.85)),
        ((0.77, 0.78), (0.77, 0.62)),
        ((0.23, 0.48), (0.37, 0.29)),
        ((0.77, 0.48), (0.63, 0.29)),
    ]
    for start, end in arrows:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=8, color=GREY, linewidth=0.8))

    ax = fig.add_subplot(gs[0, 1])
    panel(ax, "b")
    order = np.arange(len(crops))
    ax.barh(order, cal["historical_yield_potential_score"], color=[CROP_COLORS[c] for c in crops])
    ax.set_yticks(order, crops)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Historical relative-yield score")
    ax.set_title("Genuine score order", loc="left")
    ax.invert_yaxis()
    for y, v in zip(order, cal["historical_yield_potential_score"]):
        ax.text(v + 0.015, y, f"{v:.3f}", va="center", fontsize=6.5)

    ax = fig.add_subplot(gs[1, 0])
    panel(ax, "c")
    y = np.arange(len(crops))
    ax.errorbar(cal["mean_margin_real_2024_usd_per_acre"], y,
                xerr=cal["sd_margin_real_2024_usd_per_acre"], fmt="none",
                ecolor=GREY, elinewidth=1.2, capsize=2)
    for yi, c, mean in zip(y, crops, cal["mean_margin_real_2024_usd_per_acre"]):
        ax.scatter(mean, yi, s=36, color=CROP_COLORS[c], edgecolor=INK, linewidth=0.4, zorder=3)
    ax.set_yticks(y, crops)
    ax.invert_yaxis()
    ax.set_xlabel("Real margin (2024 US$ per acre), mean ± s.d.")
    ax.set_title("Calibrated cardinal margins", loc="left")

    ax = fig.add_subplot(gs[1, 1])
    panel(ax, "d")
    alloc = np.array([full[f"acres_{c}"] for c in crops])
    ax.bar(crops, alloc, color=[CROP_COLORS[c] for c in crops])
    ax.set_ylim(0, 0.5)
    ax.set_ylabel("Land share")
    ax.set_title("Full-model allocation", loc="left")
    ax.tick_params(axis="x", rotation=18)
    for i, v in enumerate(alloc):
        ax.text(i, v + 0.012, f"{v:.3f}", ha="center", fontsize=6.5)
    ax.text(
        0.02, 0.95, "selected complete rank reversal",
        transform=ax.transAxes, va="top", color=INK, weight="bold",
    )
    fig.suptitle("From agronomic ranking to risk-constrained operational allocation", x=0.06, ha="left", fontsize=10, weight="bold")
    save(fig, "Figure1")


def figure2() -> None:
    phase = copy_source("reversal_phase_diagram.csv")
    front = copy_source("reversal_frontier_summary.csv")
    fams = ["gaussian", "student_t", "clayton"]
    fig, axes = plt.subplots(1, 4, figsize=(7.205, 3.05), gridspec_kw={"width_ratios": [1, 1, 1, 1.15]})
    cmap = ListedColormap([PALE_GREY, PALE_TEAL, INK])
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
        ax.set_title(fam.replace("_", " ").title())
        panel(ax, chr(ord("a") + j))
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.5)
    ax = axes[3]
    for fam, color, marker in zip(fams, [INK, PURPLE, TEAL], ["o", "s", "^"]):
        sub = front[front["copula_family"] == fam].sort_values("kendall_tau")
        ax.plot(sub["kendall_tau"], sub["first_selected_reversal_risk_tolerance"],
                marker=marker, color=color, lw=1.3, label=fam.replace("_", " "))
    ax.set_xlabel("Kendall's $\\tau$")
    ax.set_ylabel("First reversal\nrisk-tolerance index")
    ax.set_ylim(-0.03, 1.03)
    ax.legend(title="Copula family", fontsize=6)
    ax.set_title("Conditional reversal frontier", fontsize=7.4)
    panel(ax, "d")
    true_strong = int(phase["selected_strong_reversal"].fillna(False).sum())
    fig.text(
        0.39, 0.015,
        f"grey: none     mint: pairwise only     dark teal: complete     "
        f"true strong (exclusion): {true_strong}",
        ha="center", fontsize=6.5,
    )
    fig.suptitle("Ranking reversal occupies a family- and risk-dependent phase", x=0.06, ha="left", fontsize=10, weight="bold")
    fig.subplots_adjust(top=0.8, bottom=0.23, wspace=0.42)
    save(fig, "Figure2")


def figure3() -> None:
    div = copy_source("diversification_failure.csv")
    policies = div[div["row_type"] == "registered_policy"].drop_duplicates("policy")
    order = [
        "x0_expected_profit_under_matched_gaussian",
        "xMV_registered_Gaussian_frontier_point",
        "xT_CVaR_under_matched_student_t",
    ]
    rows = policies.set_index("policy").loc[order].reset_index()
    frontier = div[div["row_type"] == "mean_variance_frontier"].sort_values("gamma")
    fig, axes = plt.subplots(
        1, 3, figsize=(7.205, 3.05),
        gridspec_kw={"width_ratios": [1.1, 1.15, 0.9]},
    )
    ax = axes[0]
    ax.plot(
        frontier["gaussian_profit_variance"],
        frontier["gaussian_expected_profit"],
        color=GREY, marker="o", ms=3, lw=1,
    )
    x0 = rows.iloc[0]
    xmv = rows.iloc[1]
    ax.scatter(
        [x0["gaussian_profit_variance"], xmv["gaussian_profit_variance"]],
        [x0["gaussian_expected_profit"], xmv["gaussian_expected_profit"]],
        color=[PURPLE, TEAL], edgecolor=INK, linewidth=0.4, s=35, zorder=4,
    )
    ax.annotate("$x^0$", (x0["gaussian_profit_variance"], x0["gaussian_expected_profit"]),
                xytext=(3, 3), textcoords="offset points")
    ax.annotate("$x^{MV}$", (xmv["gaussian_profit_variance"], xmv["gaussian_expected_profit"]),
                xytext=(3, 3), textcoords="offset points")
    ax.set_xlabel("Gaussian profit variance")
    ax.set_ylabel("Expected profit (US$ per acre)")
    ax.set_title("Registered mean–variance frontier")
    panel(ax, "a")

    ax = axes[1]
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
    ax.set_xticks(x, ["benchmark\n$x^0$", "Gaussian\n$x^{MV}$", "tail-aware\n$x^T$"])
    ax.set_ylabel("Land share")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.22))
    ax.set_title("Policy allocations")
    panel(ax, "b")

    ax = axes[2]
    vals = rows["true_law_loss_CVaR"].to_numpy()
    ax.bar(np.arange(len(vals)), vals, color=[PURPLE, TEAL, INK])
    ax.set_xticks(np.arange(len(vals)), ["$x^0$", "$x^{MV}$", "$x^T$"])
    ax.set_ylabel("True-law loss-CVaR\n(US$ per acre)")
    ceiling = float(rows["risk_ceiling"].iloc[0])
    ax.axhline(ceiling, color=RED, ls="--", lw=1)
    ax.text(0.05, ceiling + 1.2, "true-law ceiling", fontsize=6, color=RED)
    ax.set_title("Student-$t$ true-law test")
    panel(ax, "c")
    reduction = 100 * float(xmv["gaussian_variance_reduction_fraction"])
    fig.suptitle(
        f"Gaussian variance falls {reduction:.1f}%, yet the registered policy fails the true-law ceiling",
        x=0.06, ha="left", fontsize=10, weight="bold",
    )
    fig.subplots_adjust(top=0.76, bottom=0.28, wspace=0.48)
    save(fig, "Figure3")


def figure4() -> None:
    margin = copy_source("margin_mechanism.csv")
    risk = copy_source("risk_induced_reversal.csv")
    operation = copy_source("operational_mechanism.csv")
    fig, axes = plt.subplots(
        1, 3, figsize=(7.205, 3.25),
        gridspec_kw={"width_ratios": [1.05, 1.05, 1.2]},
    )
    ax = axes[0]
    for _, row in margin.iterrows():
        crop = row["crop"]
        ax.scatter(
            row["score"], row["mean_margin_real_2024_usd_per_acre"],
            s=45, color=CROP_COLORS[crop], edgecolor=INK, linewidth=0.4,
        )
        ax.annotate(crop.replace("Winter ", ""), (
            row["score"], row["mean_margin_real_2024_usd_per_acre"]
        ), xytext=(4, 3), textcoords="offset points", fontsize=6)
    ax.set_xlabel("Historical relative-yield score")
    ax.set_ylabel("Mean margin (2024 US$ per acre)")
    ax.set_title("Official score–margin separation")
    panel(ax, "a")

    ax = axes[1]
    risk = risk.sort_values("risk_tolerance")
    ax.plot(
        risk["risk_tolerance"], risk["allocation_high"],
        color=SOY, marker="o", ls="-", label="Soybean",
    )
    ax.plot(
        risk["risk_tolerance"], risk["allocation_low"],
        color=CORNF, marker="s", ls="--", label="Corn",
    )
    ax.fill_between(
        risk["risk_tolerance"], risk["allocation_low"], risk["allocation_high"],
        where=risk["allocation_high"] < risk["allocation_low"],
        color=PALE_GREEN, alpha=0.8,
    )
    ax.set_xlabel("Risk-tolerance index (tight $\\rightarrow$ loose)")
    ax.set_ylabel("Land share")
    ax.set_title("Risk-induced crossing")
    ax.legend()
    panel(ax, "b")

    ax = axes[2]
    rotation = operation[
        operation["operational_path"] == "soybean_rotation_tightening"
    ].sort_values("soybean_rotation_cap", ascending=False)
    ax.plot(
        rotation["soybean_rotation_cap"], rotation["allocation_high"],
        color=SOY, marker="o", ls="-", label="Soybean",
    )
    ax.plot(
        rotation["soybean_rotation_cap"], rotation["allocation_low"],
        color=CORNF, marker="s", ls="--", label="Corn",
    )
    ax.axvline(
        rotation["first_operational_crossing_cap"].iloc[0],
        color=GREY, ls="--", lw=0.9,
    )
    ax.invert_xaxis()
    ax.set_xlabel("Soybean rotation cap (loose $\\rightarrow$ tight)")
    ax.set_ylabel("Land share")
    ax.set_title("Operational crossing")
    ax.legend()
    panel(ax, "c")
    fig.suptitle(
        "Margin, downside risk and operations produce distinct counterfactual signatures",
        x=0.06, ha="left", fontsize=10, weight="bold",
    )
    fig.subplots_adjust(top=0.8, bottom=0.25, wspace=0.48)
    save(fig, "Figure4")


def figure5() -> None:
    info = copy_source("information_flexibility.csv")
    paths = ["post_signal_acreage_reallocation", "state_shock_buffering_recourse"]
    fig, axes = plt.subplots(
        1, 3, figsize=(7.205, 3.15),
        gridspec_kw={"width_ratios": [1, 1, 1]},
    )
    vmax = max(0.1, info["value_of_information"].max())
    ax = axes[0]
    sub = info[info["flexibility_path"] == paths[0]]
    piv = sub.pivot(
        index="signal_accuracy", columns="flexibility_level",
        values="value_of_information",
    )
    im = ax.imshow(
        piv.to_numpy(), origin="lower", aspect="auto",
        cmap=INFO_CMAP, vmin=0, vmax=vmax,
    )
    ax.set_xticks(np.arange(len(piv.columns)), [f"{v:.1f}" for v in piv.columns])
    ax.set_yticks(np.arange(len(piv.index)), [f"{v:.1f}" for v in piv.index])
    ax.set_xlabel("Flexibility level")
    ax.set_ylabel("Signal accuracy")
    ax.set_title("Information value")
    panel(ax, "a")
    cb = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.03)
    cb.set_label("US$ per acre")
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.5)

    finite_cross = info["discrete_cross_difference"].dropna()
    cross_abs = max(0.01, float(finite_cross.abs().max()))
    for j, path in enumerate(paths, start=1):
        ax = axes[j]
        sub = info[info["flexibility_path"] == path]
        piv = sub.pivot(
            index="signal_accuracy", columns="flexibility_level",
            values="discrete_cross_difference",
        )
        cross_im = ax.imshow(
            piv.to_numpy(), origin="lower", aspect="auto",
            cmap=CROSS_CMAP, vmin=-cross_abs, vmax=cross_abs,
        )
        ax.set_xticks(np.arange(len(piv.columns)), [f"{v:.1f}" for v in piv.columns])
        ax.set_yticks(np.arange(len(piv.index)), [f"{v:.1f}" for v in piv.index])
        ax.set_xlabel("Upper flexibility $\\phi_2$")
        if j == 1:
            ax.set_ylabel("Upper accuracy $q_2$")
        ax.set_title("Reallocation $\\Delta_{q,\\phi}V$" if j == 1 else "Buffering $\\Delta_{q,\\phi}V$")
        panel(ax, chr(ord("a") + j))
        values = piv.to_numpy()
        for row_index in range(values.shape[0]):
            for column_index in range(values.shape[1]):
                value = values[row_index, column_index]
                if not np.isfinite(value):
                    continue
                sign = "+" if value > 1e-7 else "−" if value < -1e-7 else "0"
                ax.text(
                    column_index, row_index, sign,
                    ha="center", va="center", fontsize=6,
                    color=INK if abs(value) < 0.65 * cross_abs else "white",
                )
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.5)
    fig.subplots_adjust(top=0.78, bottom=0.2, left=0.08, right=0.90, wspace=0.62)
    cross_cax = fig.add_axes([0.925, 0.28, 0.012, 0.44])
    cb2 = fig.colorbar(cross_im, cax=cross_cax)
    cb2.set_label("Adjacent-grid cross-difference")
    fig.suptitle(
        "The shared-CVaR model is classified by adjacent-grid cross-differences",
        x=0.06, ha="left", fontsize=10, weight="bold",
    )
    save(fig, "Figure5")


def figure6() -> None:
    ext = copy_source("external_descriptive_evidence.csv")
    boot = copy_source("bootstrap_replications.csv")
    uncertainty = copy_source("uncertainty_summary.csv")
    fig, axes = plt.subplots(1, 3, figsize=(7.205, 3.25), gridspec_kw={"width_ratios": [1.15, 1, 1]})
    ax = axes[0]
    rates = ext.dropna(subset=["top_rank_reversal_rate"]).copy()
    y = np.arange(len(rates))
    x = rates["top_rank_reversal_rate"].to_numpy()
    lo = rates["top_rank_reversal_rate_ci_low"].to_numpy()
    hi = rates["top_rank_reversal_rate_ci_high"].to_numpy()
    ax.errorbar(x, y, xerr=[x - lo, hi - x], fmt="o", color=INK, ecolor=TEAL, capsize=2)
    ax.set_yticks(y, rates["ranking_definition"].str.replace("_", " "))
    ax.set_xlim(0, 1)
    ax.set_xlabel("Top-rank disagreement rate")
    ax.set_title("31 states, 248 state-years")
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
        fmt="o", color=INK, ecolor=TEAL, capsize=3, markersize=6,
    )
    ax.set_xlim(0.8, 1.005)
    ax.set_ylim(-0.6, 0.6)
    ax.set_yticks([0], ["Selected pairwise\nreversal"])
    ax.set_xlabel("Historical-resample frequency")
    ax.set_title("Exact Clopper–Pearson 95% interval")
    ax.text(
        0.98, 0.15,
        f"{int(pair['event_count'])}/{int(pair['bootstrap_replications'])}\n"
        f"[{low:.3f}, {high:.3f}]",
        transform=ax.transAxes, ha="right", va="top", fontsize=6.5,
    )
    panel(ax, "b")

    ax = axes[2]
    vals = [boot[f"allocation_{c.replace(' ', '_')}"] for c in ["Corn", "Soybean", "Winter Wheat"]]
    bp = ax.boxplot(
        vals,
        labels=["Corn", "Soybean", "Wheat"],
        patch_artist=True,
        widths=0.55,
        showfliers=False,
        boxprops={"edgecolor": INK},
        whiskerprops={"color": INK},
        capprops={"color": INK},
        medianprops={"color": INK},
    )
    for patch, c in zip(bp["boxes"], [CORNF, SOY, WHEAT]):
        patch.set_facecolor(c)
        patch.set_alpha(0.8)
    ax.set_ylabel("Bootstrap land share")
    ax.set_title("Continuous resample distributions")
    panel(ax, "c")
    fig.suptitle(
        "Resampling quantifies short-record sensitivity, not farm-level prevalence",
        x=0.06, ha="left", fontsize=10, weight="bold",
    )
    fig.subplots_adjust(top=0.79, bottom=0.2, wspace=0.55)
    save(fig, "Figure6")


def main() -> None:
    style()
    figure1()
    figure2()
    figure3()
    figure4()
    figure5()
    figure6()
    print(f"Wrote figures and source data to {OUT}")


if __name__ == "__main__":
    main()
