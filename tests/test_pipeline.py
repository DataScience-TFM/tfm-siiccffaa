import numpy as np
import pandas as pd

from src.config import DATE_COLUMN, FEATURES, TARGET
from src.data import add_calendar_features
from src.modeling import make_logistic_pipeline, temporal_split
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

