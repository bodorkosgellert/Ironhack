"""Shared helpers for CDC PLACES + Open-Meteo data pulls."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

STATE = "AL"
YEAR = "2023"
CDC_URL = "https://data.cdc.gov/resource/swc5-untb.json"
OPEN_METEO_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Extra PLACES measures (county, crude prevalence, 2023)
CONFOUNDER_MEASURES = {
    "CSMOKING": "smoking_pct",
    "OBESITY": "obesity_pct",
    "DIABETES": "diabetes_pct",
    "LPA": "no_physical_activity_pct",
    "BINGE": "binge_drinking_pct",
}


def get_json(url: str) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "ironhack-portfolio-v2"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def fetch_measure(measure_id: str, value_column: str) -> pd.DataFrame:
    """One PLACES measure for all Alabama counties."""
    params = urllib.parse.urlencode(
        {
            "stateabbr": STATE,
            "measureid": measure_id,
            "data_value_type": "Crude prevalence",
            "year": YEAR,
            "$limit": 5000,
        }
    )
    rows = get_json(f"{CDC_URL}?{params}")
    if not rows:
        raise RuntimeError(f"No PLACES rows for measure {measure_id}")

    df = pd.DataFrame(rows)
    df["county_fips"] = df["locationid"].astype(str).str.zfill(5)
    df[value_column] = pd.to_numeric(df["data_value"], errors="coerce")
    if "geolocation" in df.columns:
        df["lat"] = df["geolocation"].apply(
            lambda g: g["coordinates"][1] if isinstance(g, dict) else None
        )
        df["lon"] = df["geolocation"].apply(
            lambda g: g["coordinates"][0] if isinstance(g, dict) else None
        )
    out_cols = ["county_fips", "locationname", value_column]
    if "lat" in df.columns:
        out_cols.extend(["lat", "lon"])
    if measure_id == "CASTHMA":
        for extra in ("low_confidence_limit", "high_confidence_limit"):
            if extra in df.columns:
                df[extra] = pd.to_numeric(df[extra], errors="coerce")
                out_cols.append(extra)
    df = df[out_cols].drop_duplicates(subset=["county_fips"], keep="first")
    return df.rename(columns={"locationname": "county"})


def fetch_pm25_annual(lat: float, lon: float) -> float:
    params = urllib.parse.urlencode(
        {
            "latitude": f"{lat:.4f}",
            "longitude": f"{lon:.4f}",
            "start_date": f"{YEAR}-01-01",
            "end_date": f"{YEAR}-12-31",
            "hourly": "pm2_5",
        }
    )
    data = get_json(f"{OPEN_METEO_URL}?{params}")
    values = [v for v in data["hourly"]["pm2_5"] if v is not None]
    if not values:
        raise RuntimeError(f"No PM2.5 values for ({lat}, {lon})")
    return sum(values) / len(values)


def attach_pm25(df: pd.DataFrame) -> pd.DataFrame:
    values: list[float] = []
    for _, row in df.iterrows():
        try:
            pm25 = fetch_pm25_annual(float(row["lat"]), float(row["lon"]))
        except (urllib.error.URLError, RuntimeError, TimeoutError):
            pm25 = float("nan")
        values.append(pm25)
        time.sleep(0.2)
    out = df.copy()
    out["pm25_ug_m3_annual_mean"] = values
    return out.dropna(subset=["pm25_ug_m3_annual_mean"])


def build_county_dataset() -> pd.DataFrame:
    """Asthma target + confounders + PM2.5 (one row per county)."""
    base = fetch_measure("CASTHMA", "asthma_pct")
    merged = base

    for measure_id, col in CONFOUNDER_MEASURES.items():
        extra = fetch_measure(measure_id, col)[["county_fips", col]]
        merged = merged.merge(extra, on="county_fips", how="left")

    merged = attach_pm25(merged)
    return merged.dropna()
