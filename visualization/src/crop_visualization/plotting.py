"""Publication-quality chart exports for the numerical experiments."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

FONT_FAMILY = ["Aptos", "Inter", "Segoe UI", "DejaVu Sans", "Arial", "sans-serif"]
TOKENS = {
    "surface": "#FCFCFD",
    "panel": "#FFFFFF",
    "ink": "#1F2430",
    "muted": "#6F768A",
    "grid": "#E6E8F0",
    "axis": "#D7DBE7",
}
COLOR_FAMILIES = {
    "blue": {"base": "#A3BEFA", "mid": "#5477C4", "dark": "#2E4780"},
    "gold": {"base": "#FFE15B", "mid": "#B8A037", "dark": "#736422"},
    "orange": {"base": "#F0986E", "mid": "#CC6F47", "dark": "#804126"},
    "olive": {"base": "#A3D576", "mid": "#71B436", "dark": "#386411"},
    "pink": {"base": "#F390CA", "mid": "#BD569B", "dark": "#8A3A6F"},
}


def use_chart_theme() -> None:
    sns.set_theme(
        style="whitegrid",
        rc={
            "figure.facecolor": TOKENS["surface"],
            "axes.facecolor": TOKENS["panel"],
            "axes.edgecolor": TOKENS["axis"],
            "axes.labelcolor": TOKENS["ink"],
            "axes.grid": True,
            "grid.color": TOKENS["grid"],
            "grid.linewidth": 0.8,
            "font.family": "sans-serif",
            "font.sans-serif": FONT_FAMILY,
            "axes.spines.top": False,
            "axes.spines.right": False,
        },
    )


def add_chart_header(fig: plt.Figure, ax: plt.Axes, title: str, subtitle: str) -> None:
    ax.set_title("")
    left = ax.get_position().x0
    fig.subplots_adjust(top=0.82)
    fig.text(left, 0.97, title, ha="left", va="top", fontsize=13, fontweight="semibold", color=TOKENS["ink"])
    fig.text(left, 0.92, subtitle, ha="left", va="top", fontsize=9, color=TOKENS["muted"])
    sns.despine(ax=ax)


def save_figure(fig: plt.Figure, path_without_suffix: Path) -> None:
    path_without_suffix.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path_without_suffix.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(path_without_suffix.with_suffix(".png"), dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_acreage_vs_tail_dependence(df: pd.DataFrame, output_base: Path) -> None:
    use_chart_theme()
    crop_cols = [col for col in df.columns if col.startswith("acres_")]
    long_df = df.melt(
        id_vars=["lambda_L", "ranking_reversal"],
        value_vars=crop_cols,
        var_name="crop",
        value_name="acres",
    )
    long_df["crop"] = long_df["crop"].str.replace("acres_", "", regex=False)
    palette = {
        "Corn": COLOR_FAMILIES["orange"]["base"],
        "Soybean": COLOR_FAMILIES["blue"]["base"],
        "Winter Wheat": COLOR_FAMILIES["olive"]["base"],
    }
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    sns.lineplot(
        data=long_df,
        x="lambda_L",
        y="acres",
        hue="crop",
        style="crop",
        markers=True,
        dashes=False,
        palette=palette,
        linewidth=1.4,
        ax=ax,
    )
    reversed_rows = df.loc[df["ranking_reversal"] == True]  # noqa: E712
    if not reversed_rows.empty:
        threshold = float(reversed_rows.sort_values("lambda_L").iloc[0]["lambda_L"])
        ax.axvline(threshold, color=TOKENS["ink"], linestyle=":", linewidth=1.0)
        ax.text(threshold, ax.get_ylim()[1] * 0.92, "reversal threshold", rotation=90, va="top", ha="right", fontsize=8)
    ax.set_xlabel("Lower-tail dependence lambda_L")
    ax.set_ylabel("Optimal acreage")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=3, frameon=False, borderaxespad=0)
    add_chart_header(
        fig,
        ax,
        "Optimal acreage shifts as lower-tail dependence rises",
        "Simulated Clayton copula scenarios; CVaR is computed on portfolio losses at alpha = 0.90.",
    )
    save_figure(fig, output_base)


def plot_policy_tradeoff(df: pd.DataFrame, output_base: Path) -> None:
    use_chart_theme()
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    palette = {
        "SU": COLOR_FAMILIES["gold"]["base"],
        "EO": COLOR_FAMILIES["orange"]["base"],
        "MV": COLOR_FAMILIES["pink"]["base"],
        "CVaR": COLOR_FAMILIES["blue"]["base"],
    }
    sns.scatterplot(
        data=df,
        x="cvar_loss",
        y="expected_profit",
        hue="policy",
        style="cvar_violation",
        s=120,
        palette=palette,
        edgecolor=TOKENS["ink"],
        linewidth=0.7,
        ax=ax,
    )
    for _, row in df.iterrows():
        ax.text(row["cvar_loss"], row["expected_profit"], f" {row['policy']}", va="center", fontsize=8)
    ax.axvline(30000, color=TOKENS["ink"], linestyle=":", linewidth=1.0, label="CVaR limit")
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_xlabel("CVaR loss")
    ax.set_ylabel("Expected profit")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=4, frameon=False, borderaxespad=0)
    add_chart_header(
        fig,
        ax,
        "Benchmark policies trade average profit against downside loss",
        "Each point is evaluated on the same simulated scenario set; vertical reference is the lender CVaR limit.",
    )
    save_figure(fig, output_base)


def plot_diversification_failure(df: pd.DataFrame, output_base: Path) -> None:
    use_chart_theme()
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    palette = {"Gaussian": COLOR_FAMILIES["blue"]["base"], "Clayton": COLOR_FAMILIES["orange"]["base"]}
    sns.lineplot(
        data=df,
        x="wheat_acres",
        y="cvar_loss",
        hue="copula",
        style="copula",
        markers=True,
        palette=palette,
        linewidth=1.4,
        ax=ax,
    )
    clayton = df.loc[df["copula"] == "Clayton"].sort_values("wheat_acres")
    if not clayton.empty:
        diffs = clayton["cvar_loss"].diff()
        increasing = clayton.loc[diffs > 0]
        if not increasing.empty:
            start = float(increasing.iloc[0]["wheat_acres"])
            ax.axvspan(start, clayton["wheat_acres"].max(), color=COLOR_FAMILIES["orange"]["base"], alpha=0.10)
            ax.text(start, ax.get_ylim()[1] * 0.92, "pseudo-diversification region", fontsize=8, color=TOKENS["ink"])
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_xlabel("Winter Wheat acreage")
    ax.set_ylabel("CVaR loss")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=2, frameon=False, borderaxespad=0)
    add_chart_header(
        fig,
        ax,
        "Tail dependence can turn added acreage into higher downside loss",
        "Controlled two-crop base with wheat varied from 0 to 150 acres; CVaR uses the worst 10 percent loss tail.",
    )
    save_figure(fig, output_base)


def plot_information_value(df: pd.DataFrame, output_base: Path) -> None:
    use_chart_theme()
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    palette = {
        "No information": "#C5CAD3",
        "75% accurate signal": COLOR_FAMILIES["gold"]["base"],
        "Perfect signal": COLOR_FAMILIES["blue"]["base"],
    }
    sns.lineplot(
        data=df,
        x="phi",
        y="value_of_information",
        hue="signal_regime",
        style="signal_regime",
        markers=True,
        palette=palette,
        linewidth=1.4,
        ax=ax,
    )
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_xlabel("Operational flexibility phi")
    ax.set_ylabel("Value of information")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=3, frameon=False, borderaxespad=0)
    add_chart_header(
        fig,
        ax,
        "Climate information is more valuable when operations can respond",
        "Value is expected profit under signal-conditioned allocation minus prior allocation, averaged across high/low corn states.",
    )
    save_figure(fig, output_base)


def plot_reversal_threshold_heatmap(df: pd.DataFrame, output_base: Path) -> None:
    use_chart_theme()
    matrix = df.pivot(index="alpha", columns="kappa", values="reversal_threshold_lambda_L").sort_index(ascending=False)
    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    cmap = sns.blend_palette(
        [TOKENS["panel"], COLOR_FAMILIES["gold"]["base"], COLOR_FAMILIES["orange"]["base"]],
        as_cmap=True,
    )
    sns.heatmap(
        matrix,
        ax=ax,
        cmap=cmap,
        annot=True,
        fmt=".3f",
        linewidths=1.0,
        linecolor=TOKENS["panel"],
        cbar_kws={"label": "Threshold lambda_L"},
    )
    ax.set_xlabel("CVaR limit kappa")
    ax.set_ylabel("CVaR confidence alpha")
    add_chart_header(
        fig,
        ax,
        "Ranking reversal thresholds shift with risk tolerance",
        "Cells report the first simulated lower-tail dependence level where Soybean acreage exceeds Corn acreage.",
    )
    save_figure(fig, output_base)


def plot_risk_binding_acreage_vs_tail_dependence(df: pd.DataFrame, output_base: Path) -> None:
    use_chart_theme()
    crop_cols = [col for col in df.columns if col.startswith("acres_")]
    long_df = df.melt(
        id_vars=["lambda_L", "ranking_reversal", "cvar_binds", "budget_binds"],
        value_vars=crop_cols,
        var_name="crop",
        value_name="acres",
    )
    long_df["crop"] = long_df["crop"].str.replace("acres_", "", regex=False)
    palette = {
        "Corn": COLOR_FAMILIES["orange"]["base"],
        "Soybean": COLOR_FAMILIES["blue"]["base"],
        "Winter Wheat": COLOR_FAMILIES["olive"]["base"],
    }
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    sns.lineplot(
        data=long_df,
        x="lambda_L",
        y="acres",
        hue="crop",
        style="crop",
        markers=True,
        dashes=False,
        palette=palette,
        linewidth=1.4,
        ax=ax,
    )
    reversed_rows = df.loc[df["ranking_reversal"] == True]  # noqa: E712
    if not reversed_rows.empty:
        threshold = float(reversed_rows.sort_values("lambda_L").iloc[0]["lambda_L"])
        ax.axvline(threshold, color=TOKENS["ink"], linestyle=":", linewidth=1.0)
        ax.text(threshold, ax.get_ylim()[1] * 0.92, "reversal threshold", rotation=90, va="top", ha="right", fontsize=8)
    ax.set_xlabel("Lower-tail dependence lambda_L")
    ax.set_ylabel("Optimal acreage")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=3, frameon=False, borderaxespad=0)
    add_chart_header(
        fig,
        ax,
        "Risk-binding stress acreage by lower-tail dependence",
        "Selected stress regime; table reports whether CVaR and budget constraints bind at each theta.",
    )
    save_figure(fig, output_base)


def plot_diversification_failure_stress(df: pd.DataFrame, output_base: Path) -> None:
    use_chart_theme()
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    palette = {"Gaussian": COLOR_FAMILIES["blue"]["base"], "Clayton": COLOR_FAMILIES["orange"]["base"]}
    sns.lineplot(
        data=df,
        x="wheat_acres",
        y="cvar_loss",
        hue="copula",
        style="copula",
        markers=True,
        palette=palette,
        linewidth=1.4,
        ax=ax,
    )
    clayton = df.loc[df["copula"] == "Clayton"].sort_values("wheat_acres")
    observed = False
    if not clayton.empty:
        diffs = clayton["cvar_loss"].diff()
        increasing = clayton.loc[diffs > 0]
        observed = bool((diffs > 0).any() and (diffs < 0).any())
        if not increasing.empty:
            start = float(increasing.iloc[0]["wheat_acres"])
            ax.axvspan(start, clayton["wheat_acres"].max(), color=COLOR_FAMILIES["orange"]["base"], alpha=0.10)
            ax.text(start, ax.get_ylim()[1] * 0.92, "CVaR increases after this point", fontsize=8, color=TOKENS["ink"])
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_xlabel("Winter Wheat acreage")
    ax.set_ylabel("CVaR loss")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=2, frameon=False, borderaxespad=0)
    add_chart_header(
        fig,
        ax,
        "Diversification failure stress test" if observed else "Diversification stress diagnostic",
        "Gaussian and Clayton runs use matched marginals; failure is claimed only when the Clayton CVaR curve is non-monotonic.",
    )
    save_figure(fig, output_base)


def plot_information_value_stress(df: pd.DataFrame, output_base: Path) -> None:
    use_chart_theme()
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    palette = {
        "No information": "#C5CAD3",
        "75% accurate signal": COLOR_FAMILIES["gold"]["base"],
        "Perfect signal": COLOR_FAMILIES["blue"]["base"],
    }
    sns.lineplot(
        data=df,
        x="phi",
        y="value_of_information",
        hue="signal_regime",
        style="signal_regime",
        markers=True,
        palette=palette,
        linewidth=1.4,
        ax=ax,
    )
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_xlabel("Operational flexibility phi")
    ax.set_ylabel("Value of information")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=3, frameon=False, borderaxespad=0)
    add_chart_header(
        fig,
        ax,
        "Information value rises only when flexibility permits reallocation",
        "Stress-calibrated signal experiment; values are generated from high/low corn-profit scenarios.",
    )
    save_figure(fig, output_base)
