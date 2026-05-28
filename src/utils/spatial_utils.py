"""Spatial utilities for the outage-traffic detection pipeline.

Core operations:
- Nearest-link join: intersection points -> road link lines
- Road hierarchy classification (arterial / collector / local)
- County boundary lookups
"""

import geopandas as gpd
import pandas as pd
import osmnx as ox
from typing import Optional

ROAD_HIERARCHY = {
    "motorway": "arterial",
    "motorway_link": "arterial",
    "trunk": "arterial",
    "trunk_link": "arterial",
    "primary": "arterial",
    "primary_link": "arterial",
    "secondary": "arterial",
    "secondary_link": "arterial",
    "tertiary": "collector",
    "tertiary_link": "collector",
    "residential": "local",
    "living_street": "local",
    "unclassified": "local",
    "service": "local",
}


def classify_road_hierarchy(highway_tag) -> str:
    """Map an OSM highway tag to arterial / collector / local."""
    if isinstance(highway_tag, list):
        highway_tag = highway_tag[0] if highway_tag else "unclassified"
    return ROAD_HIERARCHY.get(str(highway_tag).lower(), "unknown")


def nearest_link_join(
    points: gpd.GeoDataFrame,
    lines: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Join each point to its nearest line, returning point geometry with
    joined line attributes and distance.

    Uses geopandas.sjoin_nearest with spatial indexing (R-tree).
    This is O(n log m) instead of O(n * m) for a naive loop.

    Parameters
    ----------
    points : GeoDataFrame (Point geometry)
    lines : GeoDataFrame (LineString geometry)

    Returns
    -------
    GeoDataFrame with one row per point, including nearest line attributes
    and a 'distance_m' column.
    """
    if points.crs != lines.crs:
        lines = lines.to_crs(points.crs)

    joined = gpd.sjoin_nearest(
        points,
        lines,
        how="left",
        distance_col="distance_m",
    )

    side_cols = [c for c in joined.columns if c.endswith("_right")]
    for c in side_cols:
        joined.rename(columns={c: c.replace("_right", "_link")}, inplace=True)

    return joined


def load_county_boundary(
    county_key: str,
    cache_dir: Optional[str] = None,
) -> gpd.GeoDataFrame:
    """Load county boundary polygon from OSM.

    Parameters
    ----------
    county_key : str
        e.g. "harris_tx" (must be in load_osm.TARGET_COUNTIES)
    cache_dir : str or None
        Directory to cache GeoParquet

    Returns
    -------
    GeoDataFrame with county boundary
    """
    from src.data.load_osm import TARGET_COUNTIES

    info = TARGET_COUNTIES.get(county_key)
    if info is None:
        raise ValueError(f"Unknown county_key: {county_key}")

    if cache_dir:
        import os
        os.makedirs(cache_dir, exist_ok=True)
        path = os.path.join(cache_dir, f"boundary_{county_key}.parquet")
        if os.path.exists(path):
            return gpd.read_parquet(path)
    else:
        path = None

    place = f"{info['county']}, {info['state']}, USA"
    gdf = ox.geocode_to_gdf(place)

    if path:
        gdf.to_parquet(path)

    return gdf
