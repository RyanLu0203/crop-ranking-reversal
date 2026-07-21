"""Synthetic accounting utilities for GOAL-14 theorem checks.

These functions validate mathematical identities only. They do not generate
paper evidence or calibrated crop results.
"""

from __future__ import annotations

from itertools import combinations
from math import factorial
from typing import Iterable, Mapping, Sequence

import numpy as np


def pairwise_pressure_decomposition(
    mean_profit: Iterable[float],
    tail_subgradient: Iterable[float],
    risk_dual: float,
    costs: Iterable[float],
    budget_dual: float,
    shared_matrix: np.ndarray,
    shared_duals: Iterable[float],
    lower_bound_duals: Iterable[float],
    upper_bound_duals: Iterable[float],
    i: int,
    j: int,
) -> dict[str, float]:
    """Return the canonical currency-per-acre pairwise pressure ledger."""

    mu = np.asarray(list(mean_profit), dtype=float)
    d = np.asarray(list(tail_subgradient), dtype=float)
    c = np.asarray(list(costs), dtype=float)
    lower = np.asarray(list(lower_bound_duals), dtype=float)
    upper = np.asarray(list(upper_bound_duals), dtype=float)
    matrix = np.asarray(shared_matrix, dtype=float)
    eta = np.asarray(list(shared_duals), dtype=float)
    n = mu.size
    if any(array.shape != (n,) for array in (d, c, lower, upper)):
        raise ValueError("crop-indexed pressure inputs must have the same length")
    if matrix.ndim != 2 or matrix.shape[1] != n or eta.shape != (matrix.shape[0],):
        raise ValueError("shared matrix and shared dual dimensions do not agree")
    if not 0 <= i < n or not 0 <= j < n or i == j:
        raise ValueError("i and j must be distinct valid crop indices")
    if not all(np.isfinite(array).all() for array in (mu, d, c, lower, upper, matrix, eta)):
        raise ValueError("pressure inputs must be finite")
    if min(float(risk_dual), float(budget_dual), *eta, *lower, *upper) < 0:
        raise ValueError("canonical inequality and bound multipliers must be nonnegative")

    shared_normal = matrix.T @ eta
    margin = float(mu[i] - mu[j])
    risk = float(risk_dual * (d[i] - d[j]))
    budget = float(budget_dual * (c[i] - c[j]))
    shared = float(shared_normal[i] - shared_normal[j])
    boundary = float(-(lower[i] - lower[j]) + (upper[i] - upper[j]))
    residual = float(margin - risk - budget - shared - boundary)
    return {
        "margin_pressure": margin,
        "tail_risk_pressure": risk,
        "budget_pressure": budget,
        "shared_pressure": shared,
        "boundary_pressure": boundary,
        "stationarity_residual": residual,
    }


def _all_subsets(blocks: Sequence[str]) -> list[frozenset[str]]:
    return [
        frozenset(subset)
        for size in range(len(blocks) + 1)
        for subset in combinations(blocks, size)
    ]


def shapley_vector_attribution(
    values: Mapping[frozenset[str], Iterable[float]],
    blocks: Sequence[str],
) -> dict[str, np.ndarray]:
    """Compute all-subset Shapley attribution for a selected outcome vector."""

    ordered_blocks = tuple(map(str, blocks))
    if not ordered_blocks or len(ordered_blocks) != len(set(ordered_blocks)):
        raise ValueError("blocks must be non-empty and unique")
    expected = set(_all_subsets(ordered_blocks))
    if set(values) != expected:
        missing = sorted(expected - set(values), key=lambda item: (len(item), sorted(item)))
        extra = sorted(set(values) - expected, key=lambda item: (len(item), sorted(item)))
        raise ValueError(f"subset lattice mismatch: missing={missing}; extra={extra}")
    vectors = {key: np.asarray(list(value), dtype=float) for key, value in values.items()}
    shapes = {vector.shape for vector in vectors.values()}
    if len(shapes) != 1 or not all(vector.ndim == 1 for vector in vectors.values()):
        raise ValueError("every selected subset outcome must be one same-length vector")
    if not all(np.isfinite(vector).all() for vector in vectors.values()):
        raise ValueError("selected subset outcomes must be finite")

    k = len(ordered_blocks)
    result: dict[str, np.ndarray] = {}
    for block in ordered_blocks:
        contribution = np.zeros_like(vectors[frozenset()], dtype=float)
        others = [candidate for candidate in ordered_blocks if candidate != block]
        for subset in _all_subsets(others):
            size = len(subset)
            weight = factorial(size) * factorial(k - size - 1) / factorial(k)
            contribution += weight * (
                vectors[subset | {block}] - vectors[subset]
            )
        result[block] = contribution
    return result


def interaction_cross_difference(
    low_info_low_flex: float,
    high_info_low_flex: float,
    low_info_high_flex: float,
    high_info_high_flex: float,
) -> float:
    """Return the finite information-by-flexibility cross-difference."""

    values = np.asarray(
        [low_info_low_flex, high_info_low_flex, low_info_high_flex, high_info_high_flex],
        dtype=float,
    )
    if not np.isfinite(values).all():
        raise ValueError("interaction values must be finite")
    return float((values[3] - values[2]) - (values[1] - values[0]))
