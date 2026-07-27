#!/usr/bin/env python3
"""Render registered Issue #34 output values as LaTeX macros."""

from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reconstruction" / "issue34" / "outputs"
DEST = ROOT / "manuscript" / "issue34" / "generated" / "numbers.tex"
DEST.parent.mkdir(parents=True, exist_ok=True)

s = json.loads((OUT / "summary.json").read_text())
p = pd.read_csv(OUT / "policy_comparison.csv")
e = pd.read_csv(OUT / "external_descriptive_evidence.csv")
u = pd.read_csv(OUT / "uncertainty_summary.csv").set_index("metric")
d = pd.read_csv(OUT / "diversification_failure.csv").drop_duplicates("policy")
i = pd.read_csv(OUT / "information_flexibility.csv")

primary = s["primary_model"]
score = s["calibration"]["scores"]
means = s["calibration"]["means"]
row_mv = d.iloc[0]
row_tail = d.iloc[-1]

def macro(name, value):
    return f"\\newcommand{{\\{name}}}{{{value}}}"

def f(x, n=3):
    return f"{float(x):.{n}f}"

rows = [
    macro("DesignHash", s["design_sha256"][:12]),
    macro("KansasYears", s["calibration"]["raw_effective_years"]),
    macro("ScoreCorn", f(score["Corn"])),
    macro("ScoreSoy", f(score["Soybean"])),
    macro("ScoreWheat", f(score["Winter Wheat"])),
    macro("MarginCorn", f(means["Corn"], 1)),
    macro("MarginSoy", f(means["Soybean"], 1)),
    macro("MarginWheat", f(means["Winter Wheat"], 1)),
    macro("PrimaryCorn", f(primary["allocation"]["Corn"])),
    macro("PrimarySoy", f(primary["allocation"]["Soybean"])),
    macro("PrimaryWheat", f(primary["allocation"]["Winter Wheat"])),
    macro("PrimaryProfit", f(primary["expected_profit"], 1)),
    macro("PrimaryCVaR", f(primary["cvar_loss"], 1)),
    macro("PrimaryMinCVaR", f(primary["minimum_cvar"], 1)),
    macro("PrimaryNoRiskCVaR", f(primary["expected_profit_endpoint_cvar"], 1)),
    macro("KKTPrimal", f"{primary['kkt_primal_residual']:.2e}"),
    macro("KKTStationarity", f"{primary['kkt_stationarity_residual']:.2e}"),
    macro("KKTComplementarity", f"{primary['kkt_complementarity_residual']:.2e}"),
    macro("PhaseCells", s["frontier"]["cells"]),
    macro("PhaseReversal", s["frontier"]["reversal_cells"]),
    macro("PhaseStrong", s["frontier"]["strong_reversal_cells"]),
    macro("PhaseMultiple", s["frontier"]["multiple_optimum_cells"]),
    macro("BootstrapProbability", f(s["bootstrap_reversal_probability"])),
    macro("BootstrapProbabilityLow", f(u.loc["selected_reversal_probability", "percentile_95_low"])),
    macro("BootstrapProbabilityHigh", f(u.loc["selected_reversal_probability", "percentile_95_high"])),
    macro("BootstrapFirstMean", f(u.loc["first_reversal_risk_tolerance", "estimate_mean"])),
    macro("BootstrapFirstLow", f(u.loc["first_reversal_risk_tolerance", "percentile_95_low"])),
    macro("BootstrapFirstHigh", f(u.loc["first_reversal_risk_tolerance", "percentile_95_high"])),
    macro("DiversificationGaussianCVaR", f(row_mv["true_law_loss_CVaR"], 1)),
    macro("DiversificationTailCVaR", f(row_tail["true_law_loss_CVaR"], 1)),
    macro("DiversificationRiskCeiling", f(row_mv["risk_ceiling"], 1)),
    macro("LowerTailCoefficient", f(row_mv["lower_tail_dependence"])),
    macro("StateYears", int(e["state_years"].iloc[0])),
    macro("States", int(e["states"].iloc[0])),
    macro("RelativeYieldRate", f(e.loc[e.ranking_definition == "relative_yield", "top_rank_reversal_rate"].iloc[0])),
    macro("OperatingMarginRate", f(e.loc[e.ranking_definition == "operating_margin", "top_rank_reversal_rate"].iloc[0])),
    macro("RevenueRate", f(e.loc[e.ranking_definition == "standardized_revenue", "top_rank_reversal_rate"].iloc[0])),
    macro("TotalCostRate", f(e.loc[e.ranking_definition == "total_cost_margin", "top_rank_reversal_rate"].iloc[0])),
    macro("LaggedEffect", f(e.loc[e.evidence_layer == "leakage_free_2024", "lagged_score_leader_acreage_share_effect"].iloc[0], 4)),
    macro("LaggedLow", f(e.loc[e.evidence_layer == "leakage_free_2024", "lagged_effect_ci_low"].iloc[0], 4)),
    macro("LaggedHigh", f(e.loc[e.evidence_layer == "leakage_free_2024", "lagged_effect_ci_high"].iloc[0], 4)),
    macro("InfoStrictCells", s["information_regions"]["strict_complementarity"]),
    macro("InfoSubCells", s["information_regions"]["substitution"]),
    macro("InfoZeroCells", s["information_regions"]["zero_interaction"]),
    macro("InfoBoundaryCells", s["information_regions"]["weak_or_boundary"]),
    macro("MaxInformationValue", f(i["value_of_information"].max())),
]
DEST.write_text("\n".join(rows) + "\n")
print(DEST)
