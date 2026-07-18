"""Empirical scenario generation with train/test separation metadata."""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd

from .empirical_dependence import complete_profit_matrix, estimate_dependence
from crop_simulation.scenario_generation import generate_profit_scenarios


def nearest_psd_correlation(corr: np.ndarray) -> np.ndarray:
    mat = np.asarray(corr, dtype=float)
    mat = np.nan_to_num(mat, nan=0.0)
    mat = (mat + mat.T) / 2.0
    eigvals, eigvecs = np.linalg.eigh(mat)
    eigvals = np.clip(eigvals, 1e-6, None)
    psd = eigvecs @ np.diag(eigvals) @ eigvecs.T
    diag = np.sqrt(np.clip(np.diag(psd), 1e-12, None))
    psd = psd / diag[:, None] / diag[None, :]
    np.fill_diagonal(psd, 1.0)
    return psd


def empirical_marginal_moments(training_panel: pd.DataFrame, crops: Iterable[str]) -> pd.DataFrame:
    crops = list(crops)
    grouped = (
        training_panel.loc[training_panel["crop"].isin(crops)]
        .groupby("crop")["profit_per_acre"]
        .agg(mean_profit="mean", std_profit="std", observations="count")
        .reindex(crops)
        .reset_index()
    )
    grouped["std_profit"] = grouped["std_profit"].fillna(0.0).replace(0.0, 1e-6)
    return grouped


def generate_empirical_profit_scenarios(
    training_panel: pd.DataFrame,
    crops: Iterable[str],
    decision_year: int,
    random_seed: int,
    n_scenarios: int,
    dependence_model: str = "Gaussian",
) -> Tuple[np.ndarray, Dict[str, object]]:
    """Generate scenarios using only years strictly before decision_year."""

    crops = list(crops)
    if not (training_panel["year"] < decision_year).all():
        raise ValueError("training_panel contains decision-year or future observations.")
    moments = empirical_marginal_moments(training_panel, crops)
    if moments["mean_profit"].isna().any():
        raise ValueError("Cannot generate scenarios with missing crop marginal means.")
    dep = estimate_dependence(training_panel, crops, dependence_model)
    if dependence_model == "Clayton" and dep["convergence_status"] != "method_of_moments_estimated":
        dependence_model = "Gaussian"
        dep = estimate_dependence(training_panel, crops, "Gaussian")
    if dependence_model == "Gaussian":
        matrix = complete_profit_matrix(training_panel, crops)
        corr = nearest_psd_correlation(matrix.corr(method="pearson").reindex(index=crops, columns=crops).fillna(0.0).to_numpy())
        copula_param = corr
    else:
        copula_param = dep["parameters"]["theta"]
    scenarios, metadata = generate_profit_scenarios(
        moments["mean_profit"].to_numpy(),
        moments["std_profit"].to_numpy(),
        int(n_scenarios),
        dependence_model,
        copula_param,
        int(random_seed),
        crop_names=crops,
        marginal_model={"type": "normal"},
    )
    metadata.update(
        {
            "decision_year": int(decision_year),
            "training_start": int(training_panel["year"].min()),
            "training_end": int(training_panel["year"].max()),
            "geography": sorted(training_panel["county"].dropna().unique().tolist()),
            "crops": crops,
            "marginal_model": "normal_moments_from_training_profit",
            "dependence_model": dependence_model,
            "dependence_diagnostics": dep,
            "marginals": moments.to_dict("records"),
        }
    )
    return scenarios, metadata
