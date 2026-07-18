"""Empirical data provenance, coverage, panel construction, and sample selection."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import yaml


QUICKSTATS_BASE = "https://quickstats.nass.usda.gov"
ERS_BASE = "https://www.ers.usda.gov"

EMPIRICAL_YEAR_MIN = 2005
EMPIRICAL_YEAR_MAX = 2025

CROP_QUERIES: Dict[str, Dict[str, str]] = {
    "Corn": {"commodity_desc": "CORN"},
    "Soybean": {"commodity_desc": "SOYBEANS"},
    "Winter Wheat": {"commodity_desc": "WHEAT", "class_desc": "WINTER"},
    "Oats": {"commodity_desc": "OATS"},
    "Barley": {"commodity_desc": "BARLEY"},
    "Sorghum": {"commodity_desc": "SORGHUM"},
}

ERS_COST_URLS = {
    "Corn": "https://www.ers.usda.gov/media/4962/corn.csv?v=55281",
    "Soybean": "https://www.ers.usda.gov/media/4976/soybeans.csv?v=23654",
    "Winter Wheat": "https://www.ers.usda.gov/media/4978/wheat.csv?v=37534",
    "Oats": "https://www.ers.usda.gov/media/4974/oats.csv?v=68837",
    "Barley": "https://www.ers.usda.gov/media/4966/barley.csv?v=38316",
    "Sorghum": "https://www.ers.usda.gov/media/4972/sorghum.csv?v=69137",
}

NASS_CROP_LABELS = {
    "CORN": "Corn",
    "SOYBEANS": "Soybean",
    "WHEAT": "Winter Wheat",
    "OATS": "Oats",
    "BARLEY": "Barley",
    "SORGHUM": "Sorghum",
}

HEARTLAND_STATES = {
    "ILLINOIS",
    "INDIANA",
    "IOWA",
    "MISSOURI",
    "OHIO",
}


@dataclass
class RawFileRecord:
    file_id: str
    source_id: str
    filename: str
    retrieval_timestamp: str
    sha256: str
    bytes: int
    geographic_level: str
    temporal_level: str
    variable_family: str
    notes: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "file_id": self.file_id,
            "source_id": self.source_id,
            "filename": self.filename,
            "retrieval_timestamp": self.retrieval_timestamp,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "geographic_level": self.geographic_level,
            "temporal_level": self.temporal_level,
            "variable_family": self.variable_family,
            "notes": self.notes,
        }


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_empirical_dirs(project_root: Path) -> None:
    for rel in [
        "data/raw/yield",
        "data/raw/acreage",
        "data/raw/price",
        "data/raw/cost",
        "data/raw/suitability",
        "data/interim",
        "data/processed",
        "data/metadata",
        "outputs/tables/full",
        "outputs/tables/main",
        "outputs/logs",
    ]:
        (project_root / rel).mkdir(parents=True, exist_ok=True)


def read_source_registry(project_root: Path) -> Dict[str, object]:
    path = project_root / "configs" / "empirical_data_sources.yaml"
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def quickstats_query_export(
    params: Dict[str, object],
    destination: Path,
    metadata_path: Path,
) -> Dict[str, object]:
    """Download an official QuickStats query-tool CSV export.

    The public API requires a key in this environment, so this uses the same
    official query-tool workflow as the browser: row count, UUID encode, then
    spreadsheet CSV download. Queries must remain under the 50,000 row limit.
    """

    destination.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = urllib.parse.urlencode(params, doseq=True).encode()
    headers = {"User-Agent": "Mozilla/5.0 empirical-pilot", "Content-Type": "application/x-www-form-urlencoded"}

    def post_json(path: str) -> object:
        req = urllib.request.Request(f"{QUICKSTATS_BASE}{path}", data=encoded, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))

    row_counts = post_json("/row_counts")
    row_count = int(row_counts.get("rowcnt", 0))
    if row_count > 50000:
        raise ValueError(f"QuickStats query exceeds 50,000 row export limit: {row_count} rows for {params}")
    uuid = str(post_json("/uuid/encode")).strip('"')
    url = f"{QUICKSTATS_BASE}/data/spreadsheet/{uuid}.csv"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 empirical-pilot"})
    with urllib.request.urlopen(req, timeout=180) as response:
        content = response.read()
    destination.write_bytes(content)
    metadata = {
        "source": "USDA NASS QuickStats official query-tool export",
        "query_params": params,
        "row_count": row_count,
        "total_row_count": int(row_counts.get("totalrowcnt", 0)),
        "uuid": uuid,
        "download_url": url,
        "retrieval_timestamp": utc_timestamp(),
        "sha256": sha256_file(destination),
        "bytes": destination.stat().st_size,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def download_url(url: str, destination: Path, metadata_path: Path, source_note: str) -> Dict[str, object]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 empirical-pilot"})
    with urllib.request.urlopen(req, timeout=120) as response:
        content = response.read()
        content_type = response.headers.get("content-type")
    destination.write_bytes(content)
    metadata = {
        "source": source_note,
        "download_url": url,
        "retrieval_timestamp": utc_timestamp(),
        "content_type": content_type,
        "sha256": sha256_file(destination),
        "bytes": destination.stat().st_size,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def _raw_record(
    file_id: str,
    source_id: str,
    path: Path,
    metadata: Dict[str, object],
    geographic_level: str,
    variable_family: str,
    notes: str,
) -> RawFileRecord:
    return RawFileRecord(
        file_id=file_id,
        source_id=source_id,
        filename=str(path),
        retrieval_timestamp=str(metadata["retrieval_timestamp"]),
        sha256=str(metadata["sha256"]),
        bytes=int(metadata["bytes"]),
        geographic_level=geographic_level,
        temporal_level="annual",
        variable_family=variable_family,
        notes=notes,
    )


def download_raw_sources(
    project_root: Path,
    crops: Optional[Sequence[str]] = None,
    start_year: int = EMPIRICAL_YEAR_MIN,
    end_year: int = EMPIRICAL_YEAR_MAX,
    force: bool = False,
) -> pd.DataFrame:
    """Download official raw CSVs and write the raw manifest."""

    ensure_empirical_dirs(project_root)
    crops = list(crops or CROP_QUERIES)
    records: List[RawFileRecord] = []

    for crop in crops:
        query_base = {
            "source_desc": "SURVEY",
            "sector_desc": "CROPS",
            "commodity_desc": CROP_QUERIES[crop]["commodity_desc"],
            "year__GE": str(start_year),
            "year__LE": str(end_year),
        }
        if "class_desc" in CROP_QUERIES[crop]:
            query_base["class_desc"] = CROP_QUERIES[crop]["class_desc"]
        safe_crop = re.sub(r"[^a-z0-9]+", "_", crop.lower()).strip("_")

        for stat, family, directory, source_id, geo in [
            ("YIELD", "yield", "yield", "nass_quickstats_county_yield", "county"),
            ("AREA PLANTED", "acreage_planted", "acreage", "nass_quickstats_county_acreage", "county"),
            ("AREA HARVESTED", "acreage_harvested", "acreage", "nass_quickstats_county_acreage", "county"),
        ]:
            params = dict(query_base)
            params.update({"statisticcat_desc": stat, "agg_level_desc": "COUNTY"})
            path = project_root / "data" / "raw" / directory / f"nass_{family}_{safe_crop}_{start_year}_{end_year}.csv"
            meta_path = path.with_suffix(".metadata.json")
            if force or not path.exists():
                metadata = quickstats_query_export(params, path, meta_path)
            else:
                metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            records.append(_raw_record(f"raw_{family}_{safe_crop}", source_id, path, metadata, geo, family, str(params)))

        params = dict(query_base)
        params.update({"statisticcat_desc": "PRICE RECEIVED", "agg_level_desc": "STATE"})
        path = project_root / "data" / "raw" / "price" / f"nass_price_{safe_crop}_{start_year}_{end_year}.csv"
        meta_path = path.with_suffix(".metadata.json")
        if force or not path.exists():
            metadata = quickstats_query_export(params, path, meta_path)
        else:
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        records.append(_raw_record(f"raw_price_{safe_crop}", "nass_quickstats_state_price", path, metadata, "state", "price", str(params)))

        if crop in ERS_COST_URLS:
            path = project_root / "data" / "raw" / "cost" / f"ers_costs_{safe_crop}.csv"
            meta_path = path.with_suffix(".metadata.json")
            if force or not path.exists():
                metadata = download_url(
                    ERS_COST_URLS[crop],
                    path,
                    meta_path,
                    "USDA ERS Commodity Costs and Returns official CSV download",
                )
            else:
                metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            records.append(
                _raw_record(
                    f"raw_cost_{safe_crop}",
                    "ers_commodity_costs_returns",
                    path,
                    metadata,
                    "region",
                    "cost",
                    f"ERS operating-cost CSV for {crop}",
                )
            )

    manifest = pd.DataFrame([record.to_dict() for record in records])
    manifest.to_csv(project_root / "data" / "metadata" / "raw_file_manifest.csv", index=False)
    write_data_source_registry(project_root, manifest)
    return manifest


def parse_numeric_value(value: object) -> float:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan
    text = str(value).strip()
    if text in {"", "(D)", "(NA)", "NA", "--"}:
        return np.nan
    text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return np.nan


def standardize_crop_names(series: pd.Series) -> pd.Series:
    return series.astype(str).str.upper().map(NASS_CROP_LABELS).fillna(series)


def standardize_geographies(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["state"] = out["State"].astype(str).str.title()
    out["state_upper"] = out["State"].astype(str).str.upper()
    if "County" in out:
        out["county"] = out["County"].astype(str).str.title()
        county_ansi = out["County ANSI"].fillna("").astype(str).str.replace(r"\.0$", "", regex=True)
        state_ansi = out["State ANSI"].fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(2)
        out["county_fips"] = np.where(
            county_ansi.str.len() > 0,
            state_ansi + county_ansi.str.zfill(3),
            pd.NA,
        )
    return out


def convert_units(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["unit_conversion_flag"] = False
    return out


def _load_raw_family(project_root: Path, directory: str, prefix: str) -> pd.DataFrame:
    frames = []
    for path in sorted((project_root / "data" / "raw" / directory).glob(f"{prefix}*.csv")):
        df = pd.read_csv(path, dtype=str)
        df["raw_file"] = str(path)
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_raw_yield_data(project_root: Path) -> pd.DataFrame:
    return _load_raw_family(project_root, "yield", "nass_yield")


def load_raw_price_data(project_root: Path) -> pd.DataFrame:
    return _load_raw_family(project_root, "price", "nass_price")


def load_raw_cost_data(project_root: Path) -> pd.DataFrame:
    return _load_raw_family(project_root, "cost", "ers_costs")


def load_raw_acreage_data(project_root: Path) -> pd.DataFrame:
    return _load_raw_family(project_root, "acreage", "nass_acreage")


def _nass_base(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = standardize_geographies(df)
    out["year"] = pd.to_numeric(out["Year"], errors="coerce").astype("Int64")
    out["crop"] = standardize_crop_names(out["Commodity"])
    out["value_numeric"] = out["Value"].map(parse_numeric_value)
    out["data_item"] = out["Data Item"].astype(str)
    out["period"] = out["Period"].astype(str)
    out["domain"] = out["Domain"].astype(str)
    out["domain_category"] = out["Domain Category"].astype(str)
    out["missingness_flag"] = out["value_numeric"].isna()
    return convert_units(out)


def prepare_yield_data(raw_yield: pd.DataFrame) -> pd.DataFrame:
    df = _nass_base(raw_yield)
    if df.empty:
        return pd.DataFrame()
    out = df.loc[
        df["county_fips"].notna()
        & df["period"].eq("YEAR")
        & df["domain"].eq("TOTAL")
        & df["domain_category"].eq("NOT SPECIFIED")
    ].copy()
    return out[
        [
            "state",
            "state_upper",
            "county",
            "county_fips",
            "year",
            "crop",
            "value_numeric",
            "data_item",
            "raw_file",
            "missingness_flag",
            "unit_conversion_flag",
        ]
    ].rename(columns={"value_numeric": "yield_per_acre", "data_item": "yield_unit"})


def prepare_acreage_data(raw_acreage: pd.DataFrame) -> pd.DataFrame:
    df = _nass_base(raw_acreage)
    if df.empty:
        return pd.DataFrame()
    df = df.loc[
        df["county_fips"].notna()
        & df["period"].eq("YEAR")
        & df["domain"].eq("TOTAL")
        & df["domain_category"].eq("NOT SPECIFIED")
    ].copy()
    df["acreage_variable"] = np.where(df["data_item"].str.contains("PLANTED", case=False, na=False), "acreage_planted", "acreage_harvested")
    wide = (
        df.pivot_table(
            index=["state", "state_upper", "county", "county_fips", "year", "crop"],
            columns="acreage_variable",
            values="value_numeric",
            aggfunc="first",
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    for col in ["acreage_planted", "acreage_harvested"]:
        if col not in wide:
            wide[col] = np.nan
    return wide


def prepare_price_data(raw_price: pd.DataFrame) -> pd.DataFrame:
    df = _nass_base(raw_price)
    if df.empty:
        return pd.DataFrame()
    out = df.loc[
        df["period"].isin(["MARKETING YEAR", "YEAR"])
        & df["domain"].eq("TOTAL")
        & df["domain_category"].eq("NOT SPECIFIED")
        & df["data_item"].str.contains(r"\$ / BU", case=False, na=False)
    ].copy()
    out = out.sort_values(["state", "year", "crop", "period"]).drop_duplicates(["state", "state_upper", "year", "crop"])
    return out[
        [
            "state",
            "state_upper",
            "year",
            "crop",
            "value_numeric",
            "data_item",
            "raw_file",
            "missingness_flag",
            "unit_conversion_flag",
        ]
    ].rename(columns={"value_numeric": "price", "data_item": "price_unit"})


def _state_to_ers_region(state_upper: str) -> str:
    if state_upper in HEARTLAND_STATES:
        return "Heartland"
    return "U.S. total"


def prepare_cost_data(raw_cost: pd.DataFrame) -> pd.DataFrame:
    if raw_cost.empty:
        return pd.DataFrame()
    df = raw_cost.copy()
    df["crop"] = df["Commodity"].replace({"Soybean": "Soybean", "Corn": "Corn", "Wheat": "Winter Wheat"})
    df.loc[df["Commodity"].eq("Wheat"), "crop"] = "Winter Wheat"
    df["year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["cost_per_acre"] = df["Value"].map(parse_numeric_value)
    df = df.loc[
        (df["Category"].eq("Operating costs"))
        & (df["Item"].eq("Total, operating costs"))
        & (df["Units"].eq("dollars per planted acre"))
    ].copy()
    return df[["crop", "year", "Region", "cost_per_acre", "Units", "raw_file"]].rename(
        columns={"Region": "cost_region", "Units": "cost_unit"}
    )


def merge_empirical_sources(yield_df: pd.DataFrame, acreage_df: pd.DataFrame, price_df: pd.DataFrame, cost_df: pd.DataFrame) -> pd.DataFrame:
    panel = yield_df.merge(
        acreage_df,
        on=["state", "state_upper", "county", "county_fips", "year", "crop"],
        how="left",
    )
    panel = panel.merge(price_df, on=["state", "state_upper", "year", "crop"], how="left", suffixes=("", "_price"))
    panel["target_cost_region"] = panel["state_upper"].map(_state_to_ers_region)
    cost_region = cost_df.rename(columns={"cost_region": "target_cost_region"})
    panel = panel.merge(cost_region, on=["crop", "year", "target_cost_region"], how="left")
    missing_cost = panel["cost_per_acre"].isna()
    if missing_cost.any():
        us_cost = cost_df.loc[cost_df["cost_region"].eq("U.S. total")].drop(columns=["cost_region"]).rename(
            columns={"cost_per_acre": "us_cost_per_acre", "cost_unit": "us_cost_unit", "raw_file": "us_cost_raw_file"}
        )
        panel = panel.merge(us_cost, on=["crop", "year"], how="left")
        panel.loc[missing_cost, "cost_per_acre"] = panel.loc[missing_cost, "us_cost_per_acre"]
        panel.loc[missing_cost, "cost_unit"] = panel.loc[missing_cost, "us_cost_unit"]
        panel.loc[missing_cost, "raw_file_y"] = panel.loc[missing_cost, "us_cost_raw_file"]
        panel.loc[missing_cost, "target_cost_region"] = "U.S. total"
    panel["price_geography_level"] = "state"
    panel["cost_geography_level"] = np.where(panel["target_cost_region"].eq("U.S. total"), "national", "ers_region")
    panel["yield_source_id"] = "nass_quickstats_county_yield"
    panel["price_source_id"] = "nass_quickstats_state_price"
    panel["cost_source_id"] = "ers_commodity_costs_returns"
    panel["price_imputed"] = False
    panel["cost_imputed"] = False
    return panel


def construct_profit_per_acre(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    unit_ok = (
        out["yield_unit"].astype(str).str.contains("BU / ACRE", case=False, na=False)
        & out["price_unit"].astype(str).str.contains(r"\$ / BU", case=False, na=False)
        & out["cost_unit"].astype(str).str.contains("dollars per planted acre", case=False, na=False)
    )
    out["unit_conversion_flag"] = False
    out["unit_compatible"] = unit_ok
    out["profit_per_acre"] = np.where(
        unit_ok,
        out["price"].astype(float) * out["yield_per_acre"].astype(float) - out["cost_per_acre"].astype(float),
        np.nan,
    )
    out["missingness_flag"] = out[["yield_per_acre", "price", "cost_per_acre", "acreage_planted"]].isna().any(axis=1)
    out["quality_warning"] = ""
    out.loc[~unit_ok, "quality_warning"] = "unit mismatch prevents profit calculation"
    out.loc[out["price"].isna(), "quality_warning"] = out["quality_warning"].where(
        out["quality_warning"].eq(""),
        out["quality_warning"] + "; ",
    ) + "missing state price"
    out.loc[out["cost_per_acre"].isna(), "quality_warning"] = out["quality_warning"].where(
        out["quality_warning"].eq(""),
        out["quality_warning"] + "; ",
    ) + "missing ERS cost"
    return out


def validate_empirical_panel(panel: pd.DataFrame) -> Dict[str, object]:
    required = [
        "state",
        "county",
        "county_fips",
        "year",
        "crop",
        "yield_per_acre",
        "yield_unit",
        "price",
        "price_unit",
        "cost_per_acre",
        "profit_per_acre",
        "acreage_planted",
        "suitability_score",
        "suitability_definition",
        "yield_source_id",
        "price_source_id",
        "cost_source_id",
        "price_geography_level",
        "cost_geography_level",
        "price_imputed",
        "cost_imputed",
        "unit_conversion_flag",
        "missingness_flag",
        "quality_warning",
    ]
    missing_columns = [col for col in required if col not in panel.columns]
    duplicate_keys = int(panel.duplicated(["state", "county_fips", "year", "crop"]).sum()) if not missing_columns else -1
    return {
        "missing_columns": missing_columns,
        "duplicate_county_year_crop_rows": duplicate_keys,
        "rows": int(len(panel)),
        "complete_profit_rows": int(panel["profit_per_acre"].notna().sum()) if "profit_per_acre" in panel else 0,
        "valid": not missing_columns and duplicate_keys == 0,
    }


def longest_consecutive_run(years: Iterable[int]) -> Tuple[Optional[int], Optional[int], int]:
    sorted_years = sorted({int(y) for y in years if pd.notna(y)})
    if not sorted_years:
        return None, None, 0
    best_start = cur_start = sorted_years[0]
    best_end = cur_end = sorted_years[0]
    for year in sorted_years[1:]:
        if year == cur_end + 1:
            cur_end = year
        else:
            if cur_end - cur_start > best_end - best_start:
                best_start, best_end = cur_start, cur_end
            cur_start = cur_end = year
    if cur_end - cur_start > best_end - best_start:
        best_start, best_end = cur_start, cur_end
    return best_start, best_end, best_end - best_start + 1


def coverage_audits(panel: pd.DataFrame, candidate_crop_sets: Optional[List[List[str]]] = None) -> Dict[str, pd.DataFrame]:
    complete = panel.loc[panel["profit_per_acre"].notna() & panel["acreage_planted"].notna()].copy()
    by_state_crop = (
        complete.groupby(["state", "crop"])
        .agg(
            rows=("profit_per_acre", "size"),
            counties=("county_fips", "nunique"),
            years=("year", "nunique"),
            first_year=("year", "min"),
            last_year=("year", "max"),
            mean_planted_acres=("acreage_planted", "mean"),
        )
        .reset_index()
    )
    run_rows = []
    for (state, crop), part in complete.groupby(["state", "crop"]):
        start, end, length = longest_consecutive_run(part["year"])
        run_rows.append({"state": state, "crop": crop, "longest_run_start": start, "longest_run_end": end, "longest_run_years": length})
    by_state_crop = by_state_crop.merge(pd.DataFrame(run_rows), on=["state", "crop"], how="left")

    by_county_crop = (
        complete.groupby(["state", "county", "county_fips", "crop"])
        .agg(
            rows=("profit_per_acre", "size"),
            years=("year", "nunique"),
            first_year=("year", "min"),
            last_year=("year", "max"),
            mean_planted_acres=("acreage_planted", "mean"),
        )
        .reset_index()
    )
    county_runs = []
    for keys, part in complete.groupby(["state", "county", "county_fips", "crop"]):
        start, end, length = longest_consecutive_run(part["year"])
        county_runs.append(dict(zip(["state", "county", "county_fips", "crop"], keys), longest_run_start=start, longest_run_end=end, longest_run_years=length))
    by_county_crop = by_county_crop.merge(pd.DataFrame(county_runs), on=["state", "county", "county_fips", "crop"], how="left")

    candidate_crop_sets = candidate_crop_sets or [
        ["Corn", "Soybean", "Winter Wheat"],
        ["Corn", "Soybean", "Oats"],
        ["Corn", "Soybean", "Barley"],
    ]
    overlap_rows = []
    complete_key = complete[["state", "county", "county_fips", "year", "crop", "acreage_planted"]].copy()
    for crop_set in candidate_crop_sets:
        label = " + ".join(crop_set)
        subset = complete_key.loc[complete_key["crop"].isin(crop_set)]
        counts = subset.groupby(["state", "county", "county_fips", "year"])["crop"].nunique().reset_index(name="crop_count")
        full = counts.loc[counts["crop_count"].eq(len(crop_set))]
        for state, part in full.groupby("state"):
            county_years = part.groupby("county_fips")["year"].apply(list)
            run_lengths = []
            for years in county_years:
                _, _, length = longest_consecutive_run(years)
                run_lengths.append(length)
            max_run = max(run_lengths) if run_lengths else 0
            feasible_10 = sum(length >= 10 for length in run_lengths)
            feasible_15 = sum(length >= 15 for length in run_lengths)
            start, end, length = longest_consecutive_run(part["year"])
            overlap_rows.append(
                {
                    "crop_set": label,
                    "state": state,
                    "complete_county_years": int(len(part)),
                    "complete_counties": int(part["county_fips"].nunique()),
                    "complete_years": int(part["year"].nunique()),
                    "state_longest_start": start,
                    "state_longest_end": end,
                    "state_longest_years": length,
                    "max_county_longest_years": int(max_run),
                    "counties_with_10_year_run": int(feasible_10),
                    "counties_with_15_year_run": int(feasible_15),
                }
            )
    overlap = pd.DataFrame(overlap_rows).sort_values(
        ["crop_set", "complete_counties", "max_county_longest_years"], ascending=[True, False, False]
    )
    return {
        "empirical_coverage_by_state_crop": by_state_crop,
        "empirical_coverage_by_county_crop": by_county_crop,
        "empirical_overlap_matrix": overlap,
    }


def select_empirical_sample(panel: pd.DataFrame, overlap: pd.DataFrame) -> Dict[str, object]:
    """Select a defensible pilot sample using coverage, not realized outcomes."""

    preferred = ["Corn", "Soybean", "Winter Wheat"]
    feasible = overlap.loc[
        (overlap["complete_counties"] >= 3)
        & (overlap["max_county_longest_years"] >= 10)
    ].copy()
    if feasible.empty:
        feasible = overlap.loc[overlap["complete_counties"] >= 1].copy()
    if feasible.empty:
        raise ValueError("No feasible empirical sample candidate found.")

    preferred_label = " + ".join(preferred)
    pref = feasible.loc[feasible["crop_set"].eq(preferred_label)]
    if not pref.empty:
        selected_row = pref.sort_values(["counties_with_15_year_run", "complete_counties"], ascending=False).iloc[0]
        reason = "Original manuscript crop set is feasible under coverage rules."
    else:
        selected_row = feasible.sort_values(
            ["counties_with_15_year_run", "max_county_longest_years", "complete_counties"],
            ascending=False,
        ).iloc[0]
        reason = "Original Corn/Soybean/Winter Wheat set is not feasible; selected highest-coverage alternative."

    crops = selected_row["crop_set"].split(" + ")
    state = selected_row["state"]
    complete = panel.loc[
        panel["state"].eq(state)
        & panel["crop"].isin(crops)
        & panel["profit_per_acre"].notna()
        & panel["acreage_planted"].notna()
    ].copy()
    counts = complete.groupby(["county", "county_fips", "year"])["crop"].nunique().reset_index(name="crop_count")
    full = counts.loc[counts["crop_count"].eq(len(crops))]
    county_scores = []
    for (county, fips), part in full.groupby(["county", "county_fips"]):
        start, end, length = longest_consecutive_run(part["year"])
        acreage = complete.loc[complete["county_fips"].eq(fips), "acreage_planted"].mean()
        county_scores.append({"county": county, "county_fips": fips, "start_year": start, "end_year": end, "run_years": length, "mean_planted_acres": acreage})
    counties = pd.DataFrame(county_scores).sort_values(["run_years", "mean_planted_acres"], ascending=False)
    selected_counties = counties.head(min(10, max(3, len(counties)))).copy()
    common_years = []
    for year, part in full.loc[full["county_fips"].isin(selected_counties["county_fips"])].groupby("year"):
        if part["county_fips"].nunique() == len(selected_counties):
            common_years.append(int(year))
    start, end, length = longest_consecutive_run(common_years)
    if length < 10:
        best = selected_counties.iloc[0]
        start, end, length = int(best["start_year"]), int(best["end_year"]), int(best["run_years"])
        selected_counties = selected_counties.head(1)
    return {
        "selected_states": [state],
        "selected_counties": selected_counties["county"].tolist(),
        "selected_county_fips": selected_counties["county_fips"].tolist(),
        "selected_crops": crops,
        "start_year": int(start),
        "end_year": int(end),
        "minimum_observation_threshold": 10,
        "selection_reason": reason,
        "selected_overlap_row": selected_row.to_dict(),
        "county_selection_table": selected_counties,
        "manuscript_original_design": {
            "state": "Iowa",
            "counties": 15,
            "crops": preferred,
            "years": "2005-2022",
            "window": "5-year rolling",
        },
    }


def build_empirical_panel(project_root: Path) -> Tuple[pd.DataFrame, Dict[str, object]]:
    raw_yield = load_raw_yield_data(project_root)
    raw_acreage = load_raw_acreage_data(project_root)
    raw_price = load_raw_price_data(project_root)
    raw_cost = load_raw_cost_data(project_root)
    yield_df = prepare_yield_data(raw_yield)
    acreage_df = prepare_acreage_data(raw_acreage)
    price_df = prepare_price_data(raw_price)
    cost_df = prepare_cost_data(raw_cost)
    panel = merge_empirical_sources(yield_df, acreage_df, price_df, cost_df)
    panel = construct_profit_per_acre(panel)
    panel["suitability_score"] = np.nan
    panel["suitability_definition"] = "computed_later_from_lagged_history"
    canonical = [
        "state",
        "county",
        "county_fips",
        "year",
        "crop",
        "yield_per_acre",
        "yield_unit",
        "price",
        "price_unit",
        "cost_per_acre",
        "profit_per_acre",
        "acreage_planted",
        "suitability_score",
        "suitability_definition",
        "yield_source_id",
        "price_source_id",
        "cost_source_id",
        "price_geography_level",
        "cost_geography_level",
        "price_imputed",
        "cost_imputed",
        "unit_conversion_flag",
        "missingness_flag",
        "quality_warning",
        "acreage_harvested",
        "cost_region",
    ]
    for col in canonical:
        if col not in panel:
            panel[col] = np.nan
    panel = panel[canonical].drop_duplicates(["state", "county_fips", "year", "crop"]).sort_values(["state", "county_fips", "year", "crop"])
    validation = validate_empirical_panel(panel)
    processed_csv = project_root / "data" / "processed" / "county_year_crop_panel.csv"
    panel.to_csv(processed_csv, index=False)
    try:
        panel.to_parquet(project_root / "data" / "processed" / "county_year_crop_panel.parquet", index=False)
        validation["parquet_exported"] = True
    except Exception as exc:  # pragma: no cover - depends on optional parquet engine
        validation["parquet_exported"] = False
        validation["parquet_error"] = str(exc)
    return panel, validation


def write_coverage_outputs(project_root: Path, panel: pd.DataFrame, audits: Dict[str, pd.DataFrame], sample: Dict[str, object]) -> None:
    for name, df in audits.items():
        df.to_csv(project_root / "outputs" / "tables" / "full" / f"{name}.csv", index=False)
    selected_crops = " + ".join(sample["selected_crops"])
    overlap = audits["empirical_overlap_matrix"]
    iowa_original = overlap.loc[(overlap["state"].eq("Iowa")) & (overlap["crop_set"].eq("Corn + Soybean + Winter Wheat"))]
    feasible_summary = pd.DataFrame(
        [
            {
                "question": "Is Iowa empirically feasible for Corn/Soybean/Winter Wheat?",
                "answer": "Yes" if not iowa_original.empty and int(iowa_original["counties_with_10_year_run"].max()) >= 3 else "No",
                "evidence": iowa_original.to_dict("records")[:1] if not iowa_original.empty else "No complete overlap row",
            },
            {
                "question": "Does the manuscript 15-county design exist?",
                "answer": "Yes" if not iowa_original.empty and int(iowa_original["counties_with_15_year_run"].max()) >= 15 else "No",
                "evidence": iowa_original.to_dict("records")[:1] if not iowa_original.empty else "No complete overlap row",
            },
            {
                "question": "Selected empirical pilot design",
                "answer": f"{sample['selected_states'][0]}, {len(sample['selected_counties'])} county/counties, {selected_crops}, {sample['start_year']}-{sample['end_year']}",
                "evidence": sample["selection_reason"],
            },
        ]
    )
    feasible_summary.to_csv(project_root / "outputs" / "tables" / "main" / "empirical_data_feasibility_summary.csv", index=False)


def write_sample_configs_and_logs(project_root: Path, sample: Dict[str, object], audits: Dict[str, pd.DataFrame]) -> None:
    config = {
        "selected_states": sample["selected_states"],
        "selected_counties": sample["selected_counties"],
        "selected_county_fips": sample["selected_county_fips"],
        "selected_crops": sample["selected_crops"],
        "start_year": sample["start_year"],
        "end_year": sample["end_year"],
        "inclusion_rules": [
            "county-year-crop rows must have yield, planted acreage, state price, ERS operating cost, and compatible units",
            "sample chosen by coverage and average planted acreage, not by ranking-reversal outcomes",
            "training data for decision year t use only years strictly before t",
        ],
        "exclusion_rules": [
            "rows with suppressed or missing NASS values are excluded from complete-case pilot calculations",
            "county rows without county FIPS are excluded",
            "crop alternatives are considered only when the original crop set lacks feasible overlap",
        ],
        "minimum_observation_threshold": sample["minimum_observation_threshold"],
        "rationale": sample["selection_reason"],
    }
    with (project_root / "configs" / "empirical_pilot.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)

    original = sample["manuscript_original_design"]
    body = [
        "# Empirical Sample Selection",
        "",
        "Sample selection is based on coverage, continuity, and production presence, not on whether the selected sample produces ranking reversal.",
        "",
        "## Manuscript-Original Design",
        "",
        f"- State: {original['state']}",
        f"- Counties: {original['counties']}",
        f"- Crops: {', '.join(original['crops'])}",
        f"- Years: {original['years']}",
        f"- Window: {original['window']}",
        "",
        "## Selected Empirically Feasible Design",
        "",
        f"- State(s): {', '.join(sample['selected_states'])}",
        f"- Counties: {', '.join(sample['selected_counties'])}",
        f"- Crops: {', '.join(sample['selected_crops'])}",
        f"- Years: {sample['start_year']}--{sample['end_year']}",
        f"- Rationale: {sample['selection_reason']}",
        "",
        "## Coverage Evidence",
        "",
        f"- Selected overlap record: `{json.dumps(sample['selected_overlap_row'], default=str)}`",
    ]
    (project_root / "outputs" / "logs" / "empirical_sample_selection.md").write_text("\n".join(body) + "\n", encoding="utf-8")

    overlap = audits["empirical_overlap_matrix"]
    iowa = overlap.loc[overlap["state"].eq("Iowa")]
    original_rows = iowa.loc[iowa["crop_set"].eq("Corn + Soybean + Winter Wheat")]
    all_original_rows = overlap.loc[overlap["crop_set"].eq("Corn + Soybean + Winter Wheat")]
    iowa_10_year_counties = int(original_rows["counties_with_10_year_run"].max()) if not original_rows.empty else 0
    iowa_15_year_counties = int(original_rows["counties_with_15_year_run"].max()) if not original_rows.empty else 0
    iowa_raw_counties = int(original_rows["complete_counties"].max()) if not original_rows.empty else 0
    iowa_feasible = iowa_10_year_counties >= 3
    original_crop_set_feasible = bool(
        not all_original_rows.empty
        and (
            (all_original_rows["counties_with_10_year_run"] >= 3)
            & (all_original_rows["max_county_longest_years"] >= 10)
        ).any()
    )
    selected_uses_original_crops = sample["selected_crops"] == ["Corn", "Soybean", "Winter Wheat"]
    iowa_answer = (
        "Yes"
        if iowa_feasible
        else f"No; Iowa has raw overlap for {iowa_raw_counties} county/counties, but {iowa_10_year_counties} have a 10-year complete run."
    )
    joint_answer = (
        f"Yes, in the selected {sample['selected_states'][0]} pilot sample."
        if original_crop_set_feasible and selected_uses_original_crops
        else "No under the current coverage rules."
    )
    audit_body = [
        "# Empirical Sample Feasibility Audit",
        "",
        "This audit is computed before sample selection and does not assume Iowa, Winter Wheat, 15 counties, or 2005--2022 are feasible.",
        "",
        "## Required Questions",
        "",
        f"1. Is Iowa empirically feasible? {iowa_answer}",
        f"2. Are Corn / Soybean / Winter Wheat jointly feasible? {joint_answer}",
        f"3. How many Iowa counties have sufficient overlapping data for Corn/Soybean/Winter Wheat? {iowa_10_year_counties} with at least a 10-year run; {iowa_15_year_counties} with at least a 15-year run.",
        f"4. What continuous year ranges are genuinely available? Selected pilot uses {sample['start_year']}--{sample['end_year']}; full ranges are in `outputs/tables/full/empirical_overlap_matrix.csv`.",
        f"5. Does the manuscript's stated 15-county design exist in the data? {'Yes' if not original_rows.empty and int(original_rows['counties_with_15_year_run'].max()) >= 15 else 'No'}",
        f"6. Is a three-crop panel defensible? {'Yes' if len(sample['selected_crops']) >= 3 else 'No'}",
        f"7. If not, what is the most defensible alternative? Selected crops: {', '.join(sample['selected_crops'])}.",
    ]
    (project_root / "outputs" / "logs" / "empirical_sample_feasibility_audit.md").write_text(
        "\n".join(audit_body) + "\n", encoding="utf-8"
    )


def geography_resolution_audit(project_root: Path, panel: pd.DataFrame) -> pd.DataFrame:
    audit = (
        panel.groupby(["state", "crop", "price_geography_level", "cost_geography_level", "cost_region"])
        .agg(rows=("profit_per_acre", "size"), counties=("county_fips", "nunique"), years=("year", "nunique"))
        .reset_index()
    )
    audit.to_csv(project_root / "outputs" / "tables" / "full" / "geography_resolution_audit.csv", index=False)
    body = [
        "# Geography Resolution Limitations",
        "",
        "Yield and acreage are county-level NASS QuickStats records where available.",
        "Prices are state-level NASS QuickStats records, so county observations share a state-year crop price.",
        "Costs are USDA ERS regional or national operating-cost estimates, not county-level production costs.",
        "The empirical panel preserves `price_geography_level` and `cost_geography_level` for every row.",
    ]
    (project_root / "outputs" / "logs" / "geography_resolution_limitations.md").write_text(
        "\n".join(body) + "\n", encoding="utf-8"
    )
    return audit


def write_data_source_registry(project_root: Path, manifest: pd.DataFrame) -> None:
    lines = [
        "# Data Source Registry",
        "",
        "This registry records authoritative sources actually used by the empirical pilot.",
        "",
        "| Provider | Exact Dataset | Retrieval Method | Retrieval Timestamp | Raw File | SHA-256 | Geographic Level | Temporal Level | Variables / Units | Known Limitations |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for _, row in manifest.iterrows():
        if row["source_id"].startswith("nass"):
            provider = "USDA NASS"
            dataset = "QuickStats query-tool CSV export"
            method = "Official web query export; API key unavailable"
        else:
            provider = "USDA ERS"
            dataset = "Commodity Costs and Returns CSV"
            method = "Official CSV download"
        lines.append(
            f"| {provider} | {dataset} | {method} | {row['retrieval_timestamp']} | `{Path(row['filename']).relative_to(project_root)}` | `{row['sha256']}` | "
            f"{row['geographic_level']} | {row['temporal_level']} | {row['variable_family']} | {row['notes']} |"
        )
    (project_root / "outputs" / "logs" / "data_source_registry.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
