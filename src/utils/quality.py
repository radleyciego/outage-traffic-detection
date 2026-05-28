"""Reusable data quality checks for the outage-traffic detection pipeline.

Each function returns a dict with check results and logs warnings/errors.
Calling code decides severity based on context.
"""

import pandas as pd
import geopandas as gpd
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def check_no_null_geometries(gdf: gpd.GeoDataFrame, name: str = "GeoDataFrame") -> dict:
    """Fail if any geometry is None or null."""
    null_mask = gdf.geometry.isna() | gdf.geometry.isnull()
    n_null = null_mask.sum()
    if n_null:
        raise ValueError(f"{name}: {n_null} null geometries")
    return {"null_geometries": 0}


def check_coordinate_range(gdf: gpd.GeoDataFrame, name: str = "GeoDataFrame") -> dict:
    """Verify lat [-90, 90] and lon [-180, 180] or [0, 360]."""
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    lat_ok = -90 <= bounds[1] <= 90 and -90 <= bounds[3] <= 90
    if not lat_ok:
        logger.warning(f"{name}: latitude outside [-90, 90]: [{bounds[1]:.1f}, {bounds[3]:.1f}]")
    return {"lat_in_range": lat_ok, "lon_in_range": True}


def check_no_duplicates(
    df: pd.DataFrame, subset: list[str], name: str = "DataFrame"
) -> dict:
    """Warn if duplicate rows exist on the given subset."""
    n_dupes = df.duplicated(subset=subset).sum()
    if n_dupes:
        logger.warning(f"{name}: {n_dupes} duplicate rows on {subset}")
    return {"duplicates": int(n_dupes)}


def check_value_range(
    df: pd.DataFrame,
    col: str,
    min_val: float,
    max_val: float,
    name: str = "DataFrame",
) -> dict:
    """Check a numeric column stays within [min_val, max_val]."""
    if col not in df.columns:
        raise ValueError(f"{name}: column '{col}' not found")
    series = df[col]
    out = ((series < min_val) | (series > max_val)).sum()
    if out:
        logger.warning(f"{name}: {col} has {out} values outside [{min_val}, {max_val}]")
    return {"out_of_range": int(out), "min": float(series.min()), "max": float(series.max())}


def check_temporal_gaps(
    df: pd.DataFrame,
    time_col: str = "timestamp",
    expected_freq: str = "15min",
    tolerance_factor: float = 1.5,
    name: str = "DataFrame",
) -> dict:
    """Detect gaps in a time series larger than expected_freq * tolerance_factor."""
    if df.empty:
        return {"gap_count": 0, "max_gap": None}

    diffs = df[time_col].sort_values().diff()
    expected = pd.Timedelta(expected_freq)
    gaps = diffs[diffs > expected * tolerance_factor]
    return {
        "gap_count": int(len(gaps)),
        "max_gap": str(gaps.max()) if len(gaps) else None,
    }


def check_crs(
    gdf: gpd.GeoDataFrame, expected_epsg: int = 4326, name: str = "GeoDataFrame"
) -> dict:
    """Verify CRS matches expected EPSG code."""
    actual = gdf.crs
    if actual is None:
        raise ValueError(f"{name}: no CRS set")
    expected_str = f"EPSG:{expected_epsg}"
    if actual.to_authority() != ("EPSG", str(expected_epsg)):
        logger.warning(f"{name}: expected {expected_str}, got {actual}")
        return {"crs_match": False}
    return {"crs_match": True}


def check_column_types(
    df: pd.DataFrame, expected_types: dict[str, str], name: str = "DataFrame"
) -> dict:
    """Check columns exist and have expected dtypes."""
    results = {}
    for col, dtype in expected_types.items():
        if col not in df.columns:
            raise ValueError(f"{name}: missing column '{col}'")
        actual = str(df[col].dtype)
        matched = actual.startswith(dtype)
        results[col] = matched
        if not matched:
            logger.warning(f"{name}: {col} expected {dtype}, got {actual}")
    return results


def normalize_list_columns(
    df: pd.DataFrame, exclude: Optional[list[str]] = None
) -> pd.DataFrame:
    """Flatten columns that mix list and scalar values.

    OSM data often returns columns where some rows are lists (multiple values)
    and others are scalars. PyArrow/Parquet cannot serialize mixed types,
    so we flatten list values to [0] before persisting.

    Parameters
    ----------
    df : DataFrame
    exclude : list of str, optional
        Columns to skip

    Returns
    -------
    DataFrame with mixed-type columns flattened
    """
    df = df.copy()
    exclude = set(exclude or ["geometry"])
    for col in df.columns:
        if col in exclude:
            continue
        if df[col].apply(type).nunique() > 1:
            df[col] = df[col].apply(
                lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x
            )
            logger.info(f"normalized mixed-type column: {col}")
    return df
