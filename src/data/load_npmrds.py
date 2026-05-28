"""Placeholder for NPMRDS traffic probe data loader.

NPMRDS (National Performance Management Research Data Set) provides
link-level speeds at 15-minute bins on the National Highway System.

Access: Free for university researchers via FHWA application.
Status: Pending access approval.

When data arrives, this module will:
1. Load raw NPMRDS CSV/Parquet files
2. Filter to target counties by spatial join
3. Standardize columns and timestamps
4. Cache as partitioned GeoParquet
"""

import pandas as pd
import geopandas as gpd
from typing import Optional


def load_npmrds_links(
    path: str,
) -> gpd.GeoDataFrame:
    """Load NPMRDS road link geometry.

    Parameters
    ----------
    path : str
        Path to NPMRDS TMC shapefile or GeoParquet

    Returns
    -------
    GeoDataFrame of TMC links
    """
    raise NotImplementedError(
        "NPMRDS access not yet obtained. "
        "Apply via FHWA: https://ops.fhwa.dot.gov/Perf_measurement/"
    )


def load_npmrds_speeds(
    path: str,
) -> pd.DataFrame:
    """Load NPMRDS speed data for a date range.

    Parameters
    ----------
    path : str
        Path to NPMRDS speed CSV or Parquet file

    Returns
    -------
    DataFrame with columns: tmc, timestamp, speed, travel_time
    """
    raise NotImplementedError(
        "NPMRDS access not yet obtained."
    )
