"""Loader for EAGLE-I power outage data (ORNL / DOE).

EAGLE-I provides county-level outage records at 15-minute resolution.
Data is open access via the DOE API at eagle-i.ornl.gov.

Temporal resolution: 15 minutes (critical alignment with NPMRDS).
Spatial resolution: County (FIPS code).
"""

import os
import pandas as pd
import geopandas as gpd
import requests
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

EAGLE_I_API = "https://eagle-i.ornl.gov/api/v2"


def fetch_eagle_i(
    fips_codes: list[str],
    start_date: str,
    end_date: str,
    api_token: Optional[str] = None,
    cache_dir: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch EAGLE-I outage records for target counties via the DOE API.

    Parameters
    ----------
    fips_codes : list of str
        5-digit FIPS codes (e.g. ["48201"] for Harris County, TX)
    start_date : str
        ISO date (YYYY-MM-DD)
    end_date : str
        ISO date (YYYY-MM-DD)
    api_token : str or None
        EAGLE-I API token. If None, looks for EAGLE_I_API_TOKEN env var.
    cache_dir : str or None
        Directory to cache raw API responses as Parquet

    Returns
    -------
    DataFrame with columns: timestamp, fips, county, state, customers_out, customers_total
    """
    token = api_token or os.environ.get("EAGLE_I_API_TOKEN")
    if token is None:
        raise ValueError(
            "EAGLE-I API token required. Pass api_token or set EAGLE_I_API_TOKEN env var."
        )

    records = []
    for fips in fips_codes:
        url = f"{EAGLE_I_API}/outages/{fips}"
        params = {
            "start": start_date,
            "end": end_date,
            "format": "json",
        }
        headers = {"Authorization": f"Bearer {token}"}

        resp = requests.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        for entry in data.get("data", []):
            records.append({
                "timestamp": entry["timestamp"],
                "fips": fips,
                "county": entry.get("county_name", ""),
                "state": entry.get("state", ""),
                "customers_out": entry.get("customers_out", 0),
                "customers_total": entry.get("customers_total", 0),
            })

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["fips", "timestamp"]).reset_index(drop=True)

    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        fips_str = "_".join(fips_codes)
        path = os.path.join(cache_dir, f"eagle_i_{fips_str}_{start_date}_{end_date}.parquet")
        df.to_parquet(path, index=False)

    return df


def load_eagle_i_local(
    path: str,
) -> pd.DataFrame:
    """Load EAGLE-I data from a local Parquet or CSV file.

    Use this when you've downloaded the data separately instead of
    hitting the API directly.

    Parameters
    ----------
    path : str
        Path to .parquet or .csv file

    Returns
    -------
    DataFrame with standardized columns
    """
    path_obj = Path(path)
    if path_obj.suffix == ".parquet":
        df = pd.read_parquet(path)
    elif path_obj.suffix == ".csv":
        df = pd.read_csv(path)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    else:
        raise ValueError(f"Unsupported file format: {path_obj.suffix}")

    required = {"timestamp", "fips", "customers_out", "customers_total"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return df.sort_values(["fips", "timestamp"]).reset_index(drop=True)
