from __future__ import annotations

from pathlib import Path
from threading import Lock
from time import monotonic

import pandas as pd
from flask import Flask, Response, abort, redirect, render_template, url_for
from plotly.offline import get_plotlyjs

from src.bigquery_runner import BigQueryRunner
from src.queries import QUERIES

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
CACHE_TTL_SECONDS = 15 * 60
_cache: dict[str, pd.DataFrame] = {}
_cache_time = 0.0
_cache_lock = Lock()

CHARTS = [
    {"category": "calidad", "title": "Resumen de calidad", "query": "03_resumen_calidad", "type": "bar", "x": "metric", "y": "value"},
    {"category": "temporal", "title": "Reportes por año", "query": "08_distribucion_anio_mes", "type": "year"},
    {"category": "temporal", "title": "Tendencia semanal", "query": "09_tendencia_semanal", "type": "line", "x": "report_week_start", "y": "reportes"},
    {"category": "territorio", "title": "Principales provincias", "query": "10_top_provincias", "type": "bar", "x": "provincia_name", "y": "reportes"},
    {"category": "operacional", "title": "Principales tipos de reporte", "query": "11_top_tipos_reporte", "type": "bar", "x": "report_type_name", "y": "reportes"},
    {"category": "operacional", "title": "Principales instituciones", "query": "12_top_instituciones", "type": "bar", "x": "company_name", "y": "reportes"},
    {"category": "calidad", "title": "Valores faltantes en reportes", "query": "04_faltantes_fact_reportes", "type": "bar", "x": "column_name", "y": "missing_pct"},
    {"category": "calidad", "title": "Valores faltantes en Dataset Maestro", "query": "05_faltantes_dataset_maestro", "type": "bar", "x": "column_name", "y": "missing_pct"},
    {"category": "calidad", "title": "Duplicados por clave o grano analítico", "query": "06_duplicados", "type": "bar", "x": "check_name", "y": "duplicated_keys"},
    {"category": "modelado", "title": "Distribución de la variable objetivo", "query": "14_distribucion_target", "type": "pie", "x": "target_class", "y": "filas"},
    {"category": "modelado", "title": "Correlaciones numéricas", "query": "16_correlaciones_numericas", "type": "bar", "x": "variable", "y": "corr_with_reportes_semana"},
    {"category": "modelado", "title": "Valores atípicos mediante IQR", "query": "15_outliers_iqr_reportes_semana", "type": "iqr"},
    {"category": "calidad", "title": "Controles de consistencia", "query": "07_consistencia", "type": "bar", "x": "check_name", "y": "affected_rows"},
    {"category": "territorio", "title": "Provincia frente a categoría", "query": "17_cruce_provincia_categoria", "type": "heatmap"},
]


def query_bigquery(force: bool = False) -> dict[str, pd.DataFrame]:
    """Consulta BigQuery y conserva una caché breve para controlar costes."""
    global _cache, _cache_time
    fresh = bool(_cache) and monotonic() - _cache_time < CACHE_TTL_SECONDS
    if fresh and not force:
        return _cache
    with _cache_lock:
        fresh = bool(_cache) and monotonic() - _cache_time < CACHE_TTL_SECONDS
        if fresh and not force:
            return _cache
        runner = BigQueryRunner()
        results = {name: runner.query_to_dataframe(sql) for name, sql in QUERIES.items()}
        _cache, _cache_time = results, monotonic()
        return _cache


def metric_map(results: dict[str, pd.DataFrame]) -> dict[str, int]:
    frame = results.get("03_resumen_calidad", pd.DataFrame())
    if frame.empty:
        return {}
    return {str(row.metric): int(float(row.value)) for row in frame.itertuples()}


@app.get("/")
def index():
    results = query_bigquery()
    metrics = metric_map(results)
    target = results.get("14_distribucion_target", pd.DataFrame())
    target_values = dict(zip(target.get("target_class", []), target.get("filas", [])))
    cards = [
        ("Reportes limpios", metrics.get("fact_reportes_limpios_total", 0)),
        ("Filas del Dataset Maestro", metrics.get("dataset_maestro_modelado_total", 0)),
        ("Filas con variable objetivo", metrics.get("dataset_maestro_con_target", 0)),
        ("Casos con incremento", int(target_values.get("incremento", 0))),
    ]
    return render_template(
        "index.html",
        cards=cards,
        charts=CHARTS,
        datasets=list(QUERIES),
        cache_minutes=CACHE_TTL_SECONDS // 60,
    )


@app.post("/refresh")
def refresh():
    query_bigquery(force=True)
    return redirect(url_for("index"))


@app.get("/plotly.js")
def plotly_js():
    return Response(get_plotlyjs(), mimetype="application/javascript")


@app.get("/data/<path:name>")
def data(name: str):
    if Path(name).name != name or name not in QUERIES:
        abort(404)
    frame = query_bigquery()[name]
    return {
        "name": name,
        "columns": list(frame.columns),
        "rows": frame.fillna("").astype(str).to_dict(orient="records"),
        "total": len(frame),
    }


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)
