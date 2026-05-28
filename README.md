# Power Outage Detection via Traffic Patterns

Can GPS probe vehicle data passively detect distribution-level power outages by identifying anomalous driver behavior at traffic signals that have lost power?

When a traffic signal goes dark, drivers exhibit measurably different behavior — longer dwell times, altered deceleration profiles, changed speed nadirs. These signatures are passively encoded in commercial probe data already collected at 15-minute resolution by INRIX, NPMRDS, and similar services.

This project builds a detection pipeline that:
1. Spatially links signalized intersections to road network links
2. Selects known outage events from EAGLE-I (ORNL/DOE)
3. Extracts kinematic features from probe data during outage windows
4. Trains a classifier to detect outage states from traffic patterns alone

## Status

Phase 1 (spatial setup) scaffolding complete. Awaiting data access approvals for NPMRDS/INRIX probe data.

## Repository Structure

```
├── CLAUDE.md                  Persistent context for AI coding assistants
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/                   Untouched source data
│   ├── processed/             Cleaned, joined, feature-engineered
│   └── outputs/               Model results, figures, exports
├── notebooks/
│   ├── 01_osm_intersections.ipynb
│   ├── 02_eagle_i_exploration.ipynb
│   ├── 03_npmrds_feature_engineering.ipynb
│   └── 04_classification_model.ipynb
├── src/
│   ├── data/                  Data loaders (EAGLE-I, NPMRDS, OSM)
│   ├── features/              Traffic feature extraction
│   ├── models/                Classifier training and evaluation
│   └── utils/                 Spatial utilities
└── reports/
    └── figures/
```

## Data Access

- EAGLE-I: Open access via DOE — download from eagle-i.ornl.gov
- NPMRDS: Requires FHWA university researcher application
- INRIX MetroLab: Requires application via INRIX MetroLab program

## Citation

Radley Ciego, CUNY Hunter College / Oak Ridge National Laboratory.
