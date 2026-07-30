#!/usr/bin/env python3
"""Fetch fixed-vintage generalized state geometry from the US Census Bureau."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "goal17" / "raw"
OUTPUT = OUTPUT_DIR / "census_states_2024_5m.geojson"
REGISTRY = ROOT / "data" / "goal17" / "source_registry.csv"
SERVICE = "https://tigerweb.geo.census.gov/arcgis/rest/services/Generalized_ACS2024/State_County/MapServer/8/query"
PARAMS = {
    "where": "1=1",
    "outFields": "GEOID,STUSAB",
    "returnGeometry": "true",
    "outSR": "4326",
    "f": "geojson",
}


def main() -> int:
    url = f"{SERVICE}?{urllib.parse.urlencode(PARAMS)}"
    request = urllib.request.Request(url, headers={"User-Agent": "crop-ranking-reversal/GOAL17"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    document = json.loads(payload)
    if document.get("type") != "FeatureCollection" or len(document.get("features", [])) < 50:
        raise RuntimeError("Census response is not the expected state FeatureCollection")

    canonical = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(canonical)

    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source_id", "publisher", "vintage", "layer", "url", "file", "features", "sha256"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "source_id": "census_tigerweb_states_2024_5m",
                "publisher": "United States Census Bureau",
                "vintage": "ACS 2024",
                "layer": "Generalized states 5M (MapServer layer 8)",
                "url": url,
                "file": OUTPUT.relative_to(ROOT).as_posix(),
                "features": len(document["features"]),
                "sha256": digest,
            }
        )
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({len(document['features'])} features; sha256={digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
