"""Empirical-validation template for future county-year-crop panels."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from crop_optimization.benchmark_policies import run_policy_comparison
from crop_optimization.cvar_optimizer import solve_expected_profit_allocation
from .empirical_scenarios import generate_empirical_profit_scenarios
from crop_simulation.scenario_generation import generate_profit_scenarios

REQUIRED_COLUMNS = [
    "county",
    "state",
    "year",
    "crop",
    "yield_per_acre",
    "price",
    "cost_per_acre",
    "profit_per_acre",
    "suitability_score",
]


def construct_profit_panel(path_or_frame: object) -> pd.DataFrame:
    """Load and validate the processed county-year-crop panel."""

    if isinstance(path_or_frame, pd.DataFrame):
        panel = path_or_frame.copy()
    else:
        panel = pd.read_csv(path_or_frame)
    missing = [col for col in REQUIRED_COLUMNS if col not in panel.columns]
    if missing:
        raise ValueError(f"Empirical panel is missing required columns: {missing}")
    return panel[REQUIRED_COLUMNS].copy()


def estimate_marginals(panel: pd.DataFrame, crops: Optional[Iterable[str]] = None) -> pd.DataFrame:
    """Estimate crop-level profit marginal moments from historical data."""

    crops = list(crops) if crops is not None else sorted(panel["crop"].dropna().unique())
    grouped = (
        panel.loc[panel["crop"].isin(crops)]
        .groupby("crop")["profit_per_acre"]
        .agg(mean_profit="mean", std_profit="std", observations="count")
        .reset_index()
    )
    return grouped


def estimate_copula(panel: pd.DataFrame, crops: Optional[Iterable[str]] = None) -> Dict[str, object]:
    """Estimate a simple rank-correlation dependence proxy.

    A full empirical copula fit should be added once the real panel is
    available and county/year coverage is audited.
    """

    crops = list(crops) if crops is not None else sorted(panel["crop"].dropna().unique())
    pivot = panel.loc[panel["crop"].isin(crops)].pivot_table(
        index=["state", "county", "year"],
        columns="crop",
        values="profit_per_acre",
        aggfunc="mean",
    )
    corr = pivot[crops].corr(method="spearman").fillna(0.0)
    np.fill_diagonal(corr.values, 1.0)
    return {"copula_type": "Gaussian", "rank_correlation": corr}


def generate_empirical_scenarios(
    panel: pd.DataFrame,
    crops: Iterable[str],
    n_scenarios: int,
    random_seed: int,
) -> Dict[str, object]:
    """Generate scenarios from estimated empirical moments and rank correlation."""

    crops = list(crops)
    marginals = estimate_marginals(panel, crops).set_index("crop").loc[crops]
    copula = estimate_copula(panel, crops)
    scenarios, metadata = generate_profit_scenarios(
        marginals["mean_profit"].to_numpy(),
        marginals["std_profit"].fillna(0.0).replace(0.0, 1e-6).to_numpy(),
        n_scenarios,
        "Gaussian",
        copula["rank_correlation"].to_numpy(),
        random_seed,
        crop_names=crops,
        marginal_model={"type": "normal"},
    )
    return {"scenarios": scenarios, "metadata": metadata, "marginals": marginals.reset_index(), "copula": copula}


def rolling_window_policy_evaluation(
    panel: pd.DataFrame,
    base_config: Dict[str, object],
    window_years: int = 5,
    n_scenarios: int = 5000,
) -> pd.DataFrame:
    """Template rolling-window evaluation.

    Uses the previous `window_years` to estimate distributions, then
    evaluates policies on the next realized year. This function is ready
    for real data but intentionally makes no empirical claim without it.
    """

    years = sorted(panel["year"].dropna().unique())
    crops = list(base_config["crop_names"])
    rows: List[Dict[str, object]] = []
    for year in years:
        history = panel.loc[(panel["year"] >= year - window_years) & (panel["year"] < year)]
        realized = panel.loc[panel["year"] == year]
        if history["year"].nunique() < window_years or realized.empty:
            continue
        generated = generate_empirical_scenarios(history, crops, n_scenarios, int(base_config["random_seed"]) + int(year))
        comparison = run_policy_comparison(generated["scenarios"], base_config)
        realized_profit = realized.groupby("crop")["profit_per_acre"].mean().reindex(crops)
        for _, row in comparison.iterrows():
            allocation = np.asarray([row.get(f"acres_{crop}", np.nan) for crop in crops], dtype=float)
            rows.append(
                {
                    "year": int(year),
                    "policy": row["policy"],
                    "realized_profit": float(np.nansum(allocation * realized_profit.to_numpy())),
                    "ranking_reversal": bool(row.get("acres_Soybean", 0.0) > row.get("acres_Corn", 0.0)),
                    "cvar_loss_estimate": row.get("cvar_loss"),
                }
            )
    return pd.DataFrame(rows)


def compute_out_of_sample_metrics(rolling_results: pd.DataFrame) -> pd.DataFrame:
    if rolling_results.empty:
        return pd.DataFrame(
            columns=[
                "policy",
                "mean_realized_profit",
                "worst_decile_realized_profit",
                "realized_cvar",
                "ranking_reversal_frequency",
                "regret_relative_to_ex_post_best",
            ]
        )
    best_by_year = rolling_results.groupby("year")["realized_profit"].max()
    enriched = rolling_results.join(best_by_year.rename("best_realized_profit"), on="year")
    enriched["regret"] = enriched["best_realized_profit"] - enriched["realized_profit"]
    rows = []
    for policy, part in enriched.groupby("policy"):
        losses = -part["realized_profit"].to_numpy()
        tail_count = max(1, int(np.ceil(0.10 * len(losses))))
        rows.append(
            {
                "policy": policy,
                "mean_realized_profit": part["realized_profit"].mean(),
                "worst_decile_realized_profit": np.sort(part["realized_profit"].to_numpy())[:tail_count].mean(),
                "realized_cvar": np.sort(losses)[-tail_count:].mean(),
                "ranking_reversal_frequency": part["ranking_reversal"].mean(),
                "regret_relative_to_ex_post_best": part["regret"].mean(),
            }
        )
    return pd.DataFrame(rows)


def empirical_template_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "component": "Input panel",
                "status": "Pending real county-year-crop data",
                "required_fields": ", ".join(REQUIRED_COLUMNS),
            },
            {
                "component": "Rolling-window design",
                "status": "Implemented template",
                "required_fields": "Previous 5 years estimate next-year policy performance",
            },
            {
                "component": "Policies",
                "status": "Implemented template",
                "required_fields": "SU, EO, MV, CVaR-optimal",
            },
            {
                "component": "Out-of-sample metrics",
                "status": "Implemented template",
                "required_fields": "Mean profit, worst-decile profit, realized CVaR, reversal frequency, regret",
            },
        ]
    )


def train_panel_for_decision(
    panel: pd.DataFrame,
    state: str,
    county_fips: str,
    year: int,
    crops: Iterable[str],
    design_id: str,
    selected_county_fips: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    crops = list(crops)
    base = panel.loc[panel["state"].eq(state) & panel["crop"].isin(crops) & (panel["year"] < year)].copy()
    if design_id == "A_county_5yr_rolling":
        return base.loc[base["county_fips"].eq(county_fips) & (base["year"] >= year - 5)]
    if design_id == "B_county_10yr_rolling":
        return base.loc[base["county_fips"].eq(county_fips) & (base["year"] >= year - 10)]
    if design_id == "C_county_expanding":
        return base.loc[base["county_fips"].eq(county_fips)]
    if design_id == "D_pooled_counties_5yr_rolling":
        selected = set(selected_county_fips or [])
        return base.loc[base["county_fips"].isin(selected) & (base["year"] >= year - 5)]
    if design_id == "E_state_level_expanding":
        return base
    raise ValueError(f"Unsupported window design: {design_id}")


def _decision_config(
    training_panel: pd.DataFrame,
    suitability_scores: Dict[str, float],
    crops: List[str],
    alpha: float = 0.90,
    n_scenarios_for_cvar: Optional[np.ndarray] = None,
) -> Dict[str, object]:
    county_training = training_panel.copy()
    acreage_by_year = county_training.pivot_table(index="year", columns="crop", values="acreage_planted", aggfunc="mean")
    total_acres = float(acreage_by_year[crops].sum(axis=1).dropna().mean())
    if not np.isfinite(total_acres) or total_acres <= 0:
        total_acres = 1.0
    costs = {}
    for crop in crops:
        part = county_training.loc[county_training["crop"].eq(crop)].sort_values("year")
        value = part["cost_per_acre"].dropna().iloc[-1] if part["cost_per_acre"].notna().any() else 1.0
        costs[crop] = float(value)
    observed_cost = []
    for _, year_part in county_training.groupby("year"):
        if set(crops).issubset(set(year_part["crop"])):
            tmp = year_part.set_index("crop").reindex(crops)
            observed_cost.append(float((tmp["acreage_planted"] * tmp["cost_per_acre"]).sum()))
    budget = float(np.nanmean(observed_cost)) if observed_cost else float(total_acres * np.mean(list(costs.values())))
    budget = max(budget, 1.0)
    lower = {crop: 0.0 for crop in crops}
    upper = {crop: total_acres for crop in crops}
    rotation_caps = {"Corn": 0.60 * total_acres} if "Corn" in crops else {}
    cvar_limit = 0.0
    if n_scenarios_for_cvar is not None and len(crops) > 0:
        equal = np.full(len(crops), total_acres / len(crops))
        from .evaluation import empirical_var_cvar_losses

        _, cvar = empirical_var_cvar_losses(-(np.asarray(n_scenarios_for_cvar) @ equal), alpha)
        cvar_limit = float(max(0.0, cvar))
    return {
        "crop_names": crops,
        "total_acres": total_acres,
        "budget": budget,
        "alpha": alpha,
        "cvar_limit": cvar_limit,
        "costs": costs,
        "suitability_scores": suitability_scores,
        "lower_bounds": lower,
        "upper_bounds": upper,
        "rotation_caps": rotation_caps,
        "mean_variance_gamma": 1e-5,
    }


def _general_reversal(allocation: Iterable[float], suitability_scores: Dict[str, float], crops: List[str]) -> Dict[str, object]:
    alloc = dict(zip(crops, np.asarray(list(allocation), dtype=float)))
    ranked = sorted(crops, key=lambda crop: suitability_scores.get(crop, np.nan), reverse=True)
    top = ranked[0]
    lower_exceeds = [crop for crop in ranked[1:] if alloc.get(crop, 0.0) > alloc.get(top, 0.0) + 1e-5]
    return {
        "top_suitability_crop": top,
        "pairwise_reversal": bool(lower_exceeds),
        "strong_reversal": bool(alloc.get(top, 0.0) <= 1e-5 and any(alloc.get(crop, 0.0) > 1e-5 for crop in ranked[1:])),
        "reversing_crops": ";".join(lower_exceeds),
    }


def run_real_rolling_validation(
    panel: pd.DataFrame,
    sample_config: Dict[str, object],
    suitability: pd.DataFrame,
    window_design: str,
    suitability_definition: str,
    n_scenarios: int = 1000,
    random_seed: int = 20260703,
) -> pd.DataFrame:
    """Run real rolling validation with strict train/test separation."""

    state = sample_config["selected_states"][0]
    counties = list(sample_config["selected_county_fips"])
    crops = list(sample_config["selected_crops"])
    start_year = int(sample_config["start_year"])
    end_year = int(sample_config["end_year"])
    rows: List[Dict[str, object]] = []
    selected = panel.loc[panel["state"].eq(state) & panel["county_fips"].isin(counties) & panel["crop"].isin(crops)].copy()
    suit = suitability.loc[suitability["suitability_definition"].eq(suitability_definition)].copy()
    for year in range(start_year, end_year + 1):
        for county_fips in counties:
            realized = selected.loc[selected["county_fips"].eq(county_fips) & selected["year"].eq(year)]
            if realized["crop"].nunique() < len(crops) or realized["profit_per_acre"].isna().any():
                continue
            training = train_panel_for_decision(
                selected,
                state,
                county_fips,
                year,
                crops,
                window_design,
                selected_county_fips=counties,
            )
            training_complete_years = training.pivot_table(index=["county_fips", "year"], columns="crop", values="profit_per_acre").dropna().shape[0]
            if training_complete_years < 5:
                continue
            suit_rows = suit.loc[suit["county_fips"].eq(county_fips) & suit["year"].eq(year) & suit["crop"].isin(crops)]
            if suit_rows["crop"].nunique() < len(crops):
                continue
            suitability_scores = suit_rows.set_index("crop")["suitability_score"].reindex(crops).fillna(1.0).to_dict()
            scenarios, metadata = generate_empirical_profit_scenarios(
                training,
                crops,
                decision_year=year,
                random_seed=int(random_seed) + int(year) + int(str(county_fips)[-3:]),
                n_scenarios=n_scenarios,
                dependence_model="Gaussian",
            )
            cfg = _decision_config(training.loc[training["county_fips"].eq(county_fips)], suitability_scores, crops, n_scenarios_for_cvar=scenarios)
            comparison = run_policy_comparison(scenarios, cfg)
            realized_profit = realized.set_index("crop").reindex(crops)["profit_per_acre"].astype(float).to_numpy()
            costs = np.asarray([cfg["costs"][crop] for crop in crops], dtype=float)
            oracle = solve_expected_profit_allocation(
                realized_profit,
                costs,
                float(cfg["total_acres"]),
                float(cfg["budget"]),
                [cfg["lower_bounds"][crop] for crop in crops],
                [cfg["upper_bounds"][crop] for crop in crops],
                cfg.get("rotation_caps"),
                crops,
            )
            oracle_profit = float(np.dot(oracle.allocation, realized_profit)) if oracle.allocation is not None else np.nan
            for _, policy in comparison.iterrows():
                allocation = np.asarray([policy.get(f"acres_{crop}", np.nan) for crop in crops], dtype=float)
                if np.isnan(allocation).any():
                    continue
                reversal = _general_reversal(allocation, suitability_scores, crops)
                realized_portfolio_profit = float(np.dot(allocation, realized_profit))
                policy_feasible = not bool(policy.get("cvar_violation", True)) and not bool(policy.get("budget_violation", False))
                budget_usage = float(policy.get("budget_usage", np.dot(allocation, costs)))
                acreage_usage = float(policy.get("acreage_usage", np.sum(allocation)))
                cvar_loss = float(policy.get("cvar_loss", np.nan))
                rotation_active = False
                for crop, cap in cfg.get("rotation_caps", {}).items():
                    if crop in crops:
                        rotation_active = rotation_active or allocation[crops.index(crop)] >= float(cap) - 1e-5
                rows.append(
                    {
                        "state": state,
                        "county_fips": county_fips,
                        "county": realized["county"].iloc[0],
                        "decision_year": int(year),
                        "training_start": int(training["year"].min()),
                        "training_end": int(training["year"].max()),
                        "train_year_max": int(training["year"].max()),
                        "test_year": int(year),
                        "window_design": window_design,
                        "suitability_definition": suitability_definition,
                        "policy": policy["policy"],
                        "realized_portfolio_profit": realized_portfolio_profit,
                        "expected_modeled_profit": float(policy.get("expected_profit", np.nan)),
                        "realized_shortfall": float(max(0.0, -realized_portfolio_profit)),
                        "model_based_cvar_loss": cvar_loss,
                        "constraint_violation": bool(policy.get("cvar_violation", False) or policy.get("budget_violation", False)),
                        "policy_feasible": bool(policy_feasible),
                        "oracle_feasible_profit": oracle_profit,
                        "regret_vs_expost_feasible_oracle": oracle_profit - realized_portfolio_profit if policy_feasible and np.isfinite(oracle_profit) else np.nan,
                        "regret_comparable": bool(policy_feasible and np.isfinite(oracle_profit)),
                        "pairwise_reversal": reversal["pairwise_reversal"],
                        "strong_reversal": reversal["strong_reversal"],
                        "top_suitability_crop": reversal["top_suitability_crop"],
                        "reversing_crops": reversal["reversing_crops"],
                        "cvar_limit": float(cfg["cvar_limit"]),
                        "budget": float(cfg["budget"]),
                        "budget_usage": budget_usage,
                        "budget_active": bool(abs(float(cfg["budget"]) - budget_usage) <= 1e-4 * max(1.0, float(cfg["budget"]))),
                        "total_acres": float(cfg["total_acres"]),
                        "acreage_usage": acreage_usage,
                        "acreage_active": bool(abs(float(cfg["total_acres"]) - acreage_usage) <= 1e-4 * max(1.0, float(cfg["total_acres"]))),
                        "cvar_active": bool(np.isfinite(cvar_loss) and abs(float(cfg["cvar_limit"]) - cvar_loss) <= 1e-4 * max(1.0, abs(float(cfg["cvar_limit"])))),
                        "rotation_active": bool(rotation_active),
                        "dependence_model": metadata["dependence_model"],
                        "dependence_n_observations": metadata["dependence_diagnostics"]["n_observations"],
                    }
                )
                for crop, acres in zip(crops, allocation):
                    rows[-1][f"acres_{crop}"] = float(acres)
    return pd.DataFrame(rows)


def empirical_policy_summary(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return pd.DataFrame()
    rows = []
    for policy, part in results.groupby("policy"):
        realized = part["realized_portfolio_profit"].to_numpy()
        tail_count = max(1, int(np.ceil(0.10 * len(realized))))
        comparable = part.loc[part["regret_comparable"]]
        rows.append(
            {
                "policy": policy,
                "n_decisions": int(len(part)),
                "mean_realized_profit": float(np.mean(realized)),
                "median_realized_profit": float(np.median(realized)),
                "worst_decile_realized_profit": float(np.sort(realized)[:tail_count].mean()),
                "realized_downside_metric": float(np.mean(np.maximum(0.0, -realized))),
                "mean_model_based_cvar_loss": float(part["model_based_cvar_loss"].mean()),
                "violation_rate": float(part["constraint_violation"].mean()),
                "empirical_reversal_frequency": float(part["pairwise_reversal"].mean()),
                "mean_feasible_regret": float(comparable["regret_vs_expost_feasible_oracle"].mean()) if not comparable.empty else np.nan,
            }
        )
    return pd.DataFrame(rows)


def empirical_reversal_summary(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return pd.DataFrame()
    group_cols = ["suitability_definition", "policy"]
    return (
        results.groupby(group_cols)
        .agg(
            n_decisions=("pairwise_reversal", "size"),
            pairwise_reversal_frequency=("pairwise_reversal", "mean"),
            strong_reversal_frequency=("strong_reversal", "mean"),
            counties=("county_fips", "nunique"),
            years=("decision_year", "nunique"),
            mean_model_based_cvar_loss=("model_based_cvar_loss", "mean"),
            violation_rate=("constraint_violation", "mean"),
        )
        .reset_index()
    )
