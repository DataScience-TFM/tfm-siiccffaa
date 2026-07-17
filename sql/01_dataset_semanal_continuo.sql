-- Completa semanas sin actividad para que LAG/LEAD representen semanas calendario.
-- No sustituye la tabla original: crea una tabla nueva y auditable.
CREATE OR REPLACE TABLE `tfm-sbs.siiccffaa_clean.dataset_maestro_modelado_continuo`
PARTITION BY report_week_start
CLUSTER BY provincia_id, report_type_id AS
WITH limites AS (
  SELECT
    provincia_id,
    report_type_id,
    MIN(report_week_start) AS primera_semana,
    MAX(report_week_start) AS ultima_semana
  FROM `tfm-sbs.siiccffaa_clean.agg_reportes_semanal`
  GROUP BY provincia_id, report_type_id
),
cuadricula AS (
  SELECT
    l.provincia_id,
    l.report_type_id,
    semana AS report_week_start
  FROM limites l,
  UNNEST(GENERATE_DATE_ARRAY(l.primera_semana, l.ultima_semana, INTERVAL 7 DAY)) AS semana
),
serie AS (
  SELECT
    c.report_week_start,
    c.provincia_id,
    c.report_type_id,
    COALESCE(a.provincia_name, p.provincia_name, 'sin_provincia') AS provincia_name,
    COALESCE(a.report_type_name, rt.report_type_name, 'sin_tipo') AS report_type_name,
    COALESCE(a.reportes_semana, 0) AS reportes_semana
  FROM cuadricula c
  LEFT JOIN `tfm-sbs.siiccffaa_clean.agg_reportes_semanal` a
    USING (report_week_start, provincia_id, report_type_id)
  LEFT JOIN `tfm-sbs.siiccffaa_clean.dim_provincia` p USING (provincia_id)
  LEFT JOIN `tfm-sbs.siiccffaa_clean.dim_report_type` rt USING (report_type_id)
),
historico AS (
  SELECT
    *,
    LAG(reportes_semana, 1) OVER w AS reportes_lag_1w,
    LAG(reportes_semana, 2) OVER w AS reportes_lag_2w,
    LAG(reportes_semana, 4) OVER w AS reportes_lag_4w,
    AVG(reportes_semana) OVER (
      PARTITION BY provincia_id, report_type_id ORDER BY report_week_start
      ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING
    ) AS reportes_media_4w_previa,
    STDDEV_POP(reportes_semana) OVER (
      PARTITION BY provincia_id, report_type_id ORDER BY report_week_start
      ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING
    ) AS reportes_std_4w_previa,
    LEAD(reportes_semana, 1) OVER w AS reportes_siguiente_semana
  FROM serie
  WINDOW w AS (PARTITION BY provincia_id, report_type_id ORDER BY report_week_start)
)
SELECT
  *,
  EXTRACT(ISOYEAR FROM report_week_start) AS report_year,
  EXTRACT(ISOWEEK FROM report_week_start) AS report_iso_week,
  CASE
    WHEN reportes_siguiente_semana IS NULL OR reportes_media_4w_previa IS NULL THEN NULL
    WHEN reportes_siguiente_semana > reportes_media_4w_previa THEN 1
    ELSE 0
  END AS incremento_actividad_siguiente_periodo
FROM historico;

-- Control esperado: debe devolver cero filas.
WITH diferencias AS (
  SELECT
    provincia_id,
    report_type_id,
    report_week_start,
    DATE_DIFF(
      report_week_start,
      LAG(report_week_start) OVER (
        PARTITION BY provincia_id, report_type_id ORDER BY report_week_start
      ),
      DAY
    ) AS dias
  FROM `tfm-sbs.siiccffaa_clean.dataset_maestro_modelado_continuo`
)
SELECT * FROM diferencias WHERE dias IS NOT NULL AND dias != 7;

