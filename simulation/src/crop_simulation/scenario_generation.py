"""Scenario generation for calibrated crop profit simulations."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
from scipy import stats

from .copula_models import copula_metadata, sample_copula_uniforms


def _as_array(values: Iterable[float]) -> np.ndarray:
    return np.asarray(list(values), dtype=float)


def _normal_marginal_ppf(uniforms: np.ndarray, means: np.ndarray, stds: np.ndarray) -> np.ndarray:
    return means[None, :] + stds[None, :] * stats.norm.ppf(uniforms)


def _student_t_marginal_ppf(uniforms: np.ndarray, means: np.ndarray, stds: np.ndarray, df: float) -> np.ndarray:
    """Student-t marginal calibrated to the requested mean and standard deviation."""

    df = float(df)
    if df <= 2.0:
        raise ValueError("Student-t marginal df must exceed 2 to have finite variance.")
    standardized = stats.t.ppf(uniforms, df=df) / np.sqrt(df / (df - 2.0))
    return means[None, :] + stds[None, :] * standardized


def _skewed_mixture_ppf(
    uniforms: np.ndarray,
    means: np.ndarray,
    stds: np.ndarray,
    *,
    tail_probability: float,
    within_std_fraction: float,
) -> np.ndarray:
    """Map uniforms to a left-skewed two-regime marginal.

    The bad and normal regimes are calibrated so that each marginal has
    the requested mean and standard deviation in population. This keeps
    the manuscript's baseline moments while allowing economically relevant
    downside tails for CVaR-on-losses constraints.
    """

    p_bad = float(tail_probability)
    if not 0.0 < p_bad < 0.5:
        raise ValueError("tail_probability must be in (0, 0.5).")
    within = float(within_std_fraction)
    if not 0.0 <= within < 1.0:
        raise ValueError("within_std_fraction must be in [0, 1).")

    within_stds = stds * within
    between_variance = np.maximum(stds**2 - within_stds**2, 0.0)
    bad_offset = np.sqrt(between_variance * (1.0 - p_bad) / p_bad)
    good_offset = p_bad / (1.0 - p_bad) * bad_offset
    bad_means = means - bad_offset
    good_means = means + good_offset

    bad_mask = uniforms <= p_bad
    result = np.empty_like(uniforms, dtype=float)
    for crop_idx in range(uniforms.shape[1]):
        u = uniforms[:, crop_idx]
        bad = bad_mask[:, crop_idx]

        bad_u = np.clip(u[bad] / p_bad, 1e-9, 1.0 - 1e-9)
        good_u = np.clip((u[~bad] - p_bad) / (1.0 - p_bad), 1e-9, 1.0 - 1e-9)

        result[bad, crop_idx] = bad_means[crop_idx] + within_stds[crop_idx] * stats.norm.ppf(bad_u)
        result[~bad, crop_idx] = good_means[crop_idx] + within_stds[crop_idx] * stats.norm.ppf(good_u)
    return result


def generate_profit_scenarios(
    means: Iterable[float],
    stds: Iterable[float],
    n_scenarios: int,
    copula_type: str,
    copula_param: Any,
    random_seed: int,
    crop_names: Optional[List[str]] = None,
    marginal_model: Optional[Dict[str, Any]] = None,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Generate per-acre profit scenarios and metadata.

    Parameters match the paper objective. By default, the function uses a
    calibrated skewed-mixture marginal that preserves the requested means
    and standard deviations while creating downside scenarios.
    """

    means_arr = _as_array(means)
    stds_arr = _as_array(stds)
    if means_arr.shape != stds_arr.shape:
        raise ValueError("means and stds must have the same length.")

    n_crops = len(means_arr)
    rng = np.random.default_rng(int(random_seed))
    uniforms = sample_copula_uniforms(n_scenarios, n_crops, copula_type, copula_param, rng)

    marginal_model = dict(marginal_model or {"type": "skewed_mixture"})
    marginal_type = marginal_model.get("type", "skewed_mixture").lower()
    if marginal_type in {"normal", "gaussian"}:
        scenarios = _normal_marginal_ppf(uniforms, means_arr, stds_arr)
    elif marginal_type in {"student_t", "student-t", "t"}:
        scenarios = _student_t_marginal_ppf(
            uniforms,
            means_arr,
            stds_arr,
            df=float(marginal_model.get("df", 5)),
        )
    elif marginal_type in {"skewed_mixture", "calibrated_skewed_mixture"}:
        scenarios = _skewed_mixture_ppf(
            uniforms,
            means_arr,
            stds_arr,
            tail_probability=float(marginal_model.get("tail_probability", 0.07)),
            within_std_fraction=float(marginal_model.get("within_std_fraction", 0.20)),
        )
    else:
        raise ValueError(f"Unsupported marginal model: {marginal_type}")

    metadata = copula_metadata(copula_type, copula_param).to_dict()
    metadata.update(
        {
            "seed": int(random_seed),
            "n_scenarios": int(n_scenarios),
            "crop_names": crop_names or [f"Crop {i + 1}" for i in range(n_crops)],
            "target_means": means_arr.tolist(),
            "target_stds": stds_arr.tolist(),
            "sample_means": scenarios.mean(axis=0).tolist(),
            "sample_stds": scenarios.std(axis=0, ddof=1).tolist(),
            "marginal_assumptions": marginal_model,
        }
    )
    return scenarios, metadata
