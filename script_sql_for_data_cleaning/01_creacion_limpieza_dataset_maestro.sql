-- EVIDENCIA DEL PROCESO REAL DE PREPARACI?N Y LIMPIEZA EN BIGQUERY
-- Proyecto: tfm-sbs
-- Fuente: tfm-sbs.siiccffaa
-- Destino: tfm-sbs.siiccffaa_clean
-- Las sentencias se presentan en el mismo orden del script original.


-- ============================================================
-- 01. Creaci?n del dataset limpio
-- ============================================================
CREATE SCHEMA IF NOT EXISTS `tfm-sbs.siiccffaa_clean`
    OPTIONS (
      location = "europe-southwest1",
      description = "Dataset limpio y analitico del SIICCFFAA para el TFM: dimensiones, reportes depurados, agregados semanales y dataset maestro de modelado."
    );


-- ============================================================
-- 02. Dimensi?n de regiones
-- ============================================================
CREATE OR REPLACE TABLE `tfm-sbs.siiccffaa_clean`.dim_region AS
    SELECT
      id AS region_id,
      REGEXP_REPLACE(TRIM(name), r'\s+', ' ') AS region_name
    FROM `tfm-sbs.siiccffaa`.regions
    WHERE id IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC, created_at DESC) = 1;


-- ============================================================
-- 03. Dimensi?n de provincias
-- ============================================================
CREATE OR REPLACE TABLE `tfm-sbs.siiccffaa_clean`.dim_provincia AS
    SELECT
      p.id AS provincia_id,
      REGEXP_REPLACE(TRIM(p.name), r'\s+', ' ') AS provincia_name,
      p.region AS region_id,
      r.region_name
    FROM `tfm-sbs.siiccffaa`.provincias p
    LEFT JOIN `tfm-sbs.siiccffaa_clean`.dim_region r ON r.region_id = p.region
    WHERE p.id IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY p.id ORDER BY p.updated_at DESC, p.created_at DESC) = 1;


-- ============================================================
-- 04. Dimensi?n de municipios
-- ============================================================
CREATE OR REPLACE TABLE `tfm-sbs.siiccffaa_clean`.dim_municipio AS
    SELECT
      m.id AS municipio_id,
      REGEXP_REPLACE(TRIM(m.name), r'\s+', ' ') AS municipio_name,
      m.provincia AS provincia_id,
      p.provincia_name,
      p.region_id,
      p.region_name
    FROM `tfm-sbs.siiccffaa`.municipios m
    LEFT JOIN `tfm-sbs.siiccffaa_clean`.dim_provincia p ON p.provincia_id = m.provincia
    WHERE m.id IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY m.id ORDER BY m.updated_at DESC, m.created_at DESC) = 1;


-- ============================================================
-- 05. Dimensi?n de tipos de reporte
-- ============================================================
CREATE OR REPLACE TABLE `tfm-sbs.siiccffaa_clean`.dim_report_type AS
    SELECT
      id AS report_type_id,
      REGEXP_REPLACE(TRIM(name), r'\s+', ' ') AS report_type_name,
      REGEXP_REPLACE(TRIM(category), r'\s+', ' ') AS report_type_category,
      company AS company_id,
      branch AS branch_id,
      priority AS report_type_priority,
      COALESCE(active, TRUE) AS active,
      require_validation,
      ext_table_name
    FROM `tfm-sbs.siiccffaa`.report_types
    WHERE id IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC, created_at DESC) = 1;


-- ============================================================
-- 06. Dimensi?n de instituciones
-- ============================================================
CREATE OR REPLACE TABLE `tfm-sbs.siiccffaa_clean`.dim_company AS
    SELECT
      id AS company_id,
      REGEXP_REPLACE(TRIM(name), r'\s+', ' ') AS company_name,
      REGEXP_REPLACE(TRIM(code), r'\s+', ' ') AS company_code,
      priority AS company_priority,
      country AS country_id
    FROM `tfm-sbs.siiccffaa`.companies
    WHERE id IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC, created_at DESC) = 1;


-- ============================================================
-- 07. Dimensi?n de dependencias
-- ============================================================
CREATE OR REPLACE TABLE `tfm-sbs.siiccffaa_clean`.dim_branch AS
    SELECT
      b.id AS branch_id,
      REGEXP_REPLACE(TRIM(b.name), r'\s+', ' ') AS branch_name,
      b.company AS company_id,
      c.company_name,
      IF(b.latitude BETWEEN 17.0 AND 20.5 AND b.longitude BETWEEN -72.5 AND -68.0, b.latitude, NULL) AS branch_latitude,
      IF(b.latitude BETWEEN 17.0 AND 20.5 AND b.longitude BETWEEN -72.5 AND -68.0, b.longitude, NULL) AS branch_longitude,
      b.priority AS branch_priority,
      b.showInGraph AS show_in_graph
    FROM `tfm-sbs.siiccffaa`.branches b
    LEFT JOIN `tfm-sbs.siiccffaa_clean`.dim_company c ON c.company_id = b.company
    WHERE b.id IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY b.id ORDER BY b.updated_at DESC, b.created_at DESC) = 1;


-- ============================================================
-- 08. Dimensi?n de departamentos
-- ============================================================
CREATE OR REPLACE TABLE `tfm-sbs.siiccffaa_clean`.dim_company_department AS
    SELECT
      d.id AS company_department_id,
      REGEXP_REPLACE(TRIM(d.name), r'\s+', ' ') AS company_department_name,
      d.company AS company_id,
      c.company_name,
      REGEXP_REPLACE(TRIM(d.type), r'\s+', ' ') AS department_type
    FROM `tfm-sbs.siiccffaa`.company_departments d
    LEFT JOIN `tfm-sbs.siiccffaa_clean`.dim_company c ON c.company_id = d.company
    WHERE d.id IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY d.id ORDER BY d.updated_at DESC, d.created_at DESC) = 1;


-- ============================================================
-- 09. Dimensi?n de grupos de reporte
-- ============================================================
CREATE OR REPLACE TABLE `tfm-sbs.siiccffaa_clean`.dim_report_group AS
    SELECT
      g.id AS report_group_id,
      REGEXP_REPLACE(TRIM(g.name), r'\s+', ' ') AS report_group_name,
      REGEXP_REPLACE(TRIM(g.type), r'\s+', ' ') AS report_group_type,
      g.company AS company_id,
      c.company_name,
      g.priority AS report_group_priority,
      COALESCE(g.active, TRUE) AS active
    FROM `tfm-sbs.siiccffaa`.report_groups g
    LEFT JOIN `tfm-sbs.siiccffaa_clean`.dim_company c ON c.company_id = g.company
    WHERE g.id IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY g.id ORDER BY g.updated_at DESC, g.created_at DESC) = 1;


-- ============================================================
-- 10. Tabla de hechos de reportes limpios
-- ============================================================
CREATE OR REPLACE TABLE `tfm-sbs.siiccffaa_clean`.fact_reportes_limpios
    PARTITION BY report_date
    CLUSTER BY provincia_id, report_type_id, company_id AS
    WITH provincia_por_reporte AS (
      SELECT
        report_id,
        ARRAY_AGG(DISTINCT provincia_id IGNORE NULLS ORDER BY provincia_id LIMIT 1)[SAFE_OFFSET(0)] AS provincia_id_puente,
        COUNT(DISTINCT provincia_id) AS provincia_count
      FROM `tfm-sbs.siiccffaa`.reports__provincias
      GROUP BY report_id
    ),
    reportes_base AS (
      SELECT
        r.*,
        pp.provincia_id_puente,
        pp.provincia_count
      FROM `tfm-sbs.siiccffaa`.reports r
      LEFT JOIN provincia_por_reporte pp ON pp.report_id = r.id
      WHERE r.id IS NOT NULL
        AND r.created_on BETWEEN DATE '2021-01-01' AND CURRENT_DATE()
        AND r.deleted_on IS NULL
        AND r.deleted_by IS NULL
    ),
    texto AS (
      SELECT
        rb.*,
        REGEXP_REPLACE(
          REGEXP_REPLACE(
            REGEXP_REPLACE(TRIM(COALESCE(rb.title, '')), r'(?i)[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', '[EMAIL]'),
            r'\+?\d[\d\s\-\(\)]{7,}\d',
            '[TELEFONO]'
          ),
          r'\s+',
          ' '
        ) AS title_clean,
        REGEXP_REPLACE(
          REGEXP_REPLACE(
            REGEXP_REPLACE(TRIM(COALESCE(rb.description, '')), r'(?i)[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', '[EMAIL]'),
            r'\+?\d[\d\s\-\(\)]{7,}\d',
            '[TELEFONO]'
          ),
          r'\s+',
          ' '
        ) AS description_clean
      FROM reportes_base rb
    )
    SELECT
      t.id AS report_id,
      t.report_code,
      t.created_on AS report_date,
      t.created_at AS report_created_at,
      t.updated_at AS report_updated_at,
      t.created_hour AS report_time,
      EXTRACT(YEAR FROM t.created_on) AS report_year,
      EXTRACT(MONTH FROM t.created_on) AS report_month,
      EXTRACT(ISOWEEK FROM t.created_on) AS report_iso_week,
      DATE_TRUNC(t.created_on, WEEK(MONDAY)) AS report_week_start,

      t.report_type AS report_type_id,
      COALESCE(rt.report_type_name, CONCAT('SIN_DIMENSION_', CAST(t.report_type AS STRING))) AS report_type_name,
      COALESCE(rt.report_type_category, 'sin_categoria') AS report_type_category,

      t.company AS company_id,
      COALESCE(c.company_name, 'sin_institucion') AS company_name,
      t.branch AS branch_id,
      COALESCE(b.branch_name, 'sin_dependencia') AS branch_name,
      t.company_department AS company_department_id,
      cd.company_department_name,
      t.report_group AS report_group_id,
      rg.report_group_name,

      COALESCE(t.provincia, t.provincia_id_puente) AS provincia_id,
      p.provincia_name,
      COALESCE(t.region, p.region_id) AS region_id,
      COALESCE(rgion.region_name, p.region_name) AS region_name,

      IF(t.latitude BETWEEN 17.0 AND 20.5 AND t.longitude BETWEEN -72.5 AND -68.0, t.latitude, NULL) AS latitude_clean,
      IF(t.latitude BETWEEN 17.0 AND 20.5 AND t.longitude BETWEEN -72.5 AND -68.0, t.longitude, NULL) AS longitude_clean,
      t.latitude AS latitude_original,
      t.longitude AS longitude_original,
      t.latitude BETWEEN 17.0 AND 20.5 AND t.longitude BETWEEN -72.5 AND -68.0 AS has_valid_coordinates,

      LOWER(REGEXP_REPLACE(TRIM(COALESCE(t.status, 'sin_estado')), r'\s+', ' ')) AS status_norm,
      COALESCE(t.closed, FALSE) AS closed,
      COALESCE(t.has_media, FALSE) AS has_media,
      LOWER(REGEXP_REPLACE(TRIM(COALESCE(t.platform, 'sin_plataforma')), r'\s+', ' ')) AS platform_norm,
      t.weather_condition,
      SAFE_CAST(REGEXP_EXTRACT(t.weather_temp, r'-?\d+(?:\.\d+)?') AS FLOAT64) AS weather_temp_celsius,

      NULLIF(t.title_clean, '') AS title_clean,
      NULLIF(t.description_clean, '') AS description_clean,
      LENGTH(t.description_clean) AS description_length,
      t.provincia_count,
      CURRENT_TIMESTAMP() AS cleaned_at
    FROM texto t
    LEFT JOIN `tfm-sbs.siiccffaa_clean`.dim_report_type rt ON rt.report_type_id = t.report_type
    LEFT JOIN `tfm-sbs.siiccffaa_clean`.dim_company c ON c.company_id = t.company
    LEFT JOIN `tfm-sbs.siiccffaa_clean`.dim_branch b ON b.branch_id = t.branch
    LEFT JOIN `tfm-sbs.siiccffaa_clean`.dim_company_department cd ON cd.company_department_id = t.company_department
    LEFT JOIN `tfm-sbs.siiccffaa_clean`.dim_report_group rg ON rg.report_group_id = t.report_group
    LEFT JOIN `tfm-sbs.siiccffaa_clean`.dim_provincia p ON p.provincia_id = COALESCE(t.provincia, t.provincia_id_puente)
    LEFT JOIN `tfm-sbs.siiccffaa_clean`.dim_region rgion ON rgion.region_id = COALESCE(t.region, p.region_id);


-- ============================================================
-- 11. Agregaci?n semanal
-- ============================================================
CREATE OR REPLACE TABLE `tfm-sbs.siiccffaa_clean`.agg_reportes_semanal
    PARTITION BY report_week_start
    CLUSTER BY provincia_id, report_type_id AS
    SELECT
      report_week_start,
      report_year,
      report_iso_week,
      provincia_id,
      COALESCE(provincia_name, 'sin_provincia') AS provincia_name,
      region_id,
      COALESCE(region_name, 'sin_region') AS region_name,
      report_type_id,
      report_type_name,
      report_type_category,
      COUNT(*) AS reportes_semana,
      COUNTIF(has_media) AS reportes_con_media,
      COUNTIF(has_valid_coordinates) AS reportes_con_coordenadas_validas,
      COUNT(DISTINCT company_id) AS instituciones_distintas,
      COUNT(DISTINCT branch_id) AS dependencias_distintas,
      AVG(description_length) AS descripcion_longitud_media,
      COUNTIF(status_norm = 'completado') AS reportes_completados
    FROM `tfm-sbs.siiccffaa_clean`.fact_reportes_limpios
    WHERE provincia_id IS NOT NULL
      AND report_type_id IS NOT NULL
    GROUP BY
      report_week_start, report_year, report_iso_week,
      provincia_id, provincia_name, region_id, region_name,
      report_type_id, report_type_name, report_type_category;


-- ============================================================
-- 12. Dataset Maestro para modelado
-- ============================================================
CREATE OR REPLACE TABLE `tfm-sbs.siiccffaa_clean`.dataset_maestro_modelado
    PARTITION BY report_week_start
    CLUSTER BY provincia_id, report_type_id AS
    WITH base AS (
      SELECT
        *,
        LAG(reportes_semana, 1) OVER w AS reportes_lag_1w,
        LAG(reportes_semana, 2) OVER w AS reportes_lag_2w,
        LAG(reportes_semana, 4) OVER w AS reportes_lag_4w,
        AVG(reportes_semana) OVER (
          PARTITION BY provincia_id, report_type_id
          ORDER BY report_week_start
          ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING
        ) AS reportes_media_4w_previa,
        STDDEV_POP(reportes_semana) OVER (
          PARTITION BY provincia_id, report_type_id
          ORDER BY report_week_start
          ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING
        ) AS reportes_std_4w_previa,
        LEAD(reportes_semana, 1) OVER w AS reportes_siguiente_semana
      FROM `tfm-sbs.siiccffaa_clean`.agg_reportes_semanal
      WINDOW w AS (PARTITION BY provincia_id, report_type_id ORDER BY report_week_start)
    )
    SELECT
      *,
      SAFE_DIVIDE(reportes_semana - reportes_lag_1w, NULLIF(reportes_lag_1w, 0)) AS variacion_pct_1w,
      SAFE_DIVIDE(reportes_semana - reportes_media_4w_previa, NULLIF(reportes_media_4w_previa, 0)) AS variacion_pct_vs_media_4w,
      CASE
        WHEN reportes_siguiente_semana IS NULL OR reportes_media_4w_previa IS NULL THEN NULL
        WHEN reportes_siguiente_semana > reportes_media_4w_previa THEN 1
        ELSE 0
      END AS incremento_actividad_siguiente_periodo
    FROM base;


-- ============================================================
-- 13. Resumen de calidad
-- ============================================================
CREATE OR REPLACE TABLE `tfm-sbs.siiccffaa_clean`.data_quality_summary AS
    SELECT 'reports_original_total' AS metric, CAST(COUNT(*) AS STRING) AS value
    FROM `tfm-sbs.siiccffaa`.reports
    UNION ALL
    SELECT 'reports_fecha_fuera_rango', CAST(COUNTIF(created_on < DATE '2021-01-01' OR created_on > CURRENT_DATE()) AS STRING)
    FROM `tfm-sbs.siiccffaa`.reports
    UNION ALL
    SELECT 'fact_reportes_limpios_total', CAST(COUNT(*) AS STRING)
    FROM `tfm-sbs.siiccffaa_clean`.fact_reportes_limpios
    UNION ALL
    SELECT 'fact_reportes_sin_provincia', CAST(COUNTIF(provincia_id IS NULL) AS STRING)
    FROM `tfm-sbs.siiccffaa_clean`.fact_reportes_limpios
    UNION ALL
    SELECT 'fact_reportes_sin_nombre_tipo_reporte', CAST(COUNTIF(STARTS_WITH(report_type_name, 'SIN_DIMENSION_')) AS STRING)
    FROM `tfm-sbs.siiccffaa_clean`.fact_reportes_limpios
    UNION ALL
    SELECT 'fact_reportes_con_coordenadas_validas', CAST(COUNTIF(has_valid_coordinates) AS STRING)
    FROM `tfm-sbs.siiccffaa_clean`.fact_reportes_limpios
    UNION ALL
    SELECT 'agg_reportes_semanal_total', CAST(COUNT(*) AS STRING)
    FROM `tfm-sbs.siiccffaa_clean`.agg_reportes_semanal
    UNION ALL
    SELECT 'dataset_maestro_modelado_total', CAST(COUNT(*) AS STRING)
    FROM `tfm-sbs.siiccffaa_clean`.dataset_maestro_modelado
    UNION ALL
    SELECT 'dataset_maestro_con_target', CAST(COUNTIF(incremento_actividad_siguiente_periodo IS NOT NULL) AS STRING)
    FROM `tfm-sbs.siiccffaa_clean`.dataset_maestro_modelado;
