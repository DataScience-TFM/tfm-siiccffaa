# Metodología práctica del EDA

[← Volver al README principal](../README.md)

## Enfoque que apliqué

Realicé el análisis exploratorio de datos después de migrar la información
original desde PostgreSQL hacia BigQuery y de construir el esquema limpio
`tfm-sbs.siiccffaa_clean`. Mi objetivo fue conocer la estructura y el
comportamiento de los datos, comprobar el resultado de la limpieza, identificar
limitaciones y determinar si el Dataset Maestro estaba preparado para una fase
posterior de modelado.

No utilicé el EDA para modificar los datos. Primero ejecuté las reglas de
limpieza y transformación contenidas en
`script_sql_for_data_cleaning/01_creacion_limpieza_dataset_maestro.sql` y,
después, apliqué las consultas de validación de
`script_sql_for_data_cleaning/02_consultas_eda_y_validacion.sql`.

Organicé el trabajo de manera reproducible. Definí las consultas en Python,
las ejecuté contra BigQuery, convertí los resultados en estructuras tabulares
de pandas y guardé cada comprobación como un archivo CSV. De esta forma pude
conservar tanto la consulta aplicada como el resultado que obtuve.

## 1. Definición de la unidad de análisis

Antes de comenzar las comprobaciones distinguí dos niveles de información:

- Utilicé `fact_reportes_limpios` para analizar cada reporte individual,
  revisar identificadores, fechas, textos, instituciones, provincias y
  coordenadas.
- Utilicé `dataset_maestro_modelado` para el análisis temporal y predictivo.
  Definí su grano como una combinación de semana, provincia y tipo de reporte.

Esta separación me permitió evitar la mezcla de indicadores calculados a nivel
de reporte con variables agregadas a nivel semanal.

## 2. Conexión y extracción de los resultados

Me conecté a BigQuery mediante la API REST HTTPS y una cuenta de servicio. En
`script_python/src/bigquery_runner.py` implementé la autenticación, el envío
de consultas, la espera de los trabajos, la paginación de resultados y la
conversión de las respuestas a `DataFrame`.

Centralicé en `script_python/src/config.py` el proyecto, la región y los
nombres de los datasets original y limpio. En
`script_python/src/queries.py` conservé las 20 consultas utilizadas. Con
`script_python/scripts/run_eda.py` coordiné su ejecución y la generación de las
salidas.

## 3. Revisión de la estructura

Comencé inventariando las tablas creadas en el esquema limpio. Revisé sus
conteos, columnas, tipos de datos, orden de los campos y posibilidad de valores
nulos.

Con esta comprobación confirmé la existencia de las dimensiones, la tabla de
hechos, la agregación semanal, el Dataset Maestro y el resumen de calidad.
También comprobé que las variables necesarias para el análisis habían sido
materializadas correctamente.

## 4. Evaluación de la calidad general

Comparé la cantidad de registros originales con los reportes conservados
después de la limpieza. Partí de 175.317 registros y obtuve 175.292 reportes
limpios. Los 25 registros restantes estaban fuera del intervalo de fechas que
había definido.

Además de los conteos, revisé la disponibilidad de provincia, coordenadas,
nombre del tipo de reporte y variable objetivo. Utilicé estas métricas como una
primera visión de las fortalezas y limitaciones del dataset.

## 5. Análisis de valores faltantes

Calculé la cantidad y el porcentaje de valores faltantes tanto en
`fact_reportes_limpios` como en `dataset_maestro_modelado`.

En la tabla de hechos comprobé los identificadores, códigos, fechas, tipos de
reporte, instituciones, provincias, coordenadas y descripciones. En el Dataset
Maestro revisé las claves del grano, los rezagos, la media móvil y la variable
objetivo.

No apliqué una imputación automática y generalizada. Cuando no encontré
evidencia suficiente para completar un valor, preferí conservarlo como nulo:

- Si un reporte no tenía provincia directa ni una relación territorial
  verificable, no le asigné una provincia inventada.
- Si una coordenada estaba ausente o fuera del rango geográfico definido, no la
  sustituí por una coordenada aproximada.
- Si una observación semanal no tenía historial suficiente, mantuve nulos sus
  rezagos o su media móvil.
- Si no existía información futura para calcular el target, mantuve la variable
  objetivo como nula.

## 6. Comprobación de duplicados

Utilicé `report_id` como clave principal de los reportes limpios. Comparé el
número total de filas con el número de identificadores distintos y confirmé
que no existían duplicados de esta clave.

También revisé `report_code`. Encontré códigos repetidos, pero no los eliminé
automáticamente porque una repetición de este campo no demuestra por sí sola
que dos registros sean idénticos.

Para el Dataset Maestro comprobé la unicidad de la combinación formada por
semana, provincia y tipo de reporte. Detecté 59 filas adicionales respecto a
las combinaciones únicas y conservé el detalle de esos casos para su revisión
antes del modelado.

## 7. Controles de consistencia

Comprobé que las fechas de la tabla limpia no fueran nulas y revisé cuántos
registros originales estaban fuera del rango temporal permitido. También
verifiqué la disponibilidad de provincia, la validez de las coordenadas, los
rezagos y la variable objetivo.

Revisé por separado la dimensión `dim_report_group` para confirmar que sus
identificadores y nombres estuvieran completos y que sus registros se
encontraran activos.

Estos controles me permitieron distinguir entre un error de integridad y una
ausencia de información que debía conservarse como limitación del origen.

## 8. Análisis de distribuciones

Estudié la distribución de los reportes por año, mes y semana para observar su
evolución temporal. También calculé las frecuencias por provincia, tipo de
reporte e institución.

En el análisis territorial mantuve la categoría `sin_provincia` para que los
conteos generales siguieran representando el volumen real. Sin embargo, la
separé conceptualmente de las provincias conocidas y no la interpreté como una
ubicación geográfica.

La comparación de las salidas temporales también me permitió identificar una
diferencia de cobertura: la distribución mensual llega hasta mayo de 2026,
mientras que la tendencia semanal disponible termina en febrero de 2024. Dejé
esta diferencia documentada porque debo revisar y regenerar la agregación
semanal antes de utilizarla en un modelo definitivo.

## 9. Detección de valores atípicos

Apliqué el criterio del rango intercuartílico (IQR) sobre la variable
`reportes_semana`. Calculé el primer y tercer cuartil, el rango
intercuartílico y los límites inferior y superior.

Identifiqué como atípicas las observaciones que superaban el límite superior de
11 reportes semanales. No eliminé estos casos automáticamente, porque un volumen
elevado puede representar una actividad operativa real. Mi criterio fue
documentarlos y recomendar su revisión junto con la fecha, la provincia, el tipo
de reporte y la institución.

## 10. Análisis de relaciones numéricas

Calculé la correlación de `reportes_semana` con los rezagos, la media de las
cuatro semanas anteriores, la variación porcentual y la cantidad de
instituciones distintas.

Observé que la media móvil y los rezagos presentaban las relaciones más
fuertes. Interpreté este resultado como evidencia de persistencia temporal, no
como una demostración de causalidad. También tuve en cuenta que estas variables
debían construirse exclusivamente con datos anteriores a cada observación para
evitar fuga de información.

## 11. Revisión de la variable objetivo

Analicé la distribución de
`incremento_actividad_siguiente_periodo`. Separé las observaciones con
incremento, sin incremento y sin target.

No incluí las filas sin target como ejemplos etiquetados. Además, identifiqué
un desequilibrio moderado entre las clases conocidas, por lo que recomendé no
evaluar un modelo únicamente mediante exactitud. Consideré necesario utilizar
precisión, exhaustividad, F1, matriz de confusión y validación temporal.

## 12. Generación y conservación de la evidencia

Guardé cada resultado del EDA como un CSV numerado dentro de `data_Generated`.
De esta manera relacioné cada consulta con una salida concreta y verificable.

En `script_python/src/visualizations.py` implementé la generación de tarjetas,
gráficos de barras, series temporales, diagramas y mapas de calor. En
`script_python/src/reporting.py` implementé la generación de informes en
Markdown y la preparación del dashboard HTML.

Finalmente resumí los resultados, limitaciones y recomendaciones en
`INFORME_EJECUTIVO_EDA.md`. Los archivos generados documentan lo que observé;
no sustituyen los SQL con los que realicé la limpieza.

## Criterios metodológicos que mantuve

Durante todo el EDA seguí estos criterios:

1. No inventé valores para completar información territorial o temporal.
2. No eliminé registros solamente porque tuvieran campos opcionales nulos.
3. No interpreté un código repetido como duplicado sin revisar la clave
   principal.
4. No eliminé outliers sin comprobar primero su contexto operativo.
5. Diferencié los datos a nivel de reporte de los datos agregados semanalmente.
6. Conservé las consultas y sus resultados para asegurar trazabilidad.
7. Separé las operaciones de limpieza de las consultas utilizadas para
   analizar y validar el resultado.
8. Documenté las limitaciones antes de proponer el uso del dataset para
   modelado.

## Resultado de la metodología

Con esta metodología comprobé la estructura y la calidad del esquema limpio,
identifiqué valores faltantes, duplicados del grano, limitaciones geográficas,
valores atípicos y relaciones temporales. También dejé documentadas las
condiciones que debo resolver antes de entrenar un modelo: consolidar el grano
semanal, revisar la cobertura temporal de la agregación, excluir del
entrenamiento las filas sin target y evitar el uso de coordenadas mientras su
cobertura siga siendo insuficiente.

De esta forma, mi EDA no se limitó a generar gráficos. Lo utilicé como un
proceso de verificación para demostrar qué datos tenía, qué transformaciones se
habían aplicado, qué limitaciones permanecían y qué condiciones debía cumplir
el Dataset Maestro antes de pasar a la fase de modelado.
