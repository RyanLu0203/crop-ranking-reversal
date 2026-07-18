"""Empirical dependence feasibility and estimation diagnostics."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd
from scipy.stats import kendalltau


def complete_profit_matrix(panel: pd.DataFrame, crops: Iterable[str]) -> pd.DataFrame:
    crops = list(crops)
    pivot = panel.loc[panel["crop"].isin(crops)].pivot_table(
        index=["state", "county_fips", "county", "year"],
        columns="crop",
        values="profit_per_acre",
        aggfunc="first",
    )
    for crop in crops:
        if crop not in pivot:
            pivot[crop] = np.nan
    return pivot[crops].dropna()


def assess_window_designs(panel: pd.DataFrame, sample_config: Dict[str, object]) -> pd.DataFrame:
    crops = list(sample_config["selected_crops"])
    state = sample_config["selected_states"][0]
    county_fips = set(sample_config["selected_county_fips"])
    years = range(int(sample_config["start_year"]), int(sample_config["end_year"]) + 1)
    selected = panel.loc[panel["state"].eq(state) & panel["county_fips"].isin(county_fips) & panel["crop"].isin(crops)]
    rows: List[Dict[str, object]] = []
    designs = [
        ("A_county_5yr_rolling", "county", "rolling", 5),
        ("B_county_10yr_rolling", "county", "rolling", 10),
        ("C_county_expanding", "county", "expanding", None),
        ("D_pooled_counties_5yr_rolling", "pooled_counties", "rolling", 5),
        ("E_state_level_expanding", "state", "expanding", None),
    ]
    for design_id, pooling, window_type, window_years in designs:
        for year in years:
            if window_type == "rolling":
                train = selected.loc[(selected["year"] >= year - int(window_years)) & (selected["year"] < year)]
            else:
                train = selected.loc[selected["year"] < year]
            if pooling == "county":
                groups = train.groupby(["state", "county_fips", "county"], dropna=False)
            elif pooling == "pooled_counties":
                groups = [(("pooled", "pooled", "pooled"), train)]
            else:
                state_train = panel.loc[panel["state"].eq(state) & panel["crop"].isin(crops) & (panel["year"] < year)]
                groups = [(("state", "state", state), state_train)]
            for key, part in groups:
                matrix = complete_profit_matrix(part, crops)
                n = int(len(matrix))
                rows.append(
                    {
                        "design_id": design_id,
                        "decision_year": int(year),
                        "pooling": pooling,
                        "window_type": window_type,
                        "window_years": window_years if window_years is not None else "expanding",
                        "estimation_unit": key[-1],
                        "n_complete_observations": n,
                        "n_crops": len(crops),
                        "can_estimate_marginals": bool(n >= 3),
                        "can_estimate_correlation": bool(n >= len(crops) + 2),
                        "can_estimate_gaussian_copula": bool(n >= max(8, len(crops) + 5)),
                        "can_estimate_clayton_copula": bool(n >= 10),
                        "effective_sample_size": n,
                        "stability_warning": "" if n >= 10 else "too few annual complete cases for stable copula estimation",
                    }
                )
    return pd.DataFrame(rows)


def select_window_design(feasibility: pd.DataFrame) -> Dict[str, object]:
    summary = (
        feasibility.groupby("design_id")
        .agg(
            median_complete_observations=("n_complete_observations", "median"),
            min_complete_observations=("n_complete_observations", "min"),
            share_gaussian_feasible=("can_estimate_gaussian_copula", "mean"),
            share_clayton_feasible=("can_estimate_clayton_copula", "mean"),
        )
        .reset_index()
    )
    preferred_order = [
        "B_county_10yr_rolling",
        "C_county_expanding",
        "D_pooled_counties_5yr_rolling",
        "E_state_level_expanding",
        "A_county_5yr_rolling",
    ]
    viable = summary.loc[summary["share_gaussian_feasible"] >= 0.8].copy()
    if viable.empty:
        viable = summary.copy()
    viable["preference"] = viable["design_id"].map({name: idx for idx, name in enumerate(preferred_order)}).fillna(99)
    row = viable.sort_values(["share_gaussian_feasible", "median_complete_observations", "preference"], ascending=[False, False, True]).iloc[0]
    design_id = row["design_id"]
    if design_id == "A_county_5yr_rolling":
        rationale = "Selected only because no more stable design was feasible; annual 5-year county windows remain weak."
    elif design_id == "B_county_10yr_rolling":
        rationale = "Selected because county-specific 10-year windows provide more complete annual observations than 5-year windows."
    elif design_id == "C_county_expanding":
        rationale = "Selected because county-specific expanding windows improve sample size while preserving county interpretation."
    elif design_id == "D_pooled_counties_5yr_rolling":
        rationale = "Selected because pooling counties gives adequate complete cases while keeping rolling-window timing."
    else:
        rationale = "Selected because state-level dependence estimation is the most statistically stable available design."
    return {"selected_design_id": design_id, "rationale": rationale, "summary": summary}


def estimate_dependence(training_panel: pd.DataFrame, crops: Iterable[str], model: str = "Gaussian") -> Dict[str, object]:
    crops = list(crops)
    matrix = complete_profit_matrix(training_panel, crops)
    n = int(len(matrix))
    warnings: List[str] = []
    if n < 3:
        return {
            "model": model,
            "n_observations": n,
            "convergence_status": "failed",
            "parameters": {},
            "tail_dependence": np.nan,
            "warnings": "fewer than 3 complete observations",
        }
    pearson = matrix.corr(method="pearson").fillna(0.0)
    spearman = matrix.corr(method="spearman").fillna(0.0)
    for corr in [pearson, spearman]:
        np.fill_diagonal(corr.values, 1.0)
    if model == "Gaussian":
        params = {"correlation": pearson.to_dict()}
        return {
            "model": "Gaussian",
            "n_observations": n,
            "convergence_status": "estimated" if n >= len(crops) + 2 else "unstable",
            "parameters": params,
            "pearson_min_offdiag": float(_min_offdiag(pearson.to_numpy())),
            "spearman_min_offdiag": float(_min_offdiag(spearman.to_numpy())),
            "tail_dependence": 0.0,
            "log_likelihood": np.nan,
            "aic": np.nan,
            "bic": np.nan,
            "warnings": "; ".join(warnings),
        }
    if model == "Clayton":
        if n < 10:
            return {
                "model": "Clayton",
                "n_observations": n,
                "convergence_status": "failed",
                "parameters": {},
                "tail_dependence": np.nan,
                "log_likelihood": np.nan,
                "aic": np.nan,
                "bic": np.nan,
                "warnings": "fewer than 10 complete observations",
            }
        taus = []
        for i, crop_i in enumerate(crops):
            for crop_j in crops[i + 1 :]:
                tau, _ = kendalltau(matrix[crop_i], matrix[crop_j], nan_policy="omit")
                if np.isfinite(tau):
                    taus.append(float(tau))
        if not taus or np.mean(taus) <= 0:
            return {
                "model": "Clayton",
                "n_observations": n,
                "convergence_status": "failed",
                "parameters": {"mean_kendall_tau": float(np.mean(taus)) if taus else np.nan},
                "tail_dependence": np.nan,
                "log_likelihood": np.nan,
                "aic": np.nan,
                "bic": np.nan,
                "warnings": "Clayton requires positive lower-tail association; mean Kendall tau is not positive",
            }
        mean_tau = min(float(np.mean(taus)), 0.95)
        theta = 2.0 * mean_tau / max(1.0 - mean_tau, 1e-8)
        tail = 2.0 ** (-1.0 / theta)
        return {
            "model": "Clayton",
            "n_observations": n,
            "convergence_status": "method_of_moments_estimated",
            "parameters": {"mean_kendall_tau": mean_tau, "theta": theta},
            "tail_dependence": tail,
            "log_likelihood": np.nan,
            "aic": np.nan,
            "bic": np.nan,
            "warnings": "method-of-moments pilot estimate; not a forced model selection",
        }
    raise ValueError(f"Unsupported empirical dependence model: {model}")


def _min_offdiag(corr: np.ndarray) -> float:
    if corr.shape[0] <= 1:
        return 1.0
    mask = ~np.eye(corr.shape[0], dtype=bool)
    return float(np.nanmin(corr[mask]))
