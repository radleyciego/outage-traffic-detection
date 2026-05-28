# Power Outage Detection via Traffic Patterns

Core question: Can GPS probe vehicle data passively detect distribution-level power outages by identifying anomalous driver behavior at traffic signals that have lost power?

Mechanism: Power outages -> traffic signals go dark -> drivers exhibit measurably different kinematic behavior (longer dwell times, altered deceleration profiles, changed speed nadirs) -> these signatures are passively encoded in commercial probe data already collected at 15-min resolution.

Institutional affiliation: CUNY Hunter College / Oak Ridge National Laboratory (ORNL)

Project status: Data acquisition and exploratory analysis phase. No data collected yet. No scripts written yet. Literature review and methodology are fully defined.

## Datasets

### Ground Truth

| Dataset  | Source        | Description                                                          | Access        |
|----------|---------------|----------------------------------------------------------------------|---------------|
| EAGLE-I  | ORNL / DOE    | County-level outage records, 15-min intervals, 2014-2024             | Open via DOE  |

### Traffic / Probe Data (pending access applications)

| Dataset          | Source            | Description                                                  | Access                                |
|------------------|-------------------|--------------------------------------------------------------|---------------------------------------|
| NPMRDS           | FHWA / INRIX      | Link-level speeds at 15-min bins, National Highway System    | Free for university researchers       |
| INRIX MetroLab   | INRIX             | Speed distribution profiles, dangerous slowdowns, volume     | Apply via INRIX MetroLab program      |

### Supplementary

| Dataset          | Source  | Description                                     | Access         |
|------------------|---------|-------------------------------------------------|----------------|
| OpenStreetMap    | OSM     | Signalized intersection locations + road network | Open (osmnx)   |

## Case Study Sites

### Primary (proof-of-concept)

| County         | State | Rationale                                                     |
|----------------|-------|---------------------------------------------------------------|
| Harris County  | TX    | Highest probe density; flat grid; high outage frequency       |
| Travis County  | TX    | High TNC density; EAGLE-I records well-documented             |

### Extension (generalizability)

| County             | State | Rationale                                                     |
|--------------------|-------|---------------------------------------------------------------|
| Mecklenburg County | NC    | NC 4th nationally in outages; compact county                  |
| Hamilton County    | OH    | Uber Movement validated here; OH 5th in outages               |

Note on weather events: Major named storms (Beryl, Uri, Harvey) are excluded from primary analysis because concurrent weather independently alters traffic behavior in ways that cannot be cleanly separated from the dark-signal effect. Post-storm outage windows (storm cleared, grid still partially down) may be revisited as a secondary analysis.

## Methodology

### Phase 1 - Spatial Setup
- Pull signalized intersection locations from OSM using osmnx for target counties
- Spatially join intersections to road links (nearest-link join)
- Classify intersections by road hierarchy (arterial vs. collector vs. local)
- Store outputs as GeoParquet

### Phase 2 - Outage Event Selection
- Load EAGLE-I records for Harris and Travis counties
- Filter to non-weather-concurrent outages - equipment failures, grid faults, rolling blackouts, vegetation/animal contacts, and post-storm outages (storm has passed, grid still partially down, roads clear)
- Filter to events with sharp onset (>=10% customers_out change within <=30 min)
- Define treatment windows: 2hr pre-outage (baseline), during, 2hr post-restoration
- Store event index as Parquet

### Phase 3 - Traffic Signature Extraction
- Pull NPMRDS speed records for target links during treatment windows
- Engineer features at intersection level per 15-min bin: speed_nadir, dwell_time, decel_onset_distance, speed_ratio
- Construct matched control intersections (same road class, no outage nearby)
- Store as Parquet partitioned by county + date

### Phase 4 - Classification Model
- Train binary classifier (Random Forest first, then XGBoost) on engineered features
- Labels from EAGLE-I: outage = 1, no outage = 0
- Covariates: time-of-day, day-of-week (weather excluded by event selection design)
- Evaluate: precision, recall, F1, AUC-ROC
- Spatial validation: do flagged intersections cluster within known outage footprints?

### Phase 5 - Validation & Extension
- Hold out one event per site for out-of-sample validation
- Extend to Mecklenburg and Hamilton counties
- Compare spatial resolution of detections vs. EAGLE-I county-level baseline

## Tech Stack

Languages: Python, SQL (DuckDB)
Core: pandas, geopandas, osmnx, shapely, pyarrow, duckdb, scikit-learn, xgboost

## File & Data Conventions

- Parquet for all tabular data (pyarrow engine)
- GeoParquet for all spatial data (geopandas + pyarrow)
- GeoJSON for small reference files only
- CSV for raw source data ingestion only; convert immediately to Parquet
- Files: snake_case, include county/state, e.g. `eagle_i_harris_tx_2024.parquet`
- Variables: snake_case
- Functions: snake_case, verb-first (load_eagle_i(), extract_features())
- Classes: PascalCase

## Critical Research Context

- The 15-minute temporal resolution of both EAGLE-I and NPMRDS is the critical alignment - do not aggregate to hourly unless explicitly asked
- Traffic signals are the physical coupling point between the power grid and road network - all analysis should be intersection-anchored, not link-anchored
- Control intersections are essential - always match on road class and time-of-day to isolate outage effect from normal congestion
- Weather events are excluded by design - the event selection strategy deliberately targets non-weather-concurrent outages. Do not reintroduce weather covariates unless explicitly asked
- The research is novel - no prior literature uses road probe data to infer power outage state
- Start with Harris County non-weather outage events as the proof-of-concept before generalizing
