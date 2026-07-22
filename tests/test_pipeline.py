import numpy as np
import pandas as pd

from src.config import DATE_COLUMN, FEATURES, TARGET
from src.data import add_calendar_features
from src.modeling import (
    make_decision_tree_pipeline, make_linear_svm_pipeline,
    make_logistic_pipeline, make_random_forest_pipeline, model_scores,
    temporal_split, expanding_validation_folds,
)
from src.validation import audit_weekly_continuity, prepare_labeled_rows


def synthetic_data():
    rows = []
    rng = np.random.default_rng(42)
    for province in [1, 2]:
        for report_type in [10, 20]:
            values = rng.integers(1, 12, size=40)
            for i, date in enumerate(pd.date_range("2024-01-01", periods=40, freq="7D")):
                rows.append({
                    DATE_COLUMN: date, "provincia_id": province, "report_type_id": report_type,
                    "reportes_semana": values[i],
                    "reportes_lag_1w": values[max(0, i-1)], "reportes_lag_2w": values[max(0, i-2)],
                    "reportes_lag_4w": values[max(0, i-4)], "reportes_media_4w_previa": float(values[max(0, i-4):i].mean()) if i else 0,
                    "reportes_std_4w_previa": float(values[max(0, i-4):i].std()) if i else 0,
                    TARGET: int(values[i] > values[max(0, i-4):i].mean()) if i else 0,
                })
    return pd.DataFrame(rows)


def test_pipeline_trains_with_temporal_split():
    df = add_calendar_features(prepare_labeled_rows(synthetic_data()))
    train, valid, test, _, _ = temporal_split(df, DATE_COLUMN)
    model = make_logistic_pipeline().fit(train[FEATURES], train[TARGET])
    assert len(model.predict_proba(test[FEATURES])) == len(test)
    assert len(train) > len(valid) > 0 and len(test) > 0


def test_continuity_audit_detects_gap():
    df = synthetic_data()
    df = df.drop(df.index[5])
    assert len(audit_weekly_continuity(df)) >= 1


def test_four_algorithmic_families_train_and_score():
    df = add_calendar_features(prepare_labeled_rows(synthetic_data()))
    train, _, test, _, _ = temporal_split(df, DATE_COLUMN)
    factories = [
        make_logistic_pipeline, make_decision_tree_pipeline,
        make_random_forest_pipeline, make_linear_svm_pipeline,
    ]
    for factory in factories:
        model = factory().fit(train[FEATURES], train[TARGET])
        scores = model_scores(model, test[FEATURES])
        assert len(scores) == len(test)
        assert np.all((scores >= 0) & (scores <= 1))


def test_expanding_validation_never_uses_future_rows():
    df = add_calendar_features(prepare_labeled_rows(synthetic_data()))
    train, valid, _, _, _ = temporal_split(df, DATE_COLUMN)
    folds = expanding_validation_folds(pd.concat([train, valid]), DATE_COLUMN)
    assert len(folds) == 3
    for fold_train, fold_valid in folds:
        assert fold_train[DATE_COLUMN].max() < fold_valid[DATE_COLUMN].min()
