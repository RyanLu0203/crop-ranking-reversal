"""Read-only calibration helpers for the governed Issue #4 panel."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PANEL = ROOT / "data/processed/canonical_crop_year_panel.csv"
CROP_LABELS = {"corn": "Corn", "soybeans": "Soybean", "wheat": "Winter Wheat"}


def load_margin_matrix(path: Path = PANEL) -> pd.DataFrame:
    panel = pd.read_csv(path)
    matrix = panel.pivot(
        index="year", columns="crop", values="primary_margin_real_2024_usd_per_planted_acre"
    ).sort_index()
    matrix = matrix[["corn", "soybeans", "wheat"]]
    if matrix.shape != (27, 3) or matrix.isna().any().any():
        raise ValueError(f"expected complete 27x3 margin matrix, got {matrix.shape}")
    return matrix.rename(columns=CROP_LABELS)


def panel_calibration(path: Path = PANEL) -> Dict[str, Any]:
    matrix = load_margin_matrix(path)
    panel = pd.read_csv(path)
    latest = panel.loc[panel["year"].eq(2024)].set_index("crop")
    real_cost = (
        latest["operating_cost_usd_per_planted_acre"] * latest["cpi_u_deflator_to_2024"]
    )
    return {
        "crop_names": list(matrix.columns),
        "n_years": int(len(matrix)),
        "years": [int(matrix.index.min()), int(matrix.index.max())],
        "means": matrix.mean().to_dict(),
        "stds": matrix.std(ddof=1).to_dict(),
        "pearson_correlation": matrix.corr(method="pearson").to_numpy().tolist(),
        "kendall_correlation": matrix.corr(method="kendall").to_numpy().tolist(),
        "costs_2024_real": {
            CROP_LABELS[crop]: float(real_cost.loc[crop]) for crop in ("corn", "soybeans", "wheat")
        },
        "ranking": matrix.mean().sort_values(ascending=False).index.tolist(),
        "source_path": path.relative_to(ROOT).as_posix(),
    }


def equicorrelation_from_kendall_tau(tau: float, n_crops: int) -> np.ndarray:
    tau = float(tau)
    if not 0.0 <= tau < 1.0:
        raise ValueError("Kendall tau must be in [0, 1)")
    rho = np.sin(np.pi * tau / 2.0)
    corr = np.full((n_crops, n_crops), rho, dtype=float)
    np.fill_diagonal(corr, 1.0)
    return corr


def clayton_theta_from_kendall_tau(tau: float) -> float:
    tau = float(tau)
    if not 0.0 <= tau < 1.0:
        raise ValueError("Kendall tau must be in [0, 1)")
    return 0.0 if tau == 0.0 else 2.0 * tau / (1.0 - tau)
