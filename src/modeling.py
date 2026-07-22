from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier

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


def expanding_validation_folds(
    df: pd.DataFrame, date_column: str, n_folds: int = 3,
) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    """Crea ventanas expansivas para ajustar sin utilizar el bloque de prueba."""
    dates = np.array(sorted(df[date_column].dropna().unique()))
    if len(dates) < 20:
        raise ValueError("Se necesitan al menos 20 semanas para validación expansiva.")
    first_validation = max(1, int(len(dates) * 0.55))
    validation_dates = np.array_split(dates[first_validation:], n_folds)
    folds = []
    for window in validation_dates:
        if not len(window):
            continue
        fold_train = df[df[date_column] < window[0]].copy()
        fold_valid = df[df[date_column].isin(window)].copy()
        if len(fold_train) and len(fold_valid):
            folds.append((fold_train, fold_valid))
    return folds


def make_preprocessor() -> ColumnTransformer:
    numeric = NUMERIC_FEATURES + DERIVED_FEATURES
    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("numeric", numeric_pipe, numeric),
        ("categorical", categorical_pipe, CATEGORICAL_FEATURES),
    ])


def make_model_pipeline(classifier) -> Pipeline:
    return Pipeline([
        ("preprocess", make_preprocessor()),
        ("classifier", classifier),
    ])


def make_logistic_pipeline() -> Pipeline:
    return make_model_pipeline(
        LogisticRegression(
            class_weight="balanced", max_iter=2000, random_state=42
        )
    )


def make_decision_tree_pipeline() -> Pipeline:
    return make_model_pipeline(
        DecisionTreeClassifier(
            class_weight="balanced", max_depth=12, min_samples_leaf=10,
            random_state=42,
        )
    )


def make_random_forest_pipeline() -> Pipeline:
    return make_model_pipeline(
        RandomForestClassifier(
            n_estimators=500, max_depth=18, min_samples_leaf=4,
            class_weight="balanced_subsample", n_jobs=-1, random_state=42,
        )
    )


def make_linear_svm_pipeline() -> Pipeline:
    return make_model_pipeline(
        LinearSVC(
            class_weight="balanced", C=1.0, dual="auto", max_iter=5000,
            random_state=42,
        )
    )


def model_scores(model: Pipeline, features: pd.DataFrame) -> np.ndarray:
    """Devuelve puntuaciones 0-1 comparables para métricas y umbrales.

    Los modelos probabilísticos usan ``predict_proba``. Para LinearSVC se aplica
    una transformación logística a la distancia al hiperplano; sirve para
    ordenar y fijar un umbral, pero no debe interpretarse como probabilidad
    calibrada.
    """
    if hasattr(model, "predict_proba"):
        return model.predict_proba(features)[:, 1]
    decision = np.asarray(model.decision_function(features), dtype=float)
    decision = np.clip(decision, -500, 500)
    return 1.0 / (1.0 + np.exp(-decision))


def make_dummy_pipeline() -> DummyClassifier:
    return DummyClassifier(strategy="most_frequent", random_state=42)


def persistence_probabilities(df: pd.DataFrame) -> np.ndarray:
    """Baseline: alerta si la semana actual supera la media histórica previa."""
    lag = pd.to_numeric(df["reportes_semana"], errors="coerce")
    mean = pd.to_numeric(df["reportes_media_4w_previa"], errors="coerce")
    return (lag.fillna(0) > mean.fillna(np.inf)).astype(float).to_numpy()
