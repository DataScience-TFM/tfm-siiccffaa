from __future__ import annotations

import argparse
import json
from pathlib import Path
import joblib
import pandas as pd

from src.config import (
    CATEGORICAL_FEATURES, DATE_COLUMN, FEATURES, NUMERIC_FEATURES,
    TARGET, Settings,
)
from src.data import add_calendar_features, load_dataset
from src.evaluation import choose_threshold, extract_coefficients, metrics_at_threshold, save_plots
from src.modeling import make_dummy_pipeline, make_logistic_pipeline, persistence_probabilities, temporal_split
from src.validation import audit_weekly_continuity, prepare_labeled_rows, validate_schema


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena y evalúa el modelo del TFM SIICCFFAA.")
    parser.add_argument("--csv", help="CSV alternativo. Si se omite, consulta BigQuery.")
    parser.add_argument("--allow-gaps", action="store_true", help="Permite continuar si hay semanas no consecutivas.")
    args = parser.parse_args()
    settings = Settings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.model_dir.mkdir(parents=True, exist_ok=True)

    raw = load_dataset(settings, args.csv)
    validate_schema(
        raw,
        [DATE_COLUMN, TARGET]
        + NUMERIC_FEATURES
        + CATEGORICAL_FEATURES
        + ["reportes_siguiente_semana"],
    )
    gaps = audit_weekly_continuity(raw)
    gaps.to_csv(settings.output_dir / "weekly_continuity_gaps.csv", index=False)
    if len(gaps) and not args.allow_gaps:
        raise SystemExit(
            f"Se detectaron {len(gaps)} saltos semanales. Revise outputs/weekly_continuity_gaps.csv "
            "y complete la cuadrícula semanal antes de modelar. Use --allow-gaps solo para diagnóstico."
        )

    df = add_calendar_features(prepare_labeled_rows(raw)).sort_values(DATE_COLUMN)
    train, valid, test, train_end, valid_end = temporal_split(df, DATE_COLUMN)
    X_train, y_train = train[FEATURES], train[TARGET]
    X_valid, y_valid = valid[FEATURES], valid[TARGET]
    X_test, y_test = test[FEATURES], test[TARGET]

    dummy = make_dummy_pipeline().fit(X_train, y_train)
    dummy_probability = dummy.predict_proba(X_test)[:, 1]
    persistence_probability = persistence_probabilities(test)

    model = make_logistic_pipeline().fit(X_train, y_train)
    valid_probability = model.predict_proba(X_valid)[:, 1]
    threshold = choose_threshold(y_valid, valid_probability)
    test_probability = model.predict_proba(X_test)[:, 1]

    rows = []
    for name, prob, cut in [
        ("clase_mayoritaria", dummy_probability, 0.5),
        ("regla_persistencia", persistence_probability, 0.5),
        ("regresion_logistica", test_probability, threshold),
    ]:
        rows.append({"modelo": name, **metrics_at_threshold(y_test, prob, cut, settings.top_k)})
    pd.DataFrame(rows).to_csv(settings.output_dir / "model_comparison.csv", index=False)

    predictions = test[[DATE_COLUMN, "provincia_id", "report_type_id"]].copy()
    for optional in ["provincia_name", "report_type_name"]:
        if optional in test:
            predictions[optional] = test[optional]
    predictions["valor_real"] = y_test.to_numpy()
    predictions["probabilidad_incremento"] = test_probability
    predictions["prediccion"] = (test_probability >= threshold).astype(int)
    predictions["prioridad"] = pd.cut(
        predictions["probabilidad_incremento"], [-0.01, 0.4, 0.7, 1.0],
        labels=["baja", "media", "alta"]
    )
    predictions.sort_values("probabilidad_incremento", ascending=False).to_csv(
        settings.output_dir / "predictions_test.csv", index=False
    )
    extract_coefficients(model).to_csv(settings.output_dir / "coefficients.csv", index=False)
    save_plots(y_test, test_probability, threshold, settings.output_dir)
    joblib.dump(model, settings.model_dir / "logistic_regression.joblib")
    metadata = {
        "modelo": "regresion_logistica",
        "target": TARGET,
        "features": FEATURES,
        "train_end": str(train_end.date()),
        "validation_end": str(valid_end.date()),
        "threshold": threshold,
        "rows": {"train": len(train), "validation": len(valid), "test": len(test)},
    }
    (settings.model_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(pd.DataFrame(rows).to_string(index=False))
    print(f"Modelo guardado en {settings.model_dir / 'logistic_regression.joblib'}")


if __name__ == "__main__":
    main()
