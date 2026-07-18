"""Deterministic parser for the governed NASS 2024 Crop Production Summary."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SNAPSHOT = ROOT / "data/raw/usda_nass/crop_production_2024_summary.txt"
YEARS = (2022, 2023, 2024)
TABLE_TITLES = {
    "corn": "Corn Area Planted for All Purposes and Harvested for Grain, Yield, and Production -",
    "soybeans": "Soybeans for Beans Area Planted and Harvested, Yield, and Production - States and",
    "winter_wheat": "Winter Wheat Area Planted and Harvested, Yield, and Production - States and",
}
VALUE_RE = re.compile(r"\(NA\)|\(D\)|\(Z\)|-?\d[\d,]*(?:\.\d+)?")
ROW_RE = re.compile(r"^([A-Za-z][A-Za-z ]*?)(?:\s+\d/)?\s*(?:\.+)?\s*:\s*(.+)$")


def _numeric(token: str) -> float:
    if token in {"(NA)", "(D)", "(Z)"}:
        return np.nan
    return float(token.replace(",", ""))


def _table_starts(lines: list[str], title: str) -> tuple[int, int]:
    candidates = []
    for index, line in enumerate(lines):
        if not line.startswith(title):
            continue
        heading = " ".join(lines[index:index + 3])
        if "2022-2024" in heading and index > 190:
            candidates.append((index, "(continued)" in heading))
    area = next((index for index, continued in candidates if not continued), None)
    crop_yield = next((index for index, continued in candidates if continued), None)
    if area is None or crop_yield is None:
        raise ValueError(f"could not locate both NASS table panels: {title}")
    return area, crop_yield


def _parse_panel(lines: list[str], start: int) -> Dict[str, list[float]]:
    parsed: Dict[str, list[float]] = {}
    for line in lines[start:start + 140]:
        match = ROW_RE.match(line)
        if not match:
            continue
        state = re.sub(r"\s+", " ", match.group(1)).strip()
        values = VALUE_RE.findall(match.group(2))
        if len(values) < 6 or state in {"State", "States"}:
            continue
        parsed[state] = [_numeric(value) for value in values[:6]]
        if state == "United States":
            break
    if "United States" not in parsed:
        raise ValueError("NASS table panel does not contain United States total")
    return parsed


def parse_nass_state_crop_summary(path: Path = DEFAULT_SNAPSHOT) -> pd.DataFrame:
    # The official text extract is primarily ASCII but contains a small
    # number of Latin-1 bytes in unrelated tables.
    lines = path.read_text(encoding="latin-1").splitlines()
    rows = []
    for crop, title in TABLE_TITLES.items():
        area_start, yield_start = _table_starts(lines, title)
        areas = _parse_panel(lines, area_start)
        yields = _parse_panel(lines, yield_start)
        for state in sorted(set(areas) | set(yields)):
            if state not in areas or state not in yields:
                raise ValueError(f"area/yield state mismatch for {crop}: {state}")
            for year_index, year in enumerate(YEARS):
                rows.append({
                    "state": state,
                    "year": year,
                    "crop": crop,
                    "planted_acres_1000": areas[state][year_index],
                    "yield_bushels_per_acre": yields[state][year_index],
                    "source_path": path.relative_to(ROOT).as_posix(),
                    "source_table": title.rstrip(" -"),
                    "source_unit_acres": "1,000 acres",
                    "source_unit_yield": "bushels per acre",
                })
    frame = pd.DataFrame(rows).sort_values(["state", "year", "crop"]).reset_index(drop=True)
    if frame.duplicated(["state", "year", "crop"]).any():
        raise ValueError("duplicate NASS state-year-crop row")
    return frame


def complete_state_year_sample(frame: pd.DataFrame, crops: Iterable[str]) -> pd.DataFrame:
    crops = list(crops)
    states = frame.loc[frame["state"].ne("United States") & frame["crop"].isin(crops)].copy()
    states = states.dropna(subset=["planted_acres_1000", "yield_bushels_per_acre"])
    counts = states.groupby(["state", "year"])["crop"].nunique()
    complete_keys = counts.loc[counts.eq(len(crops))].index
    result = states.set_index(["state", "year"]).loc[complete_keys].reset_index()
    result = result.loc[result["crop"].isin(crops)].sort_values(["state", "year", "crop"])
    if result.groupby(["state", "year"])["crop"].nunique().ne(len(crops)).any():
        raise ValueError("complete-case restriction failed")
    return result.reset_index(drop=True)
