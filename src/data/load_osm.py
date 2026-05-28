import os
import geopandas as gpd
import osmnx as ox
import logging
from typing import Optional

from src.utils.quality import (
    check_no_null_geometries,
    check_no_duplicates,
    normalize_list_columns,
)

logger = logging.getLogger(__name__)

TARGET_COUNTIES = {
    "harris_tx": {"state": "Texas", "county": "Harris County"},
    "travis_tx": {"state": "Texas", "county": "Travis County"},
    "mecklenburg_nc": {"state": "North Carolina", "county": "Mecklenburg County"},
    "hamilton_oh": {"state": "Ohio", "county": "Hamilton County"},
}


def _place_name(county: str, state: str) -> str:
    return f"{county}, {state}, USA"


def load_intersections(
    county_key: str,
    cache_dir: Optional[str] = None,
) -> gpd.GeoDataFrame:
    """Pull signalized intersections from OSM using osmnx.

    Caches to GeoParquet on first call if cache_dir is provided.

    Parameters
    ----------
    county_key : str
        Key in TARGET_COUNTIES dict, e.g. "harris_tx"
    cache_dir : str or None
        Directory to read/write cached GeoParquet

    Returns
    -------
    GeoDataFrame of traffic signal points with OSM metadata
    """
    info = TARGET_COUNTIES.get(county_key)
    if info is None:
        raise ValueError(
            f"Unknown county_key: {county_key}. "
            f"Choose from {list(TARGET_COUNTIES)}"
        )

    place = _place_name(info["county"], info["state"])

    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        path = os.path.join(cache_dir, f"intersections_{county_key}.parquet")
        if os.path.exists(path):
            try:
                gdf = gpd.read_parquet(path)
                logger.info(f"Loaded {len(gdf)} intersections from cache")
                return gdf
            except Exception as e:
                logger.warning(f"Cache read failed ({e}), re-fetching")
    else:
        path = None

    gdf = ox.features_from_place(place, tags={"highway": "traffic_signals"})
    gdf = gdf[gdf.geometry.type == "Point"].copy().reset_index()

    if "element" in gdf.columns:
        gdf = gdf.drop(columns=["element"])

    check_no_null_geometries(gdf, f"intersections_{county_key}")
    check_no_duplicates(gdf, subset=["geometry"], name=f"intersections_{county_key}")

    gdf = normalize_list_columns(gdf)

    if path:
        gdf.to_parquet(path)
        logger.info(f"Cached {len(gdf)} intersections to {path}")

    return gdf


def load_road_network(
    county_key: str,
    network_type: str = "drive",
    cache_dir: Optional[str] = None,
) -> gpd.GeoDataFrame:
    """Pull drivable road network from OSM via osmnx.

    Caches edges to GeoParquet on first call if cache_dir is provided.
    List-typed columns are normalized for Parquet compatibility.

    Parameters
    ----------
    county_key : str
        Key in TARGET_COUNTIES dict
    network_type : str
        OSMnx network type (drive, drive_service, bike, walk, all)
    cache_dir : str or None
        Directory to read/write cached GeoParquet

    Returns
    -------
    GeoDataFrame of road edges with OSM tags
    """
    info = TARGET_COUNTIES.get(county_key)
    if info is None:
        raise ValueError(f"Unknown county_key: {county_key}")

    place = _place_name(info["county"], info["state"])

    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        path = os.path.join(cache_dir, f"roads_{county_key}.parquet")
        if os.path.exists(path):
            try:
                edges = gpd.read_parquet(path)
                logger.info(f"Loaded {len(edges)} road edges from cache")
                return edges
            except Exception as e:
                logger.warning(f"Cache read failed ({e}), re-fetching")
    else:
        path = None

    graph = ox.graph_from_place(place, network_type=network_type)
    _, edges = ox.graph_to_gdfs(graph)

    check_no_null_geometries(edges, f"roads_{county_key}")

    edges = normalize_list_columns(edges)
    check_no_duplicates(edges, subset=["osmid"], name=f"roads_{county_key}")

    if path:
        edges.to_parquet(path)
        logger.info(f"Cached {len(edges)} road edges to {path}")

    return edges


def list_available_counties() -> list[str]:
    """Return list of configured county keys."""
    return list(TARGET_COUNTIES)
