#!/usr/bin/env python3
"""Render reconstruction output values as LaTeX macros."""

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
risk = pd.read_csv(OUT / "risk_induced_reversal.csv")
risk_sensitivity = pd.read_csv(OUT / "risk_shock_sensitivity.csv")
operation = pd.read_csv(OUT / "operational_mechanism.csv")
diversification_sensitivity = pd.read_csv(
    OUT / "diversification_sensitivity.csv"
)

primary = s["primary_model"]
score = s["calibration"]["scores"]
means = s["calibration"]["means"]
row_x0 = d.loc[d["policy"].eq("x0_expected_profit_under_matched_gaussian")].iloc[0]
row_mv = d.loc[d["policy"].eq("xMV_variance_target_selected")].iloc[0]
row_tail = d.loc[
    d["policy"].eq("xT_CVaR_under_student_t_evaluation")
].iloc[0]
u_pair = u.loc["selected_pairwise_reversal_frequency"]
risk_tight = risk.sort_values("risk_tolerance").iloc[0]
risk_loose = risk.sort_values("risk_tolerance").iloc[-1]
risk_focal = risk_sensitivity.loc[risk_sensitivity["focal_case"]].iloc[0]

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
    macro("PhaseReversal", s["frontier"]["selected_pairwise_reversal_cells"]),
    macro("PhaseComplete", s["frontier"]["selected_complete_rank_reversal_cells"]),
    macro("PhaseStrong", s["frontier"]["selected_strong_reversal_cells"]),
    macro("PhasePossible", s["frontier"]["possible_pairwise_reversal_cells"]),
    macro("PhaseUniversal", s["frontier"]["universal_pairwise_reversal_cells"]),
    macro("PhaseMultiple", s["frontier"]["multiple_optimum_cells"]),
    macro("BootstrapReversalCount", int(u_pair["event_count"])),
    macro("BootstrapProbability", f(s["bootstrap_selected_pairwise_reversal_frequency"])),
    macro("BootstrapProbabilityLow", f(u_pair["exact_binomial_95_low"])),
    macro("BootstrapProbabilityHigh", f(u_pair["exact_binomial_95_high"])),
    macro("BootstrapFirstMean", f(u.loc["first_reversal_risk_tolerance", "estimate_mean"])),
    macro("BootstrapFirstLow", f(u.loc["first_reversal_risk_tolerance", "percentile_95_low"])),
    macro("BootstrapFirstHigh", f(u.loc["first_reversal_risk_tolerance", "percentile_95_high"])),
    macro("DiversificationGaussianCVaR", f(row_mv["evaluation_loss_CVaR"], 1)),
    macro("DiversificationTailCVaR", f(row_tail["evaluation_loss_CVaR"], 1)),
    macro("DiversificationRiskCeiling", f(row_mv["risk_ceiling"], 1)),
    macro("DiversificationGamma", f(row_mv["gamma"], 4)),
    macro("DiversificationTarget", f(100 * row_mv["variance_reduction_target"], 0)),
    macro("DiversificationBenchmarkVariance", f(row_x0["gaussian_profit_variance"], 1)),
    macro("DiversificationMVVariance", f(row_mv["gaussian_profit_variance"], 1)),
    macro("DiversificationVarianceReduction", f(100 * row_mv["gaussian_variance_reduction_fraction"], 1)),
    macro("DiversificationAllocationLone", f(row_mv["xMV_vs_xT_allocation_L1"], 3)),
    macro("DiversificationTailGap", f(row_mv["xMV_evaluation_CVaR_minus_xT"], 3)),
    macro("DiversificationCeilingGap", f(row_mv["evaluation_loss_CVaR"] - row_mv["risk_ceiling"], 3)),
    macro("DiversificationWeakGammaInterval", row_mv["weak_failure_gamma_intervals"]),
    macro("DiversificationStrongGammaInterval", row_mv["strong_failure_gamma_intervals"]),
    macro("DiversificationFrontierPoints", int(row_mv["frontier_points"])),
    macro("DiversificationSensitivityCases", len(diversification_sensitivity)),
    macro("DiversificationSensitivityStrongCases", int(diversification_sensitivity["selected_strong_failure"].sum())),
    macro("LowerTailCoefficient", f(row_mv["lower_tail_dependence"])),
    macro("RiskShock", f(risk_tight["downside_shock_real_2024_usd_per_acre"], 1)),
    macro("RiskMeanGap", f(risk_tight["official_mean_margin_gap_high_minus_low"], 1)),
    macro("RiskTightSoy", f(risk_tight["allocation_high"])),
    macro("RiskTightCorn", f(risk_tight["allocation_low"])),
    macro("RiskLooseSoy", f(risk_loose["allocation_high"])),
    macro("RiskLooseCorn", f(risk_loose["allocation_low"])),
    macro("RiskShockCells", len(risk_sensitivity)),
    macro("RiskShockCrossingCells", int(risk_sensitivity["classification"].eq("crossing").sum())),
    macro("RiskShockNoCrossingCells", int(risk_sensitivity["classification"].eq("no_crossing").sum())),
    macro("RiskShockInfeasibleCells", int(risk_sensitivity["classification"].eq("infeasible").sum())),
    macro("RiskFocalFirstCrossing", f(risk_focal["first_crossing_risk_tolerance"], 3)),
    macro("OperationalCrossingCap", f(s["first_operational_crossing_cap"], 2)),
    macro("StateYears", int(e["state_years"].iloc[0])),
    macro("States", int(e["states"].iloc[0])),
    macro("RelativeYieldRate", f(e.loc[e.ranking_definition == "relative_yield", "top_rank_reversal_rate"].iloc[0])),
    macro("OperatingMarginRate", f(e.loc[e.ranking_definition == "operating_margin", "top_rank_reversal_rate"].iloc[0])),
    macro("RevenueRate", f(e.loc[e.ranking_definition == "standardized_revenue", "top_rank_reversal_rate"].iloc[0])),
    macro("TotalCostRate", f(e.loc[e.ranking_definition == "total_cost_margin", "top_rank_reversal_rate"].iloc[0])),
    macro("LaggedEffect", f(e.loc[e.evidence_layer == "leakage_free_2024", "lagged_score_leader_acreage_share_effect"].iloc[0], 4)),
    macro("LaggedLow", f(e.loc[e.evidence_layer == "leakage_free_2024", "lagged_effect_ci_low"].iloc[0], 4)),
    macro("LaggedHigh", f(e.loc[e.evidence_layer == "leakage_free_2024", "lagged_effect_ci_high"].iloc[0], 4)),
    macro("InfoPositiveCells", s["information_cross_difference_regions"].get("positive_cross_difference", 0)),
    macro("InfoNegativeCells", s["information_cross_difference_regions"].get("negative_cross_difference", 0)),
    macro("InfoZeroCells", s["information_cross_difference_regions"].get("zero_information", 0)),
    macro("InfoBoundaryCells", s["information_cross_difference_regions"].get("zero_or_boundary", 0)),
    macro("MaxInformationValue", f(i["value_of_information"].max())),
]
DEST.write_text("\n".join(rows) + "\n")
print(DEST)
