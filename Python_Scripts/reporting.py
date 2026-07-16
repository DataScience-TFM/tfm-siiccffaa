from __future__ import annotations

from datetime import datetime

import pandas as pd

from .config import FIGURES_DIR, REPORTS_DIR


def to_int(value, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def to_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def metric(results: dict[str, pd.DataFrame], key: str) -> int:
    df = results["03_resumen_calidad"]
    row = df[df["metric"] == key]
    if row.empty:
        return 0
    return to_int(row.iloc[0]["value"])


def pct(part: int, total: int) -> str:
    if total == 0:
        return "0.00%"
    return f"{part * 100 / total:.2f}%"


def bullet_top(df: pd.DataFrame, label_col: str, value_col: str, n: int = 5) -> str:
    lines = []
    for _, row in df.head(n).iterrows():
        lines.append(f"- {row[label_col]}: {to_int(row[value_col]):,}")
    return "\n".join(lines)


def generate_markdown_reports(results: dict[str, pd.DataFrame]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    original = metric(results, "reports_original_total")
    clean = metric(results, "fact_reportes_limpios_total")
    removed = original - clean
    maestro = metric(results, "dataset_maestro_modelado_total")
    target = metric(results, "dataset_maestro_con_target")
    sin_prov = metric(results, "fact_reportes_sin_provincia")
    coord_valid = metric(results, "fact_reportes_con_coordenadas_validas")

    dup = {row["check_name"]: row for _, row in results["06_duplicados"].iterrows()}
    duplicate_reports = to_int(dup.get("fact_reportes_limpios.report_id", {}).get("duplicated_keys", 0))
    duplicate_grain = to_int(dup.get("dataset_maestro_modelado.grain", {}).get("duplicated_keys", 0))

    outlier = results["15_outliers_iqr_reportes_semana"].iloc[0]
    target_dist = dict(zip(results["14_distribucion_target"]["target_class"], results["14_distribucion_target"]["filas"]))
    report_group = results["20_verificacion_dim_report_group"].iloc[0]

    template = f"""# Plantilla de documentación EDA y limpieza - Proyecto Python

Fecha de generación: {now}

## Objetivo del EDA

El objetivo del análisis exploratorio fue ejecutar de forma práctica el ciclo de Ciencia de Datos sobre el dataset limpio `tfm-sbs.siiccffaa_clean`, validando estructura, calidad, faltantes, duplicados, consistencia, outliers, distribuciones y relaciones entre variables. El resultado sirve como evidencia técnica para el TFM y como base para continuar con modelado predictivo sobre el Dataset Maestro.

## Metodología

1. **Carga inicial de datos.** El proyecto Python se conecta mediante HTTPS a la API REST de BigQuery y ejecuta consultas SQL reproducibles.
2. **Revisión de estructura.** Se inspeccionan tablas, columnas y tipos de datos del esquema `siiccffaa_clean`.
3. **Valores faltantes.** Se calcula el porcentaje de faltantes en la tabla de hechos y en el Dataset Maestro.
4. **Duplicados.** Se valida la unicidad de `report_id` y el grano semanal `report_week_start + provincia_id + report_type_id`.
5. **Consistencia.** Se revisan fechas, provincia, coordenadas, rezagos y target.
6. **Outliers.** Se aplica IQR sobre `reportes_semana`.
7. **Distribuciones.** Se generan gráficos por año, semana, provincia, tipo de reporte, institución, estado y variable objetivo.
8. **Relaciones.** Se calculan correlaciones entre `reportes_semana` y variables temporales derivadas.

## Hallazgos

- Registros originales en `siiccffaa.reports`: **{original:,}**.
- Registros conservados en `fact_reportes_limpios`: **{clean:,}**.
- Registros excluidos por limpieza inicial: **{removed:,}** ({pct(removed, original)}).
- Filas del Dataset Maestro: **{maestro:,}**.
- Filas con target disponible: **{target:,}** ({pct(target, maestro)}).
- Reportes sin provincia: **{sin_prov:,}** ({pct(sin_prov, clean)}). Se conservan para análisis general, pero no se usan en agregados territoriales.
- Reportes con coordenadas válidas: **{coord_valid:,}** ({pct(coord_valid, clean)}). La visualización geográfica debe apoyarse principalmente en provincia/municipio.
- Duplicados por `report_id`: **{duplicate_reports:,}**.
- Duplicados del grano semanal del Dataset Maestro: **{duplicate_grain:,}**. Se documentan para consolidación previa al modelado.
- Outliers IQR en `reportes_semana`: **{to_int(outlier['outlier_rows']):,}** filas ({outlier['outlier_pct']}%).
- Verificación de `dim_report_group`: **{to_int(report_group['total_filas']):,}** filas, **{to_int(report_group['activos']):,}** activas.
- Distribución del target: {target_dist}.

### Principales provincias por volumen

{bullet_top(results["10_top_provincias"], "provincia_name", "reportes")}

### Principales tipos de reporte

{bullet_top(results["11_top_tipos_reporte"], "report_type_name", "reportes")}

### Principales instituciones reportantes

{bullet_top(results["12_top_instituciones"], "company_name", "reportes")}

## Decisiones de limpieza

| Área | Decisión aplicada | Justificación técnica |
|---|---|---|
| Fechas | Se conservaron fechas válidas dentro del rango operativo. | Evitar registros fuera de contexto temporal. |
| Texto | Se normalizaron títulos y descripciones. | Reducir ruido y proteger datos sensibles. |
| Geografía | Se usó provincia directa o puente cuando existía evidencia. | No imputar territorio sin respaldo. |
| Coordenadas | Se marcaron válidas solo cuando caen en rango razonable de República Dominicana. | Evitar mapas con puntos erróneos. |
| Duplicados | Se validó `report_id` como clave de la tabla limpia. | Mantener una operación por registro. |
| Grano semanal | Se documentaron duplicados por semana, provincia y tipo. | Consolidar antes del entrenamiento predictivo. |
| Riesgo | No se usaron campos `risk_*` no documentados. | Mantener interpretabilidad y defensa académica. |

## Justificación técnica

- **Reproducibilidad:** el proyecto genera `script_sql/eda_queries.sql`, CSV, gráficos y reportes con un único comando.
- **Control de versiones:** se distingue dataset original, dataset limpio y Dataset Maestro.
- **Coherencia con el negocio:** no se eliminan reportes por falta de provincia; solo se restringen análisis territoriales cuando no hay ubicación.
- **Integridad:** se evitan imputaciones agresivas que alteren la distribución real.
- **No fuga temporal:** los rezagos y medias móviles se calculan con periodos previos al objetivo.

## Visualizaciones recomendadas

Las visualizaciones generadas están en `outputs/figures/`:

1. Ciclo práctico de Ciencia de Datos.
2. Resumen de calidad.
3. Reportes por año.
4. Tendencia semanal.
5. Principales provincias.
6. Principales tipos de reporte.
7. Principales instituciones.
8. Faltantes en tabla de hechos.
9. Faltantes en Dataset Maestro.
10. Distribución de la variable objetivo.
11. Correlaciones numéricas.
12. Consistencia.
13. Cruce provincia vs categoría.
"""
    (REPORTS_DIR / "PLANTILLA_DOCUMENTACION_EDA_COMPLETA.md").write_text(template, encoding="utf-8")

    executive = f"""# Informe ejecutivo del análisis exploratorio

El proyecto Python ejecutó el análisis exploratorio sobre el esquema limpio `siiccffaa_clean` de BigQuery. La tabla de hechos conserva **{clean:,}** reportes limpios a partir de **{original:,}** registros originales. El Dataset Maestro contiene **{maestro:,}** combinaciones semanales por provincia y tipo de reporte, de las cuales **{target:,}** tienen variable objetivo disponible para análisis predictivo.

## Recomendaciones prácticas

1. Mantener la tabla `fact_reportes_limpios` como fuente principal para análisis descriptivo.
2. Usar `dataset_maestro_modelado` para análisis temporal y modelado predictivo.
3. Consolidar los **{duplicate_grain:,}** duplicados del grano semanal antes del entrenamiento.
4. Evitar modelos basados en coordenadas, porque solo **{coord_valid:,}** reportes tienen coordenadas válidas.
5. Conservar reportes sin provincia para estadísticas generales, pero excluirlos de mapas territoriales.
6. Usar rezagos y medias móviles como variables predictoras, porque presentan mayor relación con `reportes_semana`.

## Entregables generados

- `outputs/data/*.csv`
- `outputs/figures/*.png`
- `outputs/reports/PLANTILLA_DOCUMENTACION_EDA_COMPLETA.md`
- `outputs/reports/INFORME_EJECUTIVO_EDA.md`
- `outputs/reports/dashboard_eda.html`
"""
    (REPORTS_DIR / "INFORME_EJECUTIVO_EDA.md").write_text(executive, encoding="utf-8")


def generate_dashboard_html() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    figures = [
        ("Ciclo práctico", "01_ciclo_practico_ciencia_datos.png"),
        ("Resumen de calidad", "02_resumen_calidad_dataset.png"),
        ("Reportes por año", "03_reportes_por_anio.png"),
        ("Tendencia semanal", "04_tendencia_semanal.png"),
        ("Top provincias", "05_top_provincias.png"),
        ("Top tipos de reporte", "06_top_tipos_reporte.png"),
        ("Top instituciones", "07_top_instituciones.png"),
        ("Faltantes en reportes", "08_faltantes_fact_reportes.png"),
        ("Faltantes en Dataset Maestro", "09_faltantes_dataset_maestro.png"),
        ("Variable objetivo", "10_distribucion_target.png"),
        ("Correlaciones", "11_correlaciones_numericas.png"),
        ("Consistencia", "12_consistencia.png"),
        ("Provincia vs categoría", "13_heatmap_provincia_categoria.png"),
    ]
    cards = "\n".join(
        f"""
        <section class="card">
          <h2>{title}</h2>
          <img src="../figures/{filename}" alt="{title}">
        </section>
        """
        for title, filename in figures
        if (FIGURES_DIR / filename).exists()
    )
    html = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Dashboard EDA SIICCFFAA</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f4f6f9; color: #172033; }}
    header {{ background: #1F4D78; color: white; padding: 28px 44px; }}
    main {{ padding: 28px 44px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(520px, 1fr)); gap: 22px; }}
    .card {{ background: white; border: 1px solid #d8dee8; border-radius: 8px; padding: 18px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; }}
    h2 {{ color: #1F4D78; font-size: 19px; margin: 0 0 12px; }}
    img {{ width: 100%; height: auto; border: 1px solid #edf0f5; }}
    .note {{ background: #fff8e5; border-left: 5px solid #B7791F; padding: 14px 18px; margin-bottom: 24px; }}
  </style>
</head>
<body>
  <header>
    <h1>Dashboard EDA - SIICCFFAA</h1>
    <p>Análisis exploratorio práctico sobre el dataset limpio de BigQuery.</p>
  </header>
  <main>
    <div class="note">
      Este dashboard es una evidencia visual del ciclo realizado: carga, calidad, limpieza, distribuciones, relaciones y preparación para modelado.
    </div>
    <div class="grid">
      {cards}
    </div>
  </main>
</body>
</html>
"""
    (REPORTS_DIR / "dashboard_eda.html").write_text(html, encoding="utf-8")
