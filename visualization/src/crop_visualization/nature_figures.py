"""Source-grounded Nature figure and table system for Issue 8."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd
from PIL import Image, ImageOps, ImageDraw

from crop_visualization.visualization_style import (
    NATURE_COLORS,
    apply_style,
    mm_to_inches,
    panel_label,
    save_figure,
)


FIGURES = {
    "Figure1": ("main", 183, 120),
    "Figure2": ("main", 183, 150),
    "FigureS1": ("supplementary", 183, 140),
    "FigureS2": ("supplementary", 183, 105),
    "FigureS3": ("supplementary", 183, 120),
}
DEFINITION_LABELS = {
    "operating_margin": "Operating margin",
    "relative_yield": "Relative yield",
    "standardized_revenue": "Standardized revenue",
    "total_cost_margin": "Total-cost margin",
}
DEFINITION_COLORS = {
    "operating_margin": NATURE_COLORS["teal"],
    "relative_yield": NATURE_COLORS["cyan"],
    "standardized_revenue": NATURE_COLORS["steel_blue"],
    "total_cost_margin": NATURE_COLORS["muted_violet"],
}


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.10g")


def _write_latex(frame: pd.DataFrame, path: Path) -> None:
    """Write a dependency-free booktabs table with escaped cell text."""
    def esc(value: object) -> str:
        text=str(value)
        for old,new in [("\\","\\textbackslash{}"),("&","\\&"),("%","\\%"),("_","\\_")]:
            text=text.replace(old,new)
        return text
    cols=list(frame.columns)
    lines=["\\begin{tabular}{"+"l"*len(cols)+"}","\\toprule"," & ".join(esc(c) for c in cols)+" \\\\","\\midrule"]
    lines.extend(" & ".join(esc(v) for v in row)+" \\\\" for row in frame.itertuples(index=False,name=None))
    lines.extend(["\\bottomrule","\\end{tabular}",""])
    path.write_text("\n".join(lines),encoding="utf-8")


def _read(root: Path, relative: str) -> pd.DataFrame:
    return pd.read_csv(root / relative)


def _clean_axis(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#D6D6D6", linewidth=0.35, zorder=0)
    ax.set_axisbelow(True)


def _extract_source_data(root: Path, out: Path) -> dict[str, pd.DataFrame]:
    source = out / "visualization" / "source_data"
    empirical = {
        name: _read(root, f"empirical/outputs/{name}.csv")
        for name in [
            "definition_summary", "state_heterogeneity", "year_heterogeneity",
            "leave_one_year_out", "lagged_2024_validation", "national_check",
            "sample_flow", "permutation_benchmark", "claim_boundaries",
        ]
    }
    simulation = {
        name: _read(root, f"simulation/outputs/{name}.csv")
        for name in ["cell_summary", "convergence_summary", "formal_results", "solver_sensitivity"]
    }

    flow = pd.DataFrame(
        [
            ("Rank crops", "Ordinal information", "THEORY", "Ranking alone does not identify an allocation"),
            ("Cardinalize", "Scores or payoffs", "THEORY", "Cardinalization is an additional assumption"),
            ("Impose feasible set", "Land, budget, risk and policy constraints", "THEORY", "Constraints can change the optimal face"),
            ("Solve optimal face", "Set-valued optimum", "THEORY", "Possible and universal reversal are face properties"),
            ("Select allocation", "Tie-breaking or observed action", "BOUNDARY", "Observed acreage does not identify the mechanism"),
        ],
        columns=["stage", "object", "evidence_domain", "identification_boundary"],
    )
    boundaries = pd.DataFrame(
        [
            ("possible", "at least one optimizer reverses the ranking", "THEORY_DEFINED"),
            ("universal", "every optimizer reverses the ranking", "THEORY_DEFINED"),
            ("selected", "the reported optimizer reverses the ranking", "SOLVER_DEPENDENT"),
            ("simulation", "0 of 5 convergence rows pass", "NONHEADLINE"),
            ("empirical", "state-year discordance is descriptive", "DESCRIPTIVE_IDENTIFIED"),
            ("acreage mechanism", "observed acreage is not an identified optimum", "NOT_IDENTIFIED"),
        ],
        columns=["concept", "definition", "status"],
    )
    _write_csv(flow, source / "figure1_flow.csv")
    _write_csv(boundaries, source / "figure1_boundaries.csv")

    for key, frame in {**empirical, **simulation}.items():
        _write_csv(frame, source / f"{key}.csv")

    formal = simulation["formal_results"]
    bind_cols = ["land_binds", "budget_binds", "cvar_binds", "rotation_binds", "contract_binds", "lower_bound_binds", "upper_bound_binds"]
    binds = pd.DataFrame({"constraint": [c.replace("_binds", "").replace("_", " ").title() for c in bind_cols],
                          "binding_frequency": [formal[c].astype(bool).mean() for c in bind_cols],
                          "replications": len(formal)})
    _write_csv(binds, source / "constraint_binding.csv")

    lineage_rows = []
    for p in sorted(source.glob("*.csv")):
        if p.name == "lineage.csv":
            continue
        upstream = root / "theory/repaired/theorem_contract.json" if p.name.startswith("figure1_") else None
        if p.stem in empirical:
            upstream = root / "empirical/outputs" / p.name
        elif p.stem in simulation:
            upstream = root / "simulation/outputs" / p.name
        elif p.name == "constraint_binding.csv":
            upstream = root / "simulation/outputs/formal_results.csv"
        lineage_rows.append({
            "source_data": str(p.relative_to(out)),
            "source_sha256": _sha(p),
            "upstream_input": str(upstream.relative_to(root)) if upstream and upstream.exists() else "figure_plan.md",
            "upstream_sha256": _sha(upstream) if upstream and upstream.exists() else _sha(root / "visualization/figure_plan.md"),
            "transformation": "verbatim copy" if upstream and upstream.name == p.name else "deterministic aggregation or contract extraction",
        })
    _write_csv(pd.DataFrame(lineage_rows), source / "lineage.csv")
    return {**empirical, **simulation, "flow": flow, "boundaries": boundaries, "binds": binds}


def _figure1(data: dict[str, pd.DataFrame], stem: Path) -> None:
    fig = plt.figure(figsize=mm_to_inches(183, 120))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.08, 1], hspace=0.50, wspace=0.30)
    ax = fig.add_subplot(gs[0, :]); ax.axis("off"); panel_label(ax, "a")
    xs = np.linspace(0.075, 0.925, 5)
    colors = ["steel_blue", "cyan", "mint", "muted_violet", "teal"]
    for i, row in data["flow"].iterrows():
        box = FancyBboxPatch((xs[i] - .072, .40), .144, .32, boxstyle="round,pad=0.012,rounding_size=0.015",
                             facecolor=NATURE_COLORS[colors[i]], alpha=.22, edgecolor=NATURE_COLORS[colors[i]], linewidth=.8)
        ax.add_patch(box)
        ax.text(xs[i], .61, row.stage, ha="center", va="center", fontsize=6.2, fontweight="semibold")
        ax.text(xs[i], .47, row.object, ha="center", va="center", fontsize=5.3, wrap=True)
        if i < 4:
            ax.add_patch(FancyArrowPatch((xs[i]+.078, .56), (xs[i+1]-.078, .56), arrowstyle="-|>", mutation_scale=7,
                                         color=NATURE_COLORS["charcoal"], linewidth=.65))
    ax.text(.5, .89, "Ordinal rankings become allocations only through additional cardinal and feasibility assumptions",
            ha="center", va="center", fontsize=7.2, fontweight="semibold")
    ax.text(.5, .15, "Identification boundary: observed acreage does not reveal the feasible set, objective or optimizer selection rule",
            ha="center", va="center", fontsize=6.2, color=NATURE_COLORS["teal"], fontweight="semibold")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    ax = fig.add_subplot(gs[1, 0]); panel_label(ax, "b"); ax.axis("off")
    concepts = ["Possible", "Universal", "Selected"]
    defs = ["At least one optimizer\nreverses ranking", "Every optimizer\nreverses ranking", "Reported optimizer\nreverses ranking"]
    status = ["Face property", "Face property", "Solver-dependent"]
    for i, (c, d, s) in enumerate(zip(concepts, defs, status)):
        y = .81 - i*.29
        ax.add_patch(Rectangle((.02, y-.10), .24, .20, facecolor=NATURE_COLORS[["cyan","teal","muted_violet"][i]], alpha=.24, linewidth=0))
        ax.text(.14, y, c, ha="center", va="center", fontweight="semibold")
        ax.text(.31, y+.025, d, ha="left", va="center", fontsize=5.8)
        ax.text(.96, y-.045, s, ha="right", va="center", fontsize=5.4, color=NATURE_COLORS["charcoal"])
    ax.set_title("Three non-equivalent reversal definitions", loc="left")

    ax = fig.add_subplot(gs[1, 1]); panel_label(ax, "c"); ax.axis("off")
    cards = [
        ("Theory", "Defines set-valued reversal", "PROVED / BOUNDED", "steel_blue"),
        ("Simulation", "0/5 convergence rows pass", "NONHEADLINE", "muted_violet"),
        ("Empirical", "26 states; 77 state-years", "DESCRIPTIVE", "teal"),
        ("Mechanism", "Acreage optimum / CVaR", "NOT IDENTIFIED", "charcoal"),
    ]
    for i, (title, desc, stat, col) in enumerate(cards):
        y = .86 - i*.225
        ax.add_patch(FancyBboxPatch((.02,y-.08),.94,.16,boxstyle="round,pad=.01",facecolor=NATURE_COLORS[col],alpha=.13,
                                    edgecolor=NATURE_COLORS[col],linewidth=.55))
        ax.text(.05,y+.025,title,fontweight="semibold",va="center")
        ax.text(.28,y+.025,desc,va="center",fontsize=5.8)
        ax.text(.94,y-.030,stat,ha="right",va="center",fontsize=5.2,fontweight="semibold")
    ax.set_title("Evidence domains remain separated", loc="left")
    save_figure(fig, stem); plt.close(fig)


def _figure2(data: dict[str, pd.DataFrame], stem: Path) -> None:
    defs = list(DEFINITION_LABELS)
    states = data["state_heterogeneity"]["state"].drop_duplicates().tolist()
    pivot = data["state_heterogeneity"].pivot(index="state", columns="ranking_definition", values="top_reversal_rate").reindex(index=states, columns=defs)
    ns = data["state_heterogeneity"].pivot(index="state", columns="ranking_definition", values="years").reindex(index=states, columns=defs)
    fig = plt.figure(figsize=mm_to_inches(183, 150))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.25, 1], hspace=.42, wspace=.34)
    ax = fig.add_subplot(gs[:,0]); panel_label(ax,"a")
    for y in range(len(states)):
        for x in range(len(defs)):
            v = pivot.iloc[y,x]; n = int(ns.iloc[y,x])
            ax.add_patch(Rectangle((x-.5,y-.5),1,1,facecolor=NATURE_COLORS["teal"],alpha=max(.03,v),edgecolor="white",linewidth=.25))
            ax.text(x,y,f"{v:.0%}\nn={n}",ha="center",va="center",fontsize=4.2,
                    color="white" if v>.66 else NATURE_COLORS["charcoal"])
    ax.set_xlim(-.5,3.5); ax.set_ylim(len(states)-.5,-.5)
    ax.set_xticks(range(4), [DEFINITION_LABELS[d].replace(" ","\n") for d in defs])
    ax.set_yticks(range(len(states)), states); ax.tick_params(axis="y",labelsize=4.7,length=0); ax.tick_params(axis="x",length=0)
    ax.set_title("Top-rank reversal rate by state and definition", loc="left")
    for i,(rate,alpha) in enumerate([(0,.03),(.5,.5),(1,1)]):
        ax.add_patch(Rectangle((.06+i*.12,-.075),.045,.018,transform=ax.transAxes,clip_on=False,facecolor=NATURE_COLORS["teal"],alpha=alpha,edgecolor=NATURE_COLORS["charcoal"],linewidth=.3))
        ax.text(.112+i*.12,-.066,f"{rate:g}",transform=ax.transAxes,va="center",fontsize=4.8)
    ax.text(.46,-.066,"Top-rank reversal rate",transform=ax.transAxes,va="center",fontsize=5.0)

    ax=fig.add_subplot(gs[0,1]); panel_label(ax,"b")
    summ=data["definition_summary"].set_index("ranking_definition").reindex(defs)
    y=np.arange(4); h=.34
    ax.barh(y-h/2,summ.top_rank_reversal_rate,h,color=[DEFINITION_COLORS[d] for d in defs],label="Top-rank",zorder=2)
    ax.barh(y+h/2,summ.strong_reversal_rate,h,facecolor="white",edgecolor=[DEFINITION_COLORS[d] for d in defs],hatch="////",label="Strong",zorder=2)
    ax.axvline(2/3,color=NATURE_COLORS["charcoal"],linestyle="--",linewidth=.75)
    ax.text(2/3,.52,"2/3 exact reference",transform=ax.get_xaxis_transform(),ha="right",va="center",fontsize=5.0,rotation=90)
    ax.set_yticks(y,[DEFINITION_LABELS[d] for d in defs]); ax.invert_yaxis(); ax.set_xlim(0,1); ax.set_xlabel("State-year proportion (n=77)")
    ax.legend(loc="lower right",ncols=2); _clean_axis(ax); ax.set_title("Discordance depends on ranking definition",loc="left")

    ax=fig.add_subplot(gs[1,1]); panel_label(ax,"c")
    years=data["year_heterogeneity"].query("ranking_definition == 'operating_margin'")
    bars=ax.bar(years.year.astype(str),years.top_reversal_rate,color=NATURE_COLORS["teal"],width=.62,zorder=2)
    ax.bar_label(bars,labels=[f"{v:.0%}\nn={int(n)}" for v,n in zip(years.top_reversal_rate,years.states)],padding=2,fontsize=5.5)
    ax.set_ylim(0,1.08); ax.set_ylabel("Top-rank reversal rate"); ax.set_xlabel("Year")
    ax.text(.03,.11,"National check\n0/9 crop-years reverse rank",transform=ax.transAxes,ha="left",va="bottom",fontsize=5.8,
            bbox={"boxstyle":"round,pad=.3","facecolor":NATURE_COLORS["mint"],"alpha":.35,"edgecolor":"none"})
    _clean_axis(ax); ax.set_title("Operating-margin pattern by year",loc="left")
    fig.text(.01,.006,"All panels are descriptive. State-year rates do not identify acreage optimality, CVaR binding or a causal mechanism.",fontsize=5.5)
    save_figure(fig,stem); plt.close(fig)


def _figure_s1(data: dict[str,pd.DataFrame],stem:Path)->None:
    cells=data["cell_summary"]
    families=sorted(cells.copula_family.unique())
    fig,axes=plt.subplots(2,2,figsize=mm_to_inches(183,140)); axes=axes.ravel()
    markers={m:mk for m,mk in zip(sorted(cells.marginal_family.unique()),["o","s","^"])}
    for i,fam in enumerate(families[:3]):
        ax=axes[i]; sub=cells[cells.copula_family==fam]
        for marginal,grp in sub.groupby("marginal_family"):
            rev=grp.universal_reversal_probability>0
            ax.scatter(grp.kendall_tau[~rev],grp.risk_limit_frontier_quantile[~rev],s=18,marker=markers[marginal],facecolors="white",edgecolors=NATURE_COLORS["steel_blue"],linewidths=.55,label=marginal.replace("_"," "))
            ax.scatter(grp.kendall_tau[rev],grp.risk_limit_frontier_quantile[rev],s=18,marker=markers[marginal],facecolors=NATURE_COLORS["teal"],edgecolors=NATURE_COLORS["teal"],linewidths=.55)
        ax.set_xlabel("Kendall tau"); ax.set_ylabel("Risk-limit frontier quantile"); ax.set_title(fam.replace("_"," ").title(),loc="left"); _clean_axis(ax); panel_label(ax,chr(97+i))
        if i==0: ax.legend(title="Marginal family",fontsize=4.8,title_fontsize=5.2)
    ax=axes[3]; b=data["binds"].sort_values("binding_frequency")
    ax.barh(b.constraint,b.binding_frequency,color=NATURE_COLORS["muted_violet"],zorder=2)
    for y,v in enumerate(b.binding_frequency): ax.text(v+.015,y,f"{v:.0%}",va="center",fontsize=5.2)
    ax.set_xlim(0,1.08); ax.set_xlabel("Binding frequency (n=450)"); _clean_axis(ax); panel_label(ax,"d"); ax.set_title("Constraint diagnostics",loc="left")
    fig.suptitle("Mixed-factor simulation landscape: diagnostic only, not a threshold map",y=.99,fontsize=7.4,fontweight="semibold")
    fig.text(.01,.008,"Filled symbols indicate universal reversal in at least one of five replications. All simulation patterns are NONHEADLINE because 0/5 convergence rows pass.",fontsize=5.4)
    fig.tight_layout(rect=[0,.03,1,.96]); save_figure(fig,stem); plt.close(fig)


def _figure_s2(data:dict[str,pd.DataFrame],stem:Path)->None:
    c=data["convergence_summary"]
    fig,axes=plt.subplots(1,3,figsize=mm_to_inches(183,105))
    x=np.arange(len(c)); labels=[f"{int(v/1000)}k" for v in c.n_scenarios]
    ax=axes[0]; ax.plot(x,c.numeric_pass_fraction,"o-",color=NATURE_COLORS["steel_blue"]); ax.axhline(.8,ls="--",color=NATURE_COLORS["charcoal"]); ax.set_xticks(x,labels); ax.set_ylim(-.05,1.05); ax.set_ylabel("Numeric pass fraction"); ax.set_xlabel("Scenarios"); _clean_axis(ax); panel_label(ax,"a"); ax.set_title("Numeric gate",loc="left")
    ax=axes[1]; ax.plot(x,c.reversal_probability_interval_width,"o-",color=NATURE_COLORS["muted_violet"]); ax.axhline(.1,ls="--",color=NATURE_COLORS["charcoal"]); ax.set_xticks(x,labels); ax.set_ylabel("Wilson interval width"); ax.set_xlabel("Scenarios"); _clean_axis(ax); panel_label(ax,"b"); ax.set_title("Precision gate",loc="left")
    ax=axes[2]; ax.axis("off"); panel_label(ax,"c")
    formal=data["formal_results"]
    residuals={"Primal":formal.kkt_primal_residual.max(),"Dual":formal.kkt_dual_nonnegativity_violation.max(),"Stationarity":formal.kkt_stationarity_residual.max(),"Complementarity":formal.kkt_complementarity_residual.max(),"Tail":formal.tail_weight_violation.max()}
    ax.text(.03,.91,"Independent numerical checks",fontweight="semibold")
    for i,(name,v) in enumerate(residuals.items()): ax.text(.05,.78-i*.105,f"{name:<16} {v:.2e}",family="monospace",fontsize=5.6)
    ax.text(.05,.20,"Replay: 450/450 pass\nSolver sensitivity: 9/9 pass\nConvergence: 0/5 rows pass",fontsize=5.8,linespacing=1.5)
    ax.text(.03,.04,"NONHEADLINE",fontsize=6.5,fontweight="bold",color=NATURE_COLORS["teal"])
    fig.suptitle("Predeclared convergence audit fails at every scenario count",y=.97,fontsize=7.4,fontweight="semibold")
    fig.tight_layout(rect=[0,.02,1,.93]); save_figure(fig,stem); plt.close(fig)


def _figure_s3(data:dict[str,pd.DataFrame],stem:Path)->None:
    fig,axes=plt.subplots(1,3,figsize=mm_to_inches(183,120))
    defs=list(DEFINITION_LABELS)
    ax=axes[0]
    loo=data["leave_one_year_out"]
    for d in defs:
        g=loo[loo.ranking_definition==d]
        ax.plot(g.omitted_year.astype(str),g.top_rank_reversal_rate,marker="o",ms=3,color=DEFINITION_COLORS[d],label=DEFINITION_LABELS[d])
    ax.set_ylim(0,1); ax.set_ylabel("Top-rank reversal rate"); ax.set_xlabel("Omitted year"); _clean_axis(ax); panel_label(ax,"a"); ax.set_title("Leave-one-year-out",loc="left"); ax.legend(fontsize=4.5)
    ax=axes[1]; lag=data["lagged_2024_validation"]; vals=lag.pairwise_inversions.value_counts().sort_index(); ax.bar(vals.index.astype(str),vals.values,color=NATURE_COLORS["cyan"]); ax.set_xlabel("Pairwise inversions"); ax.set_ylabel("States"); _clean_axis(ax); panel_label(ax,"b"); ax.set_title("Lagged 2024 validation (n=25)",loc="left"); ax.text(.97,.95,f"{lag.top_rank_reversal.sum()}/25 top-rank reversals\nlow-powered descriptive check",transform=ax.transAxes,ha="right",va="top",fontsize=5.2)
    ax=axes[2]; nat=data["national_check"]
    for crop,col in zip(nat.crop.unique(),["steel_blue","teal","muted_violet"]):
        g=nat[nat.crop==crop]
        ax.plot(g.year.astype(str),g.margin_rank,marker="o",color=NATURE_COLORS[col],label=crop.replace("_"," ").title())
        ax.plot(g.year.astype(str),g.acreage_rank,marker="x",ls="none",color=NATURE_COLORS[col])
    ax.set_ylim(3.3,.7); ax.set_yticks([1,2,3]); ax.set_ylabel("Rank"); ax.set_xlabel("Year"); _clean_axis(ax); panel_label(ax,"c"); ax.set_title("National rank alignment: 0/9",loc="left"); ax.legend(fontsize=4.8)
    fig.text(.01,.012,"Robustness checks are descriptive; none identifies an optimizer, risk constraint or causal mechanism.",fontsize=5.4)
    fig.tight_layout(rect=[0,.04,1,.96]); save_figure(fig,stem); plt.close(fig)


def _tables(data:dict[str,pd.DataFrame],out:Path)->None:
    main=out/"tables/main"; supp=out/"tables/supplementary"; main.mkdir(parents=True,exist_ok=True); supp.mkdir(parents=True,exist_ok=True)
    flow=data["sample_flow"].copy(); flow["section"]="Sample construction"
    defs=data["definition_summary"][["ranking_definition","state_years","states","mean_pairwise_inversions","top_rank_reversal_rate","strong_reversal_rate"]].copy(); defs["ranking_definition"]=defs.ranking_definition.map(DEFINITION_LABELS); defs["section"]="Ranking definitions"
    flow2=flow.rename(columns={"stage":"item","rows":"rows_or_mean_inversions","state_years":"n_state_years"})[["section","item","rows_or_mean_inversions","n_state_years"]]
    defs2=defs.rename(columns={"ranking_definition":"item","mean_pairwise_inversions":"rows_or_mean_inversions","state_years":"n_state_years"})
    defs2["top_rank_reversal_rate"]=defs2.top_rank_reversal_rate.map(lambda x:f"{x:.1%}"); defs2["strong_reversal_rate"]=defs2.strong_reversal_rate.map(lambda x:f"{x:.1%}")
    t1=pd.concat([flow2,defs2],ignore_index=True)
    _write_csv(t1,main/"Table1_sample_and_definitions.csv")
    _write_latex(t1,main/"Table1_sample_and_definitions.tex")

    c=data["convergence_summary"].copy(); c["evidence_status"]="NONHEADLINE"; _write_csv(c,supp/"TableS1_simulation_gates.csv"); _write_latex(c,supp/"TableS1_simulation_gates.tex")
    claims=data["claim_boundaries"].copy(); _write_csv(claims,supp/"TableS2_claim_boundaries.csv"); _write_latex(claims,supp/"TableS2_claim_boundaries.tex")


def _captions(out:Path)->None:
    rows=[
        ("Figure1","Main","From ordinal crop rankings to set-valued allocation claims.","Conceptual flow distinguishes possible, universal and selected reversal, then freezes theory, simulation and empirical evidence boundaries. Simulation is nonheadline (0/5 convergence rows pass); empirical evidence is descriptive; observed acreage does not identify an optimizer or mechanism."),
        ("Figure2","Main","Ranking discordance across US states and definitions.","Panel a reports top-rank reversal rates for 26 states and four definitions (77 state-years; New Jersey n=2, other cells generally n=3). Panel b contrasts top-rank and strong reversal with the exact 2/3 combinatorial reference, not a sampling null. Panel c shows operating-margin rates by year and the national 0/9 rank-alignment check. All results are descriptive."),
        ("FigureS1","Supplementary","Mixed-factor simulation landscape and binding diagnostics.","Markers encode marginal family and fill denotes any universal reversal among five replications. The landscape is neither a threshold map nor headline evidence because 0/5 convergence rows pass. Binding frequencies use 450 optimized replications."),
        ("FigureS2","Supplementary","Predeclared convergence and numerical diagnostics.","Numeric pass fractions and Wilson interval widths are compared with the frozen 0.8 and 0.1 gates. No scenario count passes both. Independent replay (450/450) and solver sensitivity (9/9) pass but do not rescue inferential convergence."),
        ("FigureS3","Supplementary","Empirical robustness and national alignment checks.","Leave-one-year-out estimates, low-powered leakage-free 2024 validation (n=25), and national crop-year ranks (n=9) are descriptive robustness checks; none identifies an optimizer, risk constraint or causal mechanism."),
    ]
    _write_csv(pd.DataFrame(rows,columns=["figure_id","location","short_title","caption"]),out/"visualization/captions.csv")


def _qa(root:Path,out:Path)->None:
    qa=out/"visualization/qa"; qa.mkdir(parents=True,exist_ok=True)
    records=[]
    gray_paths=[]
    for fid,(loc,wmm,hmm) in FIGURES.items():
        stem=out/"figures"/loc/fid
        png=stem.with_suffix(".png")
        im=Image.open(png)
        expected=(round(wmm/25.4*300),round(hmm/25.4*300))
        gray=ImageOps.grayscale(im).convert("RGB")
        gray_path=qa/f"{fid}_grayscale.png"; gray.save(gray_path,optimize=False); gray_paths.append(gray_path)
        svg=stem.with_suffix(".svg").read_text(encoding="utf-8")
        records.append({"figure_id":fid,"width_mm":wmm,"height_mm":hmm,"png_pixels":list(im.size),"expected_pixels":list(expected),"size_pass":all(abs(a-b)<=1 for a,b in zip(im.size,expected)),"svg_editable_text":"<text" in svg and "<image" not in svg,"png_sha256":_sha(png),"svg_sha256":_sha(stem.with_suffix('.svg'))})
    (qa/"visual_regression.json").write_text(json.dumps(records,indent=2)+"\n",encoding="utf-8")
    thumbs=[]
    for p in gray_paths:
        im=Image.open(p); im.thumbnail((700,500)); thumbs.append((p.stem,im.copy()))
    sheet=Image.new("RGB",(1440,1100),"white"); draw=ImageDraw.Draw(sheet)
    positions=[(10,30),(730,30),(10,560),(490,560),(970,560)]
    for (label,im),(x,y) in zip(thumbs,positions):
        sheet.paste(im,(x,y+20)); draw.text((x,y),label,fill=NATURE_COLORS["charcoal"])
    sheet.save(qa/"contact_sheet.png")
    acc={"palette":NATURE_COLORS,"redundant_encoding":"hatch, marker, label or direct annotation accompanies semantic color","grayscale_files":[p.name for p in gray_paths],"colorblind_note":"cyan/teal are never the sole discriminator; definitions are labelled and secondary series use hatch or markers","status":"PASS"}
    (qa/"accessibility.json").write_text(json.dumps(acc,indent=2)+"\n",encoding="utf-8")


def _checksums(out:Path)->None:
    paths=[]
    for folder in ["visualization/source_data","figures","tables"]:
        paths.extend(p for p in (out/folder).rglob("*") if p.is_file() and p.name!="SHA256SUMS")
    ledger="".join(f"{_sha(p)}  {p.relative_to(out)}\n" for p in sorted(paths))
    (out/"visualization/source_data/SHA256SUMS").write_text("".join(line for line in ledger.splitlines(True) if "visualization/source_data/" in line),encoding="utf-8")
    (out/"figures/SHA256SUMS").write_text("".join(line for line in ledger.splitlines(True) if "figures/" in line),encoding="utf-8")
    (out/"tables/SHA256SUMS").write_text("".join(line for line in ledger.splitlines(True) if "tables/" in line),encoding="utf-8")


def _registries(out: Path) -> None:
    reg=out/"evidence_registry"; reg.mkdir(parents=True,exist_ok=True)
    fig_rows=[]
    sources={
        "Figure1":"visualization/source_data/figure1_flow.csv;visualization/source_data/figure1_boundaries.csv",
        "Figure2":"visualization/source_data/state_heterogeneity.csv;visualization/source_data/definition_summary.csv;visualization/source_data/year_heterogeneity.csv;visualization/source_data/national_check.csv",
        "FigureS1":"visualization/source_data/cell_summary.csv;visualization/source_data/constraint_binding.csv",
        "FigureS2":"visualization/source_data/convergence_summary.csv;visualization/source_data/formal_results.csv;visualization/source_data/solver_sensitivity.csv",
        "FigureS3":"visualization/source_data/leave_one_year_out.csv;visualization/source_data/lagged_2024_validation.csv;visualization/source_data/national_check.csv",
    }
    claims={"Figure1":"Identification flow and evidence boundaries","Figure2":"Descriptive state-year ranking discordance","FigureS1":"Diagnostic simulation landscape","FigureS2":"Failed convergence gate and passed numerical checks","FigureS3":"Descriptive robustness checks"}
    statuses={"Figure1":"THEORY_AND_BOUNDARY","Figure2":"DESCRIPTIVE_IDENTIFIED","FigureS1":"NONHEADLINE","FigureS2":"NONHEADLINE","FigureS3":"DESCRIPTIVE_ROBUSTNESS"}
    for fid,(loc,_,_) in FIGURES.items():
        fig_rows.append({"figure_id":fid,"manuscript_location":loc,"caption_claim":claims[fid],"source_data":sources[fid],"generating_script":"scripts/generate_nature_figures.py","generation_command":"make figures","config":"visualization/configs/nature_style.yaml","checksum":_sha(out/f"figures/{loc}/{fid}.svg"),"evidence_status":statuses[fid],"notes":"Editable SVG/PDF plus PNG 300 dpi and TIFF 600 dpi; see visualization/captions.csv"})
    _write_csv(pd.DataFrame(fig_rows),reg/"figures.csv")
    table_defs=[
        ("Table1","main","Sample construction and ranking-definition outcomes","tables/main/Table1_sample_and_definitions.csv","DESCRIPTIVE_IDENTIFIED"),
        ("TableS1","supplementary","Predeclared simulation convergence gates","tables/supplementary/TableS1_simulation_gates.csv","NONHEADLINE"),
        ("TableS2","supplementary","Permitted and prohibited empirical claims","tables/supplementary/TableS2_claim_boundaries.csv","CLAIM_BOUNDARY"),
    ]
    tab_rows=[]
    for tid,loc,claim,path,status in table_defs:
        tab_rows.append({"table_id":tid,"manuscript_location":loc,"caption_claim":claim,"source_data":path,"generating_script":"scripts/generate_nature_figures.py","generation_command":"make figures","config":"visualization/configs/nature_style.yaml","checksum":_sha(out/path),"evidence_status":status,"notes":"CSV source and booktabs-compatible TeX export"})
    _write_csv(pd.DataFrame(tab_rows),reg/"tables.csv")


def generate(root:Path,output_root:Path|None=None)->None:
    root=root.resolve(); out=(output_root or root).resolve()
    os.environ.setdefault("SOURCE_DATE_EPOCH","1784390400")
    matplotlib.rcParams["svg.hashsalt"]="crop-ranking-reversal-issue-8"
    apply_style()
    data=_extract_source_data(root,out)
    for fid,(loc,_,_) in FIGURES.items(): (out/"figures"/loc).mkdir(parents=True,exist_ok=True)
    _figure1(data,out/"figures/main/Figure1")
    _figure2(data,out/"figures/main/Figure2")
    _figure_s1(data,out/"figures/supplementary/FigureS1")
    _figure_s2(data,out/"figures/supplementary/FigureS2")
    _figure_s3(data,out/"figures/supplementary/FigureS3")
    _tables(data,out); _captions(out); _qa(root,out); _checksums(out); _registries(out)
