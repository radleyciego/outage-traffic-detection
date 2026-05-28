"""Binary classifier for outage detection from traffic features.

Two-stage approach:
1. Random Forest (baseline, interpretable)
2. XGBoost (higher performance)

Label: 1 = outage ongoing, 0 = normal conditions (from EAGLE-I)
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    classification_report, confusion_matrix,
)
from typing import Optional, Tuple
import xgboost as xgb


def prepare_features(
    features: pd.DataFrame,
    time_cols: list[str] = ["hour", "day_of_week"],
) -> Tuple[pd.DataFrame, pd.Series]:
    """Separate features from labels and add time covariates."""
    label_col = "outage"
    feature_cols = [
        "speed_nadir", "dwell_time", "decel_onset_distance", "speed_ratio",
    ] + time_cols

    missing = set(feature_cols) - set(features.columns)
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")

    X = features[feature_cols].copy()
    y = features[label_col].copy()

    return X, y


def train_random_forest(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n_estimators: int = 300,
    max_depth: int = 12,
    random_state: int = 42,
) -> RandomForestClassifier:
    """Train a Random Forest classifier.

    Returns trained model for feature importance inspection.
    """
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)
    return model


def train_xgboost(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    random_state: int = 42,
) -> xgb.XGBClassifier:
    """Train an XGBoost classifier."""
    model = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=8,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),
        random_state=random_state,
        eval_metric="auc",
        use_label_encoder=False,
    )
    model.fit(X_train, y_train)
    return model


def evaluate_model(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict:
    """Return precision, recall, F1, AUC-ROC, and confusion matrix."""
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    results = {
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "auc_roc": roc_auc_score(y_test, y_prob),
        "classification_report": classification_report(y_test, y_pred),
    }
    return results


def get_feature_importance(model, feature_names: list[str]) -> pd.DataFrame:
    """Return feature importance as a DataFrame."""
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    else:
        raise ValueError("Model does not have feature_importances_")

    return pd.DataFrame({
        "feature": feature_names,
        "importance": importances,
    }).sort_values("importance", ascending=False)
