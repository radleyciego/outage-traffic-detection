"""Feature engineering for outage-traffic detection.

Transforms raw NPMRDS speed observations at the intersection level
into engineered features for classification.

Engineered features (per intersection per 15-min bin):
- speed_nadir: minimum speed in approach zone
- dwell_time: estimated stop duration
- decel_onset_distance: distance at which deceleration begins
- speed_ratio: speed during outage / baseline speed
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from typing import Optional


def extract_features(
    speed_records: pd.DataFrame,
    intersections: gpd.GeoDataFrame,
    treatment_windows: pd.DataFrame,
) -> pd.DataFrame:
    """Extract intersection-level traffic features for each 15-min bin
    in the given treatment windows.

    Parameters
    ----------
    speed_records : DataFrame
        Columns: tmc_id, timestamp, speed, travel_time
    intersections : GeoDataFrame
        Intersection points with nearest_link_id
    treatment_windows : DataFrame
        Columns: event_id, fips, window_start, window_end, treatment (0/1)

    Returns
    -------
    DataFrame of features, one row per (intersection_id, timestamp)
    """
    raise NotImplementedError(
        "Feature extraction requires NPMRDS data (pending access)."
    )
