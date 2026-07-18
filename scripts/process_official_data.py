#!/usr/bin/env python3
"""Build the frozen U.S.-total crop-year panel from official raw snapshots."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
DEFAULT_OUTPUT = ROOT / "data/processed/canonical_crop_year_panel.csv"
YEARS = range(1998, 2025)
ERS_FILES = {
    "corn": RAW / "usda_ers/corn_2026-05-01.csv",
    "soybeans": RAW / "usda_ers/soybeans_2026-05-01.csv",
    "wheat": RAW / "usda_ers/wheat_2026-05-01.csv",
}
ITEMS = {
    "yield_bushels_per_planted_acre": "Yield",
    "harvest_price_usd_per_bushel": "Price",
    "operating_cost_usd_per_planted_acre": "Total, operating costs",
    "total_cost_usd_per_planted_acre": "Total, costs listed",
    "enterprise_size_planted_acres": "Enterprise size",
    "dryland_share_percent": "Dryland",
    "irrigated_share_percent": "Irrigated",
}
FIELDS = [
    "crop", "year", "geography", "ers_survey_base_year",
    *ITEMS,
    "primary_margin_nominal_usd_per_planted_acre",
    "cpi_u_annual_index", "cpi_u_deflator_to_2024",
    "primary_margin_real_2024_usd_per_planted_acre",
    "annual_precipitation_inches", "annual_mean_temperature_f",
]


def fmt(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.000001')):f}"


def read_ers(path: Path) -> tuple[dict[int, dict[str, str]], dict[int, str]]:
    selected: dict[int, dict[str, str]] = defaultdict(dict)
    bases: dict[int, str] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            year = int(row["Year"])
            if row["Region"] != "U.S. total" or year not in YEARS:
                continue
            item = row["Item"].strip()
            for field, wanted in ITEMS.items():
                if item == wanted:
                    if field in selected[year]:
                        raise ValueError(f"duplicate ERS value: {path.name}:{year}:{field}")
                    selected[year][field] = row["Value"]
                    bases[year] = row["Survey base year"]
    return dict(selected), bases


def read_noaa(path: Path) -> dict[int, Decimal]:
    values: dict[int, Decimal] = {}
    with path.open(encoding="utf-8") as handle:
        lines = [line for line in handle if not line.startswith("#")]
    for row in csv.DictReader(lines):
        year = int(row["Date"][:4])
        values[year] = Decimal(row["Value"])
    return values


def read_cpi() -> dict[int, Decimal]:
    monthly: dict[int, list[Decimal]] = defaultdict(list)
    for path in sorted((RAW / "bls").glob("cpi_u_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload["status"] != "REQUEST_SUCCEEDED":
            raise ValueError(f"BLS request failed in {path.name}")
        series = payload["Results"]["series"]
        if len(series) != 1 or series[0]["seriesID"] != "CUUR0000SA0":
            raise ValueError(f"unexpected BLS series in {path.name}")
        for row in series[0]["data"]:
            year = int(row["year"])
            if year in YEARS and row["period"].startswith("M"):
                monthly[year].append(Decimal(row["value"]))
    annual: dict[int, Decimal] = {}
    for year in YEARS:
        if len(monthly[year]) != 12:
            raise ValueError(f"expected 12 CPI months for {year}, got {len(monthly[year])}")
        annual[year] = sum(monthly[year]) / Decimal(12)
    return annual


def build_rows() -> list[dict[str, str]]:
    precipitation = read_noaa(RAW / "noaa_ncei/conus_annual_precipitation_1998-2024.csv")
    temperature = read_noaa(RAW / "noaa_ncei/conus_annual_temperature_1998-2024.csv")
    cpi = read_cpi()
    cpi_base = cpi[2024]
    output: list[dict[str, str]] = []
    for crop, path in ERS_FILES.items():
        values, bases = read_ers(path)
        for year in YEARS:
            missing = set(ITEMS) - set(values.get(year, {}))
            if missing:
                raise ValueError(f"missing ERS values: {crop}:{year}:{sorted(missing)}")
            current = values[year]
            price = Decimal(current["harvest_price_usd_per_bushel"])
            crop_yield = Decimal(current["yield_bushels_per_planted_acre"])
            operating = Decimal(current["operating_cost_usd_per_planted_acre"])
            margin = price * crop_yield - operating
            deflator = cpi_base / cpi[year]
            row = {
                "crop": crop,
                "year": str(year),
                "geography": "United States",
                "ers_survey_base_year": bases[year],
                **{field: fmt(Decimal(current[field])) for field in ITEMS},
                "primary_margin_nominal_usd_per_planted_acre": fmt(margin),
                "cpi_u_annual_index": fmt(cpi[year]),
                "cpi_u_deflator_to_2024": fmt(deflator),
                "primary_margin_real_2024_usd_per_planted_acre": fmt(margin * deflator),
                "annual_precipitation_inches": fmt(precipitation[year]),
                "annual_mean_temperature_f": fmt(temperature[year]),
            }
            output.append(row)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows = build_rows()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"panel_rows={len(rows)} crops={len(ERS_FILES)} years={len(YEARS)} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
