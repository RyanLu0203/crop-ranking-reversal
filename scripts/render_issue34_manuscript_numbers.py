#!/usr/bin/env python3
"""Render reconstruction output values as LaTeX macros."""

from pathlib import Path
import json
import numpy as np
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
canonical_mv = pd.read_csv(OUT / "canonical_mean_variance_policy.csv").iloc[0]
lower_bound = pd.read_csv(
    OUT / "strong_reversal_lower_bound_summary.csv"
)
projection = pd.read_csv(
    OUT / "heuristic_projection_sensitivity.csv"
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
zero_primary = float(
    s["strong_reversal_lower_bound_sensitivity"][
        "all_zero_lower_bounds"
    ]["near_zero_tolerance"]
)
lower_primary = lower_bound.loc[
    np.isclose(lower_bound["near_zero_tolerance"], zero_primary)
].set_index("lower_bound_specification")
all_zero = lower_primary.loc["all_zero_lower_bounds"]
top_zero = lower_primary.loc["highest_ranked_crop_zero_lower_bound"]
winner_projection = projection.loc[
    projection["heuristic_policy"].eq("winner_take_all")
].set_index("projection_method")
winner_l2 = winner_projection.loc["euclidean_l2"]
winner_l1 = winner_projection.loc["l1_lexicographic"]
policy_rows = p.set_index("policy")
policy_suitability = policy_rows.loc[
    "suitability_proportional_euclidean"
]
policy_equal = policy_rows.loc["equal_share_euclidean"]
policy_expected = policy_rows.loc["expected_profit_no_CVaR"]
policy_minimum = policy_rows.loc["minimum_CVaR_endpoint_not_primary"]

def macro(name, value):
    return f"\\newcommand{{\\{name}}}{{{value}}}"

def f(x, n=3):
    return f"{float(x):.{n}f}"

def interval_tex(value):
    """Format a closed positive interval with a comma between endpoints."""
    return str(value).replace("-", ",", 1)

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
    macro("DiversificationWeakGammaInterval", interval_tex(
        row_mv["weak_failure_gamma_intervals"]
    )),
    macro("DiversificationStrongGammaInterval", interval_tex(
        row_mv["strong_failure_gamma_intervals"]
    )),
    macro("DiversificationFrontierPoints", int(row_mv["frontier_points"])),
    macro("CanonicalMVCorn", f(canonical_mv["allocation_Corn"])),
    macro("CanonicalMVSoy", f(canonical_mv["allocation_Soybean"])),
    macro("CanonicalMVWheat", f(canonical_mv["allocation_Winter_Wheat"])),
    macro("CanonicalMVExpectedProfit", f(
        canonical_mv["student_t_evaluation_expected_profit"], 1
    )),
    macro("CanonicalMVGaussianExpectedProfit", f(
        canonical_mv["gaussian_expected_profit"], 1
    )),
    macro("CanonicalMVGaussianVariance", f(
        canonical_mv["gaussian_profit_variance"], 1
    )),
    macro("CanonicalMVCVaR", f(
        canonical_mv["student_t_evaluation_loss_CVaR"], 1
    )),
    macro("CanonicalMVOperationalFeasible", (
        "yes" if bool(canonical_mv["operational_feasible"]) else "no"
    )),
    macro("CanonicalMVRiskFeasible", (
        "yes" if bool(canonical_mv["risk_ceiling_feasible"]) else "no"
    )),
    macro("AllZeroPairwise", int(
        all_zero["selected_pairwise_reversal_cells"]
    )),
    macro("AllZeroComplete", int(
        all_zero["selected_complete_rank_reversal_cells"]
    )),
    macro("AllZeroStrong", int(
        all_zero["selected_strong_reversal_cells"]
    )),
    macro("AllZeroPossibleStrong", int(
        all_zero["possible_strong_reversal_cells"]
    )),
    macro("AllZeroUniversalStrong", int(
        all_zero["universal_strong_reversal_cells"]
    )),
    macro("AllZeroMultiple", int(all_zero["multiple_optimum_cells"])),
    macro("AllZeroInfeasible", int(all_zero["infeasible_cells"])),
    macro("AllZeroMinTop", f(
        all_zero["minimum_selected_top_crop_allocation"]
    )),
    macro("TopZeroPairwise", int(
        top_zero["selected_pairwise_reversal_cells"]
    )),
    macro("TopZeroComplete", int(
        top_zero["selected_complete_rank_reversal_cells"]
    )),
    macro("TopZeroStrong", int(
        top_zero["selected_strong_reversal_cells"]
    )),
    macro("TopZeroPossibleStrong", int(
        top_zero["possible_strong_reversal_cells"]
    )),
    macro("TopZeroUniversalStrong", int(
        top_zero["universal_strong_reversal_cells"]
    )),
    macro("TopZeroMultiple", int(top_zero["multiple_optimum_cells"])),
    macro("TopZeroInfeasible", int(top_zero["infeasible_cells"])),
    macro("ProjectionWinnerLtwoCorn", f(winner_l2["projected_Corn"])),
    macro("ProjectionWinnerLtwoSoy", f(winner_l2["projected_Soybean"])),
    macro("ProjectionWinnerLtwoWheat", f(
        winner_l2["projected_Winter_Wheat"]
    )),
    macro("ProjectionWinnerLoneCorn", f(winner_l1["projected_Corn"])),
    macro("ProjectionWinnerLoneSoy", f(winner_l1["projected_Soybean"])),
    macro("ProjectionWinnerLoneWheat", f(
        winner_l1["projected_Winter_Wheat"]
    )),
    macro("ProjectionWinnerLtwoDistance", f(
        winner_l2["projection_distance_l2"]
    )),
    macro("ProjectionWinnerLoneDistance", f(
        winner_l1["projection_distance_l1"]
    )),
    macro("ProjectionWinnerLtwoProfit", f(
        winner_l2["expected_profit"], 1
    )),
    macro("ProjectionWinnerLtwoCVaR", f(
        winner_l2["cvar_loss"], 1
    )),
    macro("ProjectionWinnerLoneProfit", f(
        winner_l1["expected_profit"], 1
    )),
    macro("ProjectionWinnerLoneCVaR", f(
        winner_l1["cvar_loss"], 1
    )),
    macro("PolicySuitabilityCorn", f(policy_suitability["acres_Corn"])),
    macro("PolicySuitabilitySoy", f(policy_suitability["acres_Soybean"])),
    macro("PolicySuitabilityWheat", f(
        policy_suitability["acres_Winter Wheat"]
    )),
    macro("PolicySuitabilityProfit", f(
        policy_suitability["expected_profit"], 1
    )),
    macro("PolicySuitabilityCVaR", f(policy_suitability["cvar_loss"], 1)),
    macro("PolicyEqualCorn", f(policy_equal["acres_Corn"])),
    macro("PolicyEqualSoy", f(policy_equal["acres_Soybean"])),
    macro("PolicyEqualWheat", f(policy_equal["acres_Winter Wheat"])),
    macro("PolicyEqualProfit", f(policy_equal["expected_profit"], 1)),
    macro("PolicyEqualCVaR", f(policy_equal["cvar_loss"], 1)),
    macro("PolicyExpectedCorn", f(policy_expected["acres_Corn"])),
    macro("PolicyExpectedSoy", f(policy_expected["acres_Soybean"])),
    macro("PolicyExpectedWheat", f(policy_expected["acres_Winter Wheat"])),
    macro("PolicyExpectedProfit", f(policy_expected["expected_profit"], 1)),
    macro("PolicyExpectedCVaR", f(policy_expected["cvar_loss"], 1)),
    macro("PolicyMinimumCorn", f(policy_minimum["acres_Corn"])),
    macro("PolicyMinimumSoy", f(policy_minimum["acres_Soybean"])),
    macro("PolicyMinimumWheat", f(policy_minimum["acres_Winter Wheat"])),
    macro("PolicyMinimumProfit", f(policy_minimum["expected_profit"], 1)),
    macro("PolicyMinimumCVaR", f(policy_minimum["cvar_loss"], 1)),
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
