# Informe ejecutivo del análisis exploratorio de datos

[← Volver al README principal](../README.md)

## Resumen ejecutivo

Después de migrar los datos originales desde PostgreSQL hacia BigQuery,
apliqué las reglas de preparación y limpieza documentadas en
`script_sql_for_data_cleaning/01_creacion_limpieza_dataset_maestro.sql`.
Posteriormente ejecuté 20 consultas de análisis exploratorio y validación sobre
el esquema limpio `tfm-sbs.siiccffaa_clean`.

Partí de **175.317 registros originales** y conservé **175.292 reportes
limpios**, equivalentes al **99,986 %** del total. Excluí **25 registros** con
fechas fuera del intervalo operativo. La clave `report_id` quedó completa y sin
duplicados.

Construí un Dataset Maestro de **20.147 filas** agregadas por semana, provincia
y tipo de reporte. De ellas, **18.128 (89,98 %)** tienen una variable objetivo
disponible para análisis predictivo. El resultado es utilizable para análisis
descriptivo y temporal, aunque identifiqué limitaciones importantes de
cobertura geográfica, coordenadas y duplicación del grano que debo resolver o
controlar antes de entrenar un modelo.

## Indicadores principales

| Indicador | Resultado | Interpretación |
|---|---:|---|
| Registros originales | 175.317 | Registros disponibles antes de aplicar el filtro temporal. |
| Reportes limpios | 175.292 | Conservé el 99,986 % de los registros originales. |
| Registros fuera del intervalo | 25 | Los excluí por no cumplir el criterio de fecha. |
| `report_id` duplicados | 0 | La clave principal de la tabla limpia quedó única. |
| Filas del Dataset Maestro | 20.147 | Combinaciones semanales por provincia y tipo de reporte. |
| Filas con target | 18.128 | El 89,98 % puede utilizarse para evaluar la variable objetivo. |
| Filas sin target | 2.019 | Corresponden al 10,02 % y no deben utilizarse como etiquetas conocidas. |
| Filas sin rezago de una semana | 1.128 | El 5,60 % no tiene historial anterior suficiente. |
| Reportes sin provincia | 87.006 | El 49,63 % limita los análisis territoriales. |
| Coordenadas válidas | 12 | Solo el 0,0068 % permite análisis geoespacial fiable. |
| Descripciones faltantes | 9.807 | El 5,59 % no tiene descripción limpia disponible. |
| Outliers semanales por IQR | 2.358 | El 11,70 % supera el límite superior de 11 reportes semanales. |

## Calidad e integridad de los datos

### Identificadores y duplicados

Comprobé que los **175.292 valores de `report_id` son únicos**, por lo que no
detecté duplicación de registros según la clave principal utilizada para la
tabla de hechos.

Encontré **4.590 repeticiones de `report_code`**, pero no las interpreto
automáticamente como registros duplicados: un mismo código puede aparecer en
más de un registro mientras cada `report_id` siga siendo diferente. Antes de
eliminar información por este criterio debo confirmar el significado funcional
de `report_code`.

En el Dataset Maestro detecté **59 filas adicionales respecto al grano único**:
20.147 filas frente a 20.088 combinaciones distintas de semana, provincia y
tipo de reporte. Debo consolidar estas combinaciones antes del entrenamiento
para evitar que una misma unidad analítica aparezca repetida.

### Valores faltantes

Los campos esenciales `report_id`, `report_code`, `report_date`,
`report_type_name` y `company_name` no presentan valores faltantes. La
principal limitación se encuentra en la información territorial:

- **87.006 reportes (49,63 %)** no tienen provincia.
- **175.280 reportes (99,99 %)** no tienen latitud o longitud limpia válida.
- **9.807 reportes (5,59 %)** no tienen descripción limpia.

Conservé los reportes sin provincia porque siguen siendo útiles para conteos
generales, análisis temporales y análisis por institución o tipo de reporte. Sin
embargo, no debo utilizarlos como si tuvieran una localización territorial
conocida.

### Coordenadas

Solo **12 reportes** superaron la validación del rango geográfico definido para
la República Dominicana. Por esta razón no considero las coordenadas una fuente
suficiente para mapas puntuales, distancias o modelos geoespaciales. La
provincia, cuando está disponible, es una referencia territorial más adecuada.

## Distribución de los reportes

### Cobertura temporal

La tabla de hechos contiene registros desde **agosto de 2021 hasta mayo de
2026**. Los mayores volúmenes mensuales observados fueron:

| Periodo | Reportes |
|---|---:|
| Marzo de 2023 | 6.493 |
| Abril de 2024 | 5.953 |
| Marzo de 2024 | 5.863 |
| Abril de 2023 | 5.769 |
| Mayo de 2023 | 5.712 |

El año 2023 concentra **63.733 reportes** y 2024 concentra **60.697**. Los
extremos de 2021 y 2026 representan periodos parciales, por lo que no debo
compararlos directamente con años completos sin controlar la cobertura.

La salida de tendencia semanal disponible abarca del **9 de agosto de 2021 al
19 de febrero de 2024** y suma 52.012 reportes, mientras que la distribución
mensual de la tabla de hechos llega hasta mayo de 2026. Esta diferencia indica
que ambas salidas no tienen exactamente el mismo alcance. Antes de utilizar la
serie semanal para modelado debo revisar los filtros y las uniones empleados en
la agregación y regenerarla con el periodo completo.

### Distribución territorial

La categoría con mayor volumen es `sin_provincia`, con **87.006 reportes**. Si
considero únicamente las provincias identificadas, las de mayor frecuencia son:

| Provincia | Reportes |
|---|---:|
| Santo Domingo | 21.755 |
| Santiago | 8.932 |
| Monseñor Nouel | 4.851 |
| La Altagracia | 4.136 |
| Peravia | 4.028 |

Santo Domingo representa el **12,41 %** del total de la tabla limpia, pero la
proporción elevada de registros sin provincia impide interpretar este ranking
como una distribución territorial completa de todos los reportes.

### Tipos de reporte e instituciones

El tipo con mayor frecuencia es **REPORTE OPERACIONAL**, con **17.442
registros**, seguido de **CONTROL DE BUQUES DE CARGA (CESEP)**, con 16.731, y
**OPERATIVO DE PATRULLA (CECCOM)**, con 16.198.

Las instituciones con mayor volumen son:

| Institución | Reportes |
|---|---:|
| CESEP | 30.760 |
| FT CIUTRAN | 28.257 |
| CESAC | 23.535 |
| CECCOM | 22.988 |
| OPERACIONES C5i | 19.372 |

CESEP concentra el **17,55 %** de los reportes. Estas concentraciones deben
considerarse al dividir los datos para modelado, ya que una partición aleatoria
podría favorecer las categorías más frecuentes.

## Dataset Maestro y variable objetivo

El Dataset Maestro contiene **20.147 observaciones**. La variable objetivo se
distribuye de la siguiente manera:

| Clase | Filas | Porcentaje sobre target conocido |
|---|---:|---:|
| Sin incremento | 11.933 | 65,83 % |
| Incremento | 6.195 | 34,17 % |
| Sin target | 2.019 | No aplica |

Existe un desequilibrio moderado entre las clases conocidas. Si entreno un
clasificador, no debo evaluar su desempeño únicamente con exactitud; debo
incorporar, como mínimo, precisión, exhaustividad, F1, matriz de confusión y una
validación temporal.

## Outliers y relaciones numéricas

Aplicando el criterio IQR obtuve un primer cuartil de 1, un tercer cuartil de 5
y un límite superior de 11 reportes por semana. Identifiqué **2.358
observaciones atípicas (11,70 %)**, con un máximo de 83 reportes semanales.

No debo eliminar estos casos automáticamente. Pueden representar semanas de
actividad operativa real. Primero debo contrastarlos con fecha, provincia, tipo
de reporte e institución y solo corregirlos cuando exista evidencia de error.

Las variables con mayor correlación respecto a `reportes_semana` son:

| Variable | Correlación |
|---|---:|
| Media de las cuatro semanas anteriores | 0,884 |
| Rezago de una semana | 0,867 |
| Rezago de dos semanas | 0,845 |
| Rezago de cuatro semanas | 0,825 |
| Variación porcentual semanal | 0,164 |
| Instituciones distintas | 0,005 |

Estos resultados muestran una fuerte persistencia temporal. Los rezagos y la
media móvil son candidatos útiles para el modelado, pero debo calcularlos
utilizando exclusivamente información anterior a cada observación para evitar
fuga de información.

## Conclusiones

1. Conseguí conservar prácticamente todos los registros válidos y dejé una
   clave principal sin duplicados.
2. La tabla `fact_reportes_limpios` es adecuada para análisis descriptivos
   generales, temporales, institucionales y por tipo de reporte.
3. La falta de provincia en casi la mitad de los reportes limita las
   conclusiones territoriales.
4. La cobertura de coordenadas es insuficiente para análisis geoespacial.
5. El Dataset Maestro dispone de target en casi el 90 % de sus filas y presenta
   variables temporales con relaciones fuertes.
6. Antes de modelar debo resolver las 59 repeticiones del grano y comprobar por
   qué la serie semanal termina antes que la distribución mensual.
7. Los outliers requieren investigación contextual y no una eliminación
   automática.

## Recomendaciones prioritarias

1. Consolidar el Dataset Maestro para garantizar una sola fila por semana,
   provincia y tipo de reporte.
2. Regenerar y validar la agregación semanal con el mismo rango temporal de la
   tabla de hechos.
3. Separar los datos de entrenamiento, validación y prueba respetando el orden
   temporal.
4. Excluir las filas sin target del entrenamiento supervisado, sin eliminarlas
   de la evidencia ni de otros análisis.
5. Mantener los reportes sin provincia para indicadores generales y excluirlos
   de resultados territoriales específicos.
6. No utilizar coordenadas en el modelado actual, salvo que se complete o
   corrija su cobertura.
7. Analizar los outliers junto con su contexto operativo antes de decidir si
   representan errores o eventos reales.
8. Evaluar el modelo con métricas apropiadas para clases desbalanceadas y
   comparar el resultado contra una línea base temporal sencilla.

## Evidencias consultadas

- [`01_conteo_tablas_limpias.csv`](../data_Generated_csv/01_conteo_tablas_limpias.csv)
- [`02_estructura_tablas_limpias.csv`](../data_Generated_csv/02_estructura_tablas_limpias.csv)
- [`03_resumen_calidad.csv`](../data_Generated_csv/03_resumen_calidad.csv)
- [`04_faltantes_fact_reportes.csv`](../data_Generated_csv/04_faltantes_fact_reportes.csv)
- [`05_faltantes_dataset_maestro.csv`](../data_Generated_csv/05_faltantes_dataset_maestro.csv)
- [`06_duplicados.csv`](../data_Generated_csv/06_duplicados.csv)
- [`08_distribucion_anio_mes.csv`](../data_Generated_csv/08_distribucion_anio_mes.csv)
- [`09_tendencia_semanal.csv`](../data_Generated_csv/09_tendencia_semanal.csv)
- [`14_distribucion_target.csv`](../data_Generated_csv/14_distribucion_target.csv)
- [`15_outliers_iqr_reportes_semana.csv`](../data_Generated_csv/15_outliers_iqr_reportes_semana.csv)
- [`16_correlaciones_numericas.csv`](../data_Generated_csv/16_correlaciones_numericas.csv)
- [`19_auditoria_limpieza.csv`](../data_Generated_csv/19_auditoria_limpieza.csv)
