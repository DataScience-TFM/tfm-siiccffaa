from __future__ import annotations

from .config import CLEAN, SOURCE


QUERIES: dict[str, str] = {
    "01_conteo_tablas_limpias": f"""
        SELECT 'dim_region' AS table_name, COUNT(*) AS row_count FROM {CLEAN}.dim_region
        UNION ALL SELECT 'dim_provincia', COUNT(*) FROM {CLEAN}.dim_provincia
        UNION ALL SELECT 'dim_municipio', COUNT(*) FROM {CLEAN}.dim_municipio
        UNION ALL SELECT 'dim_report_type', COUNT(*) FROM {CLEAN}.dim_report_type
        UNION ALL SELECT 'dim_report_group', COUNT(*) FROM {CLEAN}.dim_report_group
        UNION ALL SELECT 'dim_company', COUNT(*) FROM {CLEAN}.dim_company
        UNION ALL SELECT 'dim_branch', COUNT(*) FROM {CLEAN}.dim_branch
        UNION ALL SELECT 'dim_company_department', COUNT(*) FROM {CLEAN}.dim_company_department
        UNION ALL SELECT 'fact_reportes_limpios', COUNT(*) FROM {CLEAN}.fact_reportes_limpios
        UNION ALL SELECT 'agg_reportes_semanal', COUNT(*) FROM {CLEAN}.agg_reportes_semanal
        UNION ALL SELECT 'dataset_maestro_modelado', COUNT(*) FROM {CLEAN}.dataset_maestro_modelado
        ORDER BY row_count DESC
    """,
    "02_estructura_tablas_limpias": """
        SELECT table_name, ordinal_position, column_name, data_type, is_nullable
        FROM `tfm-sbs.siiccffaa_clean.INFORMATION_SCHEMA.COLUMNS`
        ORDER BY table_name, ordinal_position
    """,
    "03_resumen_calidad": f"""
        SELECT metric, value
        FROM {CLEAN}.data_quality_summary
        ORDER BY metric
    """,
    "04_faltantes_fact_reportes": f"""
        WITH base AS (SELECT COUNT(*) AS total FROM {CLEAN}.fact_reportes_limpios)
        SELECT 'report_id' AS column_name, COUNTIF(report_id IS NULL) AS missing_count, ROUND(100 * COUNTIF(report_id IS NULL) / total, 2) AS missing_pct FROM {CLEAN}.fact_reportes_limpios, base GROUP BY total
        UNION ALL SELECT 'report_code', COUNTIF(report_code IS NULL), ROUND(100 * COUNTIF(report_code IS NULL) / total, 2) FROM {CLEAN}.fact_reportes_limpios, base GROUP BY total
        UNION ALL SELECT 'report_date', COUNTIF(report_date IS NULL), ROUND(100 * COUNTIF(report_date IS NULL) / total, 2) FROM {CLEAN}.fact_reportes_limpios, base GROUP BY total
        UNION ALL SELECT 'report_type_name', COUNTIF(report_type_name IS NULL), ROUND(100 * COUNTIF(report_type_name IS NULL) / total, 2) FROM {CLEAN}.fact_reportes_limpios, base GROUP BY total
        UNION ALL SELECT 'company_name', COUNTIF(company_name IS NULL), ROUND(100 * COUNTIF(company_name IS NULL) / total, 2) FROM {CLEAN}.fact_reportes_limpios, base GROUP BY total
        UNION ALL SELECT 'provincia_name', COUNTIF(provincia_name IS NULL), ROUND(100 * COUNTIF(provincia_name IS NULL) / total, 2) FROM {CLEAN}.fact_reportes_limpios, base GROUP BY total
        UNION ALL SELECT 'latitude_clean', COUNTIF(latitude_clean IS NULL), ROUND(100 * COUNTIF(latitude_clean IS NULL) / total, 2) FROM {CLEAN}.fact_reportes_limpios, base GROUP BY total
        UNION ALL SELECT 'longitude_clean', COUNTIF(longitude_clean IS NULL), ROUND(100 * COUNTIF(longitude_clean IS NULL) / total, 2) FROM {CLEAN}.fact_reportes_limpios, base GROUP BY total
        UNION ALL SELECT 'description_clean', COUNTIF(description_clean IS NULL), ROUND(100 * COUNTIF(description_clean IS NULL) / total, 2) FROM {CLEAN}.fact_reportes_limpios, base GROUP BY total
        ORDER BY missing_pct DESC, column_name
    """,
    "05_faltantes_dataset_maestro": f"""
        WITH base AS (SELECT COUNT(*) AS total FROM {CLEAN}.dataset_maestro_modelado)
        SELECT 'report_week_start' AS column_name, COUNTIF(report_week_start IS NULL) AS missing_count, ROUND(100 * COUNTIF(report_week_start IS NULL) / total, 2) AS missing_pct FROM {CLEAN}.dataset_maestro_modelado, base GROUP BY total
        UNION ALL SELECT 'provincia_id', COUNTIF(provincia_id IS NULL), ROUND(100 * COUNTIF(provincia_id IS NULL) / total, 2) FROM {CLEAN}.dataset_maestro_modelado, base GROUP BY total
        UNION ALL SELECT 'report_type_id', COUNTIF(report_type_id IS NULL), ROUND(100 * COUNTIF(report_type_id IS NULL) / total, 2) FROM {CLEAN}.dataset_maestro_modelado, base GROUP BY total
        UNION ALL SELECT 'reportes_semana', COUNTIF(reportes_semana IS NULL), ROUND(100 * COUNTIF(reportes_semana IS NULL) / total, 2) FROM {CLEAN}.dataset_maestro_modelado, base GROUP BY total
        UNION ALL SELECT 'reportes_lag_1w', COUNTIF(reportes_lag_1w IS NULL), ROUND(100 * COUNTIF(reportes_lag_1w IS NULL) / total, 2) FROM {CLEAN}.dataset_maestro_modelado, base GROUP BY total
        UNION ALL SELECT 'reportes_media_4w_previa', COUNTIF(reportes_media_4w_previa IS NULL), ROUND(100 * COUNTIF(reportes_media_4w_previa IS NULL) / total, 2) FROM {CLEAN}.dataset_maestro_modelado, base GROUP BY total
        UNION ALL SELECT 'incremento_actividad_siguiente_periodo', COUNTIF(incremento_actividad_siguiente_periodo IS NULL), ROUND(100 * COUNTIF(incremento_actividad_siguiente_periodo IS NULL) / total, 2) FROM {CLEAN}.dataset_maestro_modelado, base GROUP BY total
        ORDER BY missing_pct DESC, column_name
    """,
    "06_duplicados": f"""
        SELECT 'fact_reportes_limpios.report_id' AS check_name, COUNT(*) AS total_rows, COUNT(DISTINCT report_id) AS distinct_keys, COUNT(*) - COUNT(DISTINCT report_id) AS duplicated_keys
        FROM {CLEAN}.fact_reportes_limpios
        UNION ALL
        SELECT 'fact_reportes_limpios.report_code_non_null', COUNTIF(report_code IS NOT NULL), COUNT(DISTINCT report_code), COUNTIF(report_code IS NOT NULL) - COUNT(DISTINCT report_code)
        FROM {CLEAN}.fact_reportes_limpios
        UNION ALL
        SELECT 'dataset_maestro_modelado.grain', COUNT(*), COUNT(DISTINCT CONCAT(CAST(report_week_start AS STRING), '|', CAST(provincia_id AS STRING), '|', CAST(report_type_id AS STRING))), COUNT(*) - COUNT(DISTINCT CONCAT(CAST(report_week_start AS STRING), '|', CAST(provincia_id AS STRING), '|', CAST(report_type_id AS STRING)))
        FROM {CLEAN}.dataset_maestro_modelado
    """,
    "07_consistencia": f"""
        SELECT 'fact_fecha_nula' AS check_name, COUNTIF(report_date IS NULL) AS affected_rows FROM {CLEAN}.fact_reportes_limpios
        UNION ALL SELECT 'fecha_fuera_rango_original', COUNTIF(created_on < DATE '2021-01-01' OR created_on > CURRENT_DATE()) FROM {SOURCE}.reports
        UNION ALL SELECT 'fact_sin_provincia', COUNTIF(provincia_id IS NULL) FROM {CLEAN}.fact_reportes_limpios
        UNION ALL SELECT 'fact_coordenadas_invalidas_o_nulas', COUNTIF(NOT has_valid_coordinates) FROM {CLEAN}.fact_reportes_limpios
        UNION ALL SELECT 'dataset_target_nulo', COUNTIF(incremento_actividad_siguiente_periodo IS NULL) FROM {CLEAN}.dataset_maestro_modelado
        UNION ALL SELECT 'dataset_lag1_nulo', COUNTIF(reportes_lag_1w IS NULL) FROM {CLEAN}.dataset_maestro_modelado
    """,
    "08_distribucion_anio_mes": f"""
        SELECT report_year, report_month, COUNT(*) AS reportes
        FROM {CLEAN}.fact_reportes_limpios
        GROUP BY report_year, report_month
        ORDER BY report_year, report_month
    """,
    "09_tendencia_semanal": f"""
        SELECT report_week_start, SUM(reportes_semana) AS reportes
        FROM {CLEAN}.dataset_maestro_modelado
        GROUP BY report_week_start
        ORDER BY report_week_start
    """,
    "10_top_provincias": f"""
        SELECT COALESCE(provincia_name, 'sin_provincia') AS provincia_name, COUNT(*) AS reportes
        FROM {CLEAN}.fact_reportes_limpios
        GROUP BY provincia_name
        ORDER BY reportes DESC
        LIMIT 15
    """,
    "11_top_tipos_reporte": f"""
        SELECT COALESCE(report_type_name, 'sin_tipo_reporte') AS report_type_name, COUNT(*) AS reportes
        FROM {CLEAN}.fact_reportes_limpios
        GROUP BY report_type_name
        ORDER BY reportes DESC
        LIMIT 15
    """,
    "12_top_instituciones": f"""
        SELECT COALESCE(company_name, 'sin_institucion') AS company_name, COUNT(*) AS reportes
        FROM {CLEAN}.fact_reportes_limpios
        GROUP BY company_name
        ORDER BY reportes DESC
        LIMIT 15
    """,
    "13_estado_reportes": f"""
        SELECT COALESCE(status_norm, 'sin_estado') AS status_norm, COUNT(*) AS reportes
        FROM {CLEAN}.fact_reportes_limpios
        GROUP BY status_norm
        ORDER BY reportes DESC
    """,
    "14_distribucion_target": f"""
        SELECT
          CASE
            WHEN incremento_actividad_siguiente_periodo IS NULL THEN 'sin_target'
            WHEN incremento_actividad_siguiente_periodo = 1 THEN 'incremento'
            ELSE 'no_incremento'
          END AS target_class,
          COUNT(*) AS filas
        FROM {CLEAN}.dataset_maestro_modelado
        GROUP BY target_class
        ORDER BY filas DESC
    """,
    "15_outliers_iqr_reportes_semana": f"""
        WITH stats AS (
          SELECT
            APPROX_QUANTILES(reportes_semana, 4)[OFFSET(1)] AS q1,
            APPROX_QUANTILES(reportes_semana, 4)[OFFSET(3)] AS q3
          FROM {CLEAN}.dataset_maestro_modelado
        ),
        limits AS (
          SELECT q1, q3, q3 - q1 AS iqr, q1 - 1.5 * (q3 - q1) AS lower_limit, q3 + 1.5 * (q3 - q1) AS upper_limit
          FROM stats
        )
        SELECT
          q1, q3, iqr, lower_limit, upper_limit,
          COUNT(*) AS total_rows,
          COUNTIF(reportes_semana < lower_limit OR reportes_semana > upper_limit) AS outlier_rows,
          ROUND(100 * COUNTIF(reportes_semana < lower_limit OR reportes_semana > upper_limit) / COUNT(*), 2) AS outlier_pct,
          MIN(reportes_semana) AS min_value,
          MAX(reportes_semana) AS max_value,
          AVG(reportes_semana) AS avg_value
        FROM {CLEAN}.dataset_maestro_modelado, limits
        GROUP BY q1, q3, iqr, lower_limit, upper_limit
    """,
    "16_correlaciones_numericas": f"""
        SELECT 'reportes_lag_1w' AS variable, CORR(CAST(reportes_semana AS FLOAT64), CAST(reportes_lag_1w AS FLOAT64)) AS corr_with_reportes_semana FROM {CLEAN}.dataset_maestro_modelado WHERE reportes_lag_1w IS NOT NULL
        UNION ALL SELECT 'reportes_lag_2w', CORR(CAST(reportes_semana AS FLOAT64), CAST(reportes_lag_2w AS FLOAT64)) FROM {CLEAN}.dataset_maestro_modelado WHERE reportes_lag_2w IS NOT NULL
        UNION ALL SELECT 'reportes_lag_4w', CORR(CAST(reportes_semana AS FLOAT64), CAST(reportes_lag_4w AS FLOAT64)) FROM {CLEAN}.dataset_maestro_modelado WHERE reportes_lag_4w IS NOT NULL
        UNION ALL SELECT 'reportes_media_4w_previa', CORR(CAST(reportes_semana AS FLOAT64), CAST(reportes_media_4w_previa AS FLOAT64)) FROM {CLEAN}.dataset_maestro_modelado WHERE reportes_media_4w_previa IS NOT NULL
        UNION ALL SELECT 'variacion_pct_1w', CORR(CAST(reportes_semana AS FLOAT64), CAST(variacion_pct_1w AS FLOAT64)) FROM {CLEAN}.dataset_maestro_modelado WHERE variacion_pct_1w IS NOT NULL
        UNION ALL SELECT 'instituciones_distintas', CORR(CAST(reportes_semana AS FLOAT64), CAST(instituciones_distintas AS FLOAT64)) FROM {CLEAN}.dataset_maestro_modelado WHERE instituciones_distintas IS NOT NULL
        ORDER BY ABS(corr_with_reportes_semana) DESC
    """,
    "17_cruce_provincia_categoria": f"""
        SELECT provincia_name, COALESCE(report_type_category, 'sin_categoria') AS report_type_category, COUNT(*) AS reportes
        FROM {CLEAN}.fact_reportes_limpios
        WHERE provincia_name IS NOT NULL
        GROUP BY provincia_name, report_type_category
        ORDER BY reportes DESC
        LIMIT 60
    """,
    "18_detalle_duplicados_grano": f"""
        SELECT
          report_week_start,
          provincia_id,
          provincia_name,
          report_type_id,
          report_type_name,
          COUNT(*) AS filas,
          SUM(reportes_semana) AS reportes_semana_total
        FROM {CLEAN}.dataset_maestro_modelado
        GROUP BY report_week_start, provincia_id, provincia_name, report_type_id, report_type_name
        HAVING COUNT(*) > 1
        ORDER BY filas DESC, report_week_start, provincia_name, report_type_name
        LIMIT 100
    """,
    "19_auditoria_limpieza": f"""
        SELECT 'fechas' AS area, 'created_on convertido/validado como DATE; rango 2021-01-01 a CURRENT_DATE' AS decision, CAST(COUNTIF(created_on < DATE '2021-01-01' OR created_on > CURRENT_DATE()) AS STRING) AS evidencia
        FROM {SOURCE}.reports
        UNION ALL SELECT 'texto', 'title y description normalizados con TRIM, REGEXP_REPLACE y redacción de emails/teléfonos', CAST(COUNT(*) AS STRING) FROM {CLEAN}.fact_reportes_limpios
        UNION ALL SELECT 'coordenadas', 'latitud/longitud válidas solo si caen dentro de rango aproximado de República Dominicana', CAST(COUNTIF(has_valid_coordinates) AS STRING) FROM {CLEAN}.fact_reportes_limpios
        UNION ALL SELECT 'geografía', 'provincia tomada de reports o puente reports__provincias; se conserva nulo si no existe evidencia territorial', CAST(COUNTIF(provincia_id IS NULL) AS STRING) FROM {CLEAN}.fact_reportes_limpios
        UNION ALL SELECT 'duplicados', 'report_id usado como clave de reporte limpio', CAST(COUNT(*) - COUNT(DISTINCT report_id) AS STRING) FROM {CLEAN}.fact_reportes_limpios
        UNION ALL SELECT 'modelado', 'target creado con comparación contra media móvil de cuatro semanas previas', CAST(COUNTIF(incremento_actividad_siguiente_periodo IS NOT NULL) AS STRING) FROM {CLEAN}.dataset_maestro_modelado
    """,
    "20_verificacion_dim_report_group": f"""
        SELECT
          COUNT(*) AS total_filas,
          COUNTIF(report_group_id IS NULL) AS id_nulo,
          COUNTIF(report_group_name IS NULL) AS nombre_nulo,
          COUNTIF(active) AS activos
        FROM {CLEAN}.dim_report_group
    """,
}

