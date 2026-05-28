import os
import geopandas as gpd
import osmnx as ox
from typing import Optional

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
        raise ValueError(f"Unknown county_key: {county_key}. "
                         f"Choose from {list(TARGET_COUNTIES)}")

    place = _place_name(info["county"], info["state"])

    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        path = os.path.join(cache_dir, f"intersections_{county_key}.parquet")
        if os.path.exists(path):
            return gpd.read_parquet(path)
    else:
        path = None

    gdf = ox.features_from_place(place, tags={"highway": "traffic_signals"})
    gdf = gdf[gdf.geometry.type == "Point"].copy().reset_index()

    if "element" in gdf.columns:
        gdf = gdf.drop(columns=["element"])

    if path:
        gdf.to_parquet(path)

    return gdf


def load_road_network(
    county_key: str,
    network_type: str = "drive",
    cache_dir: Optional[str] = None,
) -> gpd.GeoDataFrame:
    """Pull drivable road network from OSM via osmnx.

    Caches edges to GeoParquet on first call if cache_dir is provided.

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
            return gpd.read_parquet(path)
    else:
        path = None

    graph = ox.graph_from_place(place, network_type=network_type)
    _, edges = ox.graph_to_gdfs(graph)

    if path:
        edges.to_parquet(path)

    return edges


def list_available_counties() -> list[str]:
    """Return list of configured county keys."""
    return list(TARGET_COUNTIES)
