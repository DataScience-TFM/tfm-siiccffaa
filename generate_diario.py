from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np

from src.config import DATE_COLUMN, FEATURES, Settings
from src.data import add_calendar_features, load_dataset

ROOT = Path(__file__).resolve().parent


def priority(probability: float) -> str:
    if probability >= 0.70:
        return "Alta"
    if probability >= 0.40:
        return "Media"
    return "Baja"


def trend(current: float, mean: float | None) -> tuple[str, float | None]:
    if mean is None or np.isnan(mean) or mean == 0:
        return ("Sin referencia", None)
    change = ((current - mean) / mean) * 100
    if change >= 20:
        return ("Ascendente", change)
    if change <= -20:
        return ("Descendente", change)
    return ("Estable", change)


def main() -> None:
    settings = Settings()
    model_path = settings.model_dir / "logistic_regression.joblib"
    if not model_path.is_file():
        raise FileNotFoundError("No existe el modelo. Ejecute primero run_model.ps1.")

    data = add_calendar_features(load_dataset(settings))
    latest_date = data[DATE_COLUMN].max()
    latest = data[data[DATE_COLUMN].eq(latest_date)].copy()
    if latest.empty:
        raise RuntimeError("No existen observaciones para el último periodo.")

    model = joblib.load(model_path)
    metadata_path = settings.model_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else {}
    latest["probabilidad_incremento"] = model.predict_proba(latest[FEATURES])[:, 1]
    latest = latest.sort_values("probabilidad_incremento", ascending=False)

    records = []
    for _, row in latest.head(25).iterrows():
        label, change = trend(float(row["reportes_semana"]), row["reportes_media_4w_previa"])
        probability = float(row["probabilidad_incremento"])
        records.append({
            "provincia": str(row.get("provincia_name", row["provincia_id"])),
            "tipo_reporte": str(row.get("report_type_name", row["report_type_id"])),
            "operaciones_semana": int(row["reportes_semana"]),
            "media_4w": None if np.isnan(row["reportes_media_4w_previa"]) else round(float(row["reportes_media_4w_previa"]), 2),
            "tendencia": label,
            "variacion_pct": None if change is None else round(change, 1),
            "probabilidad": round(probability, 6),
            "prioridad": priority(probability),
            "mensaje": (
                f"Señal analítica con {probability:.1%} de probabilidad estimada de incremento. "
                f"La actividad reciente se clasifica como {label.lower()}."
            ),
        })

    prediction_date = latest_date + np.timedelta64(7, "D")
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_week": str(latest_date.date()),
        "prediction_week": str(prediction_date.date()),
        "model": "Regresión logística",
        "threshold": float(metadata.get("threshold", 0.5)),
        "total_evaluated": int(len(latest)),
        "high_priority": sum(r["prioridad"] == "Alta" for r in records),
        "medium_priority": sum(r["prioridad"] == "Media" for r in records),
        "total_operations": int(latest["reportes_semana"].sum()),
        "signals": records,
        "method_note": (
            "Las probabilidades son señales de apoyo a la revisión humana. No representan certeza, "
            "causalidad ni una orden de actuación."
        ),
    }
    destination = settings.output_dir / "diario_ejecutivo.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Diario generado: {destination}")
    print(f"Periodo predicho: {payload['prediction_week']} | Señales: {len(records)}")


if __name__ == "__main__":
    main()
