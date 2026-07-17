from __future__ import annotations

from pathlib import Path
import pandas as pd

from .config import DATE_COLUMN, Settings, configure_credentials


def load_from_bigquery(settings: Settings) -> pd.DataFrame:
    """Lee solo las columnas necesarias; usa Application Default Credentials."""
    from google.cloud import bigquery

    configure_credentials()

    query = f"""
    SELECT
      report_week_start, provincia_id, provincia_name,
      report_type_id, report_type_name,
      reportes_semana, reportes_lag_1w, reportes_lag_2w,
      reportes_lag_4w, reportes_media_4w_previa,
      reportes_std_4w_previa, reportes_siguiente_semana,
      incremento_actividad_siguiente_periodo
    FROM `{settings.model_table}`
    ORDER BY report_week_start, provincia_id, report_type_id
    """
    client = bigquery.Client(project=settings.project_id, location=settings.location)
    rows = client.query(query, location=settings.location).result()
    # Se construye el DataFrame directamente para no depender de pyarrow.
    # Esto mantiene compatibilidad con Python 3.14 en Windows.
    return pd.DataFrame([dict(row.items()) for row in rows])


def load_dataset(settings: Settings, csv_path: str | None = None) -> pd.DataFrame:
    if csv_path:
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"No existe el CSV: {path}")
        df = pd.read_csv(path)
    else:
        df = load_from_bigquery(settings)
    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors="raise")
    return df


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["mes"] = result[DATE_COLUMN].dt.month.astype("int16")
    result["semana_anio"] = result[DATE_COLUMN].dt.isocalendar().week.astype("int16")
    return result
