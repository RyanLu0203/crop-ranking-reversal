"""Centralized numerical conventions for v7.1 ranking-reversal audits."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "numerical_tolerances.yaml"


def load_tolerances(path: Path | None = None) -> Dict[str, Any]:
    """Load the single source of truth for numerical tolerances."""

    config_path = path or DEFAULT_CONFIG_PATH
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def primary_tolerances(path: Path | None = None) -> Dict[str, float]:
    """Return primary tolerance values as floats."""

    primary = load_tolerances(path)["primary"]
    return {key: float(value) for key, value in primary.items()}


def score_tied(score_high: float, score_low: float, tolerance: float | None = None) -> bool:
    tol = primary_tolerances()["score_tie_tolerance_normalized"] if tolerance is None else float(tolerance)
    return (float(score_high) - float(score_low)) <= tol


def acreage_tied(acres_a: float, acres_b: float, tolerance: float | None = None) -> bool:
    tol = primary_tolerances()["acreage_tie_tolerance_acres"] if tolerance is None else float(tolerance)
    return abs(float(acres_a) - float(acres_b)) <= tol


def near_zero_acreage(acres: float, tolerance: float | None = None) -> bool:
    tol = primary_tolerances()["near_zero_acreage_tolerance_acres"] if tolerance is None else float(tolerance)
    return float(acres) <= tol


def pairwise_reversal(
    high_rank_acres: float,
    low_rank_acres: float,
    score_high: float | None = None,
    score_low: float | None = None,
    acreage_tolerance: float | None = None,
    score_tolerance: float | None = None,
) -> bool:
    """Classify pairwise reversal using centralized score and acreage ties."""

    if score_high is not None and score_low is not None and score_tied(score_high, score_low, score_tolerance):
        return False
    tol = primary_tolerances()["acreage_tie_tolerance_acres"] if acreage_tolerance is None else float(acreage_tolerance)
    return float(low_rank_acres) > float(high_rank_acres) + tol


def top_rank_reversal(top_acres: float, other_acres: list[float], acreage_tolerance: float | None = None) -> bool:
    tol = primary_tolerances()["acreage_tie_tolerance_acres"] if acreage_tolerance is None else float(acreage_tolerance)
    return any(float(value) > float(top_acres) + tol for value in other_acres)


def strong_reversal(top_acres: float, other_acres: list[float], near_zero_tolerance: float | None = None) -> bool:
    tol = primary_tolerances()["near_zero_acreage_tolerance_acres"] if near_zero_tolerance is None else float(near_zero_tolerance)
    return float(top_acres) <= tol and any(float(value) > tol for value in other_acres)
