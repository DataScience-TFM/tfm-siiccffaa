-- Corrección del grano semanal en semanas que cruzan el cambio de año.
-- Se conservan respaldos previos para permitir auditoría o reversión.

CREATE TABLE IF NOT EXISTS `tfm-sbs.siiccffaa_clean.agg_reportes_semanal_before_dedup_20260716` AS
SELECT * FROM `tfm-sbs.siiccffaa_clean.agg_reportes_semanal`;

CREATE TABLE IF NOT EXISTS `tfm-sbs.siiccffaa_clean.dataset_maestro_modelado_before_dedup_20260716` AS
SELECT * FROM `tfm-sbs.siiccffaa_clean.dataset_maestro_modelado`;

CREATE OR REPLACE TABLE `tfm-sbs.siiccffaa_clean.agg_reportes_semanal`
PARTITION BY report_week_start
CLUSTER BY provincia_id, report_type_id AS
SELECT
  report_week_start,
  EXTRACT(ISOYEAR FROM report_week_start) AS report_year,
  EXTRACT(ISOWEEK FROM report_week_start) AS report_iso_week,
  provincia_id,
  ANY_VALUE(COALESCE(provincia_name, 'sin_provincia')) AS provincia_name,
  ANY_VALUE(region_id) AS region_id,
  ANY_VALUE(COALESCE(region_name, 'sin_region')) AS region_name,
  report_type_id,
  ANY_VALUE(report_type_name) AS report_type_name,
  ANY_VALUE(report_type_category) AS report_type_category,
  COUNT(*) AS reportes_semana,
  COUNTIF(has_media) AS reportes_con_media,
  COUNTIF(has_valid_coordinates) AS reportes_con_coordenadas_validas,
  COUNT(DISTINCT company_id) AS instituciones_distintas,
  COUNT(DISTINCT branch_id) AS dependencias_distintas,
  AVG(description_length) AS descripcion_longitud_media,
  COUNTIF(status_norm = 'completado') AS reportes_completados
FROM `tfm-sbs.siiccffaa_clean.fact_reportes_limpios`
WHERE provincia_id IS NOT NULL
  AND report_type_id IS NOT NULL
GROUP BY report_week_start, provincia_id, report_type_id;

CREATE OR REPLACE TABLE `tfm-sbs.siiccffaa_clean.dataset_maestro_modelado`
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
  FROM `tfm-sbs.siiccffaa_clean.agg_reportes_semanal`
  WINDOW w AS (
    PARTITION BY provincia_id, report_type_id
    ORDER BY report_week_start
  )
)
SELECT
  *,
  SAFE_DIVIDE(
    reportes_semana - reportes_lag_1w,
    NULLIF(reportes_lag_1w, 0)
  ) AS variacion_pct_1w,
  SAFE_DIVIDE(
    reportes_semana - reportes_media_4w_previa,
    NULLIF(reportes_media_4w_previa, 0)
  ) AS variacion_pct_vs_media_4w,
  CASE
    WHEN reportes_siguiente_semana IS NULL
      OR reportes_media_4w_previa IS NULL THEN NULL
    WHEN reportes_siguiente_semana > reportes_media_4w_previa THEN 1
    ELSE 0
  END AS incremento_actividad_siguiente_periodo
FROM base;

MERGE `tfm-sbs.siiccffaa_clean.data_quality_summary` AS target
USING (
  SELECT 'agg_reportes_semanal_total' AS metric, CAST(COUNT(*) AS STRING) AS value
  FROM `tfm-sbs.siiccffaa_clean.agg_reportes_semanal`
  UNION ALL
  SELECT 'dataset_maestro_modelado_total', CAST(COUNT(*) AS STRING)
  FROM `tfm-sbs.siiccffaa_clean.dataset_maestro_modelado`
  UNION ALL
  SELECT 'dataset_maestro_con_target',
         CAST(COUNTIF(incremento_actividad_siguiente_periodo IS NOT NULL) AS STRING)
  FROM `tfm-sbs.siiccffaa_clean.dataset_maestro_modelado`
) AS source
ON target.metric = source.metric
WHEN MATCHED THEN UPDATE SET value = source.value
WHEN NOT MATCHED THEN INSERT (metric, value) VALUES (source.metric, source.value);

-- Debe devolver duplicated_rows = 0.
WITH grain AS (
  SELECT report_week_start, provincia_id, report_type_id, COUNT(*) AS rows_per_grain
  FROM `tfm-sbs.siiccffaa_clean.dataset_maestro_modelado`
  GROUP BY report_week_start, provincia_id, report_type_id
)
SELECT
  SUM(rows_per_grain) AS total_rows,
  COUNT(*) AS distinct_grain,
  SUM(rows_per_grain - 1) AS duplicated_rows
FROM grain;
