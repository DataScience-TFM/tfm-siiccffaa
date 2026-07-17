from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import CATEGORICAL_FEATURES, NUMERIC_FEATURES, DERIVED_FEATURES


def temporal_split(df: pd.DataFrame, date_column: str):
    dates = np.array(sorted(df[date_column].dropna().unique()))
    if len(dates) < 10:
        raise ValueError("Se necesitan al menos 10 semanas distintas para dividir temporalmente.")
    train_end = dates[max(0, int(len(dates) * 0.70) - 1)]
    valid_end = dates[max(1, int(len(dates) * 0.85) - 1)]
    train = df[df[date_column] <= train_end].copy()
    valid = df[(df[date_column] > train_end) & (df[date_column] <= valid_end)].copy()
    test = df[df[date_column] > valid_end].copy()
    return train, valid, test, pd.Timestamp(train_end), pd.Timestamp(valid_end)


def make_logistic_pipeline() -> Pipeline:
    numeric = NUMERIC_FEATURES + DERIVED_FEATURES
    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    preprocess = ColumnTransformer([
        ("numeric", numeric_pipe, numeric),
        ("categorical", categorical_pipe, CATEGORICAL_FEATURES),
    ])
    return Pipeline([
        ("preprocess", preprocess),
        ("classifier", LogisticRegression(
            class_weight="balanced", max_iter=2000, random_state=42
        )),
    ])


def make_dummy_pipeline() -> DummyClassifier:
    return DummyClassifier(strategy="most_frequent", random_state=42)


def persistence_probabilities(df: pd.DataFrame) -> np.ndarray:
    """Baseline: alerta si lag 1 supera la media histórica previa."""
    lag = pd.to_numeric(df["reportes_lag_1w"], errors="coerce")
    mean = pd.to_numeric(df["reportes_media_4w_previa"], errors="coerce")
    return (lag.fillna(0) > mean.fillna(np.inf)).astype(float).to_numpy()

