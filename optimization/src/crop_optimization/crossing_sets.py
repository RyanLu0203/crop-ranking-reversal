"""Crossing-set detection without imposing a unique-threshold narrative."""

from __future__ import annotations

from typing import Iterable


def crossing_set_audit(
    parameters: Iterable[float],
    reversal_states: Iterable[bool],
) -> dict[str, object]:
    points = sorted(zip(map(float, parameters), map(bool, reversal_states)))
    if len(points) < 2 or len({point for point, _ in points}) != len(points):
        raise ValueError("at least two unique parameter points are required")
    crossing_intervals: list[list[float]] = []
    for (left, left_state), (right, right_state) in zip(points[:-1], points[1:]):
        if left_state != right_state:
            crossing_intervals.append([left, right])

    regions: list[list[float]] = []
    start = None
    end = None
    for value, state in points:
        if state and start is None:
            start = end = value
        elif state:
            end = value
        elif start is not None:
            regions.append([float(start), float(end)])
            start = end = None
    if start is not None:
        regions.append([float(start), float(end)])
    return {
        "sampled_points": len(points),
        "crossing_intervals": crossing_intervals,
        "reversal_regions_on_grid": regions,
        "crossing_count": len(crossing_intervals),
        "reversal_region_count": len(regions),
        "unique_threshold_admissible": len(crossing_intervals) == 1 and len(regions) == 1,
    }
