"""Copula utilities used by the simulation experiments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class CopulaMetadata:
    """Lightweight copula metadata written to experiment outputs."""

    copula_type: str
    parameter: Any
    lower_tail_dependence: float
    ordering_scope: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "copula_type": self.copula_type,
            "copula_param": self.parameter,
            "lower_tail_dependence": self.lower_tail_dependence,
            "ordering_scope": self.ordering_scope,
        }


def validate_correlation_matrix(corr: np.ndarray, n_crops: int) -> np.ndarray:
    """Validate a copula correlation matrix and reject silent repairs."""

    matrix = np.asarray(corr, dtype=float)
    if matrix.shape != (n_crops, n_crops):
        raise ValueError(f"correlation matrix must have shape {(n_crops, n_crops)}")
    if not np.isfinite(matrix).all() or not np.allclose(matrix, matrix.T, atol=1e-12):
        raise ValueError("correlation matrix must be finite and symmetric")
    if not np.allclose(np.diag(matrix), 1.0, atol=1e-12):
        raise ValueError("correlation matrix diagonal must equal one")
    if np.linalg.eigvalsh(matrix).min() < -1e-10:
        raise ValueError("correlation matrix must be positive semidefinite")
    return matrix


def lower_tail_dependence(copula_type: str, copula_param: Any) -> float:
    """Return the theoretical lower-tail dependence coefficient when defined."""

    normalized = copula_type.lower().replace("_", "-")
    if normalized == "clayton":
        theta = float(copula_param)
        if theta <= 0:
            return 0.0
        return float(2 ** (-1.0 / theta))
    if normalized in {"gaussian", "normal"}:
        return 0.0
    if normalized in {"t", "student-t", "t-copula"}:
        if isinstance(copula_param, dict):
            df = float(copula_param.get("df", 4))
            corr = np.asarray(copula_param.get("corr", [[1.0, 0.0], [0.0, 1.0]]), dtype=float)
            rho = float(np.mean(corr[np.triu_indices_from(corr, k=1)]))
        else:
            df = 4.0
            rho = 0.35
        arg = -np.sqrt((df + 1.0) * (1.0 - rho) / max(1.0 + rho, 1e-9))
        return float(2.0 * stats.t.cdf(arg, df + 1.0))
    return float("nan")


def gaussian_copula_uniforms(
    n_scenarios: int,
    n_crops: int,
    corr: Optional[np.ndarray],
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample uniforms from a Gaussian copula."""

    if corr is None:
        corr = np.full((n_crops, n_crops), 0.35)
        np.fill_diagonal(corr, 1.0)
    corr = validate_correlation_matrix(corr, n_crops)
    draws = rng.multivariate_normal(np.zeros(n_crops), corr, size=n_scenarios)
    uniforms = stats.norm.cdf(draws)
    return np.clip(uniforms, 1e-9, 1.0 - 1e-9)


def clayton_copula_uniforms(
    n_scenarios: int,
    n_crops: int,
    theta: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample uniforms from an exchangeable Clayton copula."""

    theta = float(theta)
    if not np.isfinite(theta):
        raise ValueError("Clayton theta must be finite")
    if theta <= 1e-8:
        return rng.uniform(1e-9, 1.0 - 1e-9, size=(n_scenarios, n_crops))
    frailty = rng.gamma(shape=1.0 / theta, scale=1.0, size=n_scenarios)
    exponentials = rng.exponential(scale=1.0, size=(n_scenarios, n_crops))
    uniforms = (1.0 + exponentials / frailty[:, None]) ** (-1.0 / theta)
    return np.clip(uniforms, 1e-9, 1.0 - 1e-9)


def t_copula_uniforms(
    n_scenarios: int,
    n_crops: int,
    corr: Optional[np.ndarray],
    df: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample uniforms from a Student-t copula."""

    if corr is None:
        corr = np.full((n_crops, n_crops), 0.35)
        np.fill_diagonal(corr, 1.0)
    corr = validate_correlation_matrix(corr, n_crops)
    if not np.isfinite(df) or float(df) <= 2.0:
        raise ValueError("Student-t copula df must exceed 2")
    normals = rng.multivariate_normal(np.zeros(n_crops), corr, size=n_scenarios)
    chi2 = rng.chisquare(df, size=n_scenarios)
    t_draws = normals / np.sqrt(chi2[:, None] / df)
    uniforms = stats.t.cdf(t_draws, df=df)
    return np.clip(uniforms, 1e-9, 1.0 - 1e-9)


def sample_copula_uniforms(
    n_scenarios: int,
    n_crops: int,
    copula_type: str,
    copula_param: Any,
    rng: np.random.Generator,
) -> np.ndarray:
    """Dispatch copula sampling by name."""

    if int(n_scenarios) <= 0 or int(n_crops) <= 0:
        raise ValueError("n_scenarios and n_crops must be positive")
    normalized = copula_type.lower().replace("_", "-")
    if normalized in {"gaussian", "normal"}:
        corr = copula_param if copula_param is not None else None
        return gaussian_copula_uniforms(n_scenarios, n_crops, corr, rng)
    if normalized == "clayton":
        return clayton_copula_uniforms(n_scenarios, n_crops, float(copula_param), rng)
    if normalized in {"t", "student-t", "t-copula"}:
        param = copula_param or {}
        corr = param.get("corr") if isinstance(param, dict) else None
        df = float(param.get("df", 4)) if isinstance(param, dict) else 4.0
        return t_copula_uniforms(n_scenarios, n_crops, corr, df, rng)
    raise ValueError(f"Unsupported copula_type: {copula_type}")


def copula_metadata(copula_type: str, copula_param: Any) -> CopulaMetadata:
    return CopulaMetadata(
        copula_type=str(copula_type),
        parameter=copula_param,
        lower_tail_dependence=lower_tail_dependence(copula_type, copula_param),
        ordering_scope=(
            "WITHIN_NAMED_FAMILY_ONLY; scalar tail dependence is not a cross-family order"
        ),
    )
