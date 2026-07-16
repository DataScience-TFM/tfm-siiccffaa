# Evidencia de la migración, limpieza y análisis exploratorio de datos

## Acceso rápido a los documentos

- [Informe ejecutivo del EDA](informes.md/INFORME_EJECUTIVO_EDA.md)
- [Metodología práctica del EDA](informes.md/METODOLOGIA_PRACTICA_EDA.md)
- [Documentación completa de la limpieza y del EDA](informes.md/PLANTILLA_DOCUMENTACION_EDA_COMPLETA.md)

## Objetivo de esta evidencia

En esta carpeta reuní la evidencia técnica del proceso que seguí para trabajar
con los datos originales. Mi trabajo comenzó con la migración de la información
desde PostgreSQL hacia BigQuery. Después preparé y limpié los registros,
construí un esquema analítico limpio y generé el Dataset Maestro. Finalmente,
apliqué un análisis exploratorio de datos (EDA) y diferentes controles para
validar la calidad del resultado.

Conservo los scripts, los CSV y los informes Markdown para demostrar qué hice
en cada etapa. Los CSV y los informes muestran los resultados de mis
comprobaciones; la limpieza y transformación fueron realizadas mediante las
sentencias SQL ejecutadas en BigQuery.

## Resumen del proceso que seguí

```text
1- Datos originales en PostgreSQL
              
2- Exportación de los datos a CSV
              
3- Primer intento de carga manual mediante un bucket
              
4- El intento manual no permitió completar correctamente la migración
              
5- Automatización con los scripts de Migrator_SqlScript
              
6- Carga y validación en BigQuery
              
7- Limpieza y transformación de los datos migrados
              
8- Creación del esquema limpio y del Dataset Maestro
              
9- EDA, validaciones de calidad, CSV e informes
```

## Organización de la evidencia

![alt text](image.png)

## 1. Cómo migré los datos desde PostgreSQL

Los datos originales se encontraban en PostgreSQL. Primero los exporté a
archivos CSV e intenté cargarlos creando un bucket de Cloud Storage. Con ese
procedimiento manual no pude completar correctamente la migración, por lo que
decidí automatizar el proceso con los archivos que conservo en
`Migrator_SqlScript`.

Aunque el nombre de la carpeta incluye `SqlScript`, estos archivos son scripts
de PowerShell que utilicé para coordinar PostgreSQL, Cloud Storage y BigQuery.

### `00_check_local_requirements.ps1`

Utilicé este script para comprobar que las herramientas `gcloud` y `bq`
estuvieran disponibles y que existieran los CSV y los esquemas requeridos antes
de comenzar la carga.

### `03_extract_from_postgresql_local.ps1`

Con este script ejecuté el pipeline de extracción desde PostgreSQL, preparé los
CSV para la migración y convertí la matriz de cobertura a un formato tabular
largo cuando fue necesario. No guardé la contraseña de PostgreSQL en el script;
la introduje de forma interactiva durante la ejecución.

### `01_upload_and_load_bigquery.ps1`

Utilicé este script para seleccionar el proyecto de Google Cloud, activar las
API necesarias, crear o reutilizar el bucket, crear o reutilizar el dataset de
BigQuery, subir los CSV a Cloud Storage y cargar las tablas con sus esquemas.

### `02_validate_bigquery.ps1`

Después de la carga ejecuté este script para revisar los conteos, la cobertura
y la coherencia de la información migrada antes de comenzar la limpieza.

### `00_migracion_completa_postgresql_a_bigquery.ps1`

Este fue el punto de entrada del flujo automatizado. Lo utilicé para ejecutar
en orden la verificación de requisitos, la extracción opcional desde
PostgreSQL, la autenticación, la creación del bucket y del dataset, la subida de
los CSV, la carga de tablas, la creación de vistas y la validación final.

De esta forma sustituí el intento manual que no había funcionado por un proceso
controlado, repetible y verificable.

## 2. Cómo limpié y transformé los datos en BigQuery

### `script_sql_for_data_cleaning/01_creacion_limpieza_dataset_maestro.sql`

Este es el archivo principal con el que documenté la limpieza. Partí de las
tablas migradas al esquema fuente `tfm-sbs.siiccffaa` y creé el esquema
analítico `tfm-sbs.siiccffaa_clean`.

Durante este proceso:

1. Creé el dataset destinado a los datos limpios.
2. Depuré las dimensiones y conservé la versión más reciente de cada registro
   mediante `ROW_NUMBER`, `updated_at` y `created_at`.
3. Eliminé espacios innecesarios y normalicé textos mediante `TRIM` y
   `REGEXP_REPLACE`.
4. Construí las dimensiones de región, provincia, municipio, tipo de reporte,
   institución, sucursal, departamento y grupo de reporte.
5. Excluí registros sin identificador, registros marcados como eliminados y
   fechas fuera del intervalo operativo definido.
6. Sustituí patrones de correo electrónico y teléfono para reducir la
   exposición de información personal en los textos.
7. Integré la provincia incluida directamente en el reporte y, cuando no
   estaba disponible, utilicé la relación `reports__provincias`.
8. Validé las coordenadas usando un rango geográfico aproximado para la
   República Dominicana. Cuando no eran válidas, mantuve el valor original para
   auditoría y dejé nula la coordenada limpia.
9. Normalicé los estados y las plataformas.
10. Construí la tabla de hechos `fact_reportes_limpios`.
11. Agregué los reportes por semana, provincia y tipo de reporte.
12. Calculé rezagos de una, dos y cuatro semanas, una media móvil de cuatro
    semanas, desviación estándar y variaciones porcentuales.
13. Construí `dataset_maestro_modelado` con el grano semanal definido.
14. Creé la variable objetivo
    `incremento_actividad_siguiente_periodo`.
15. Generé `data_quality_summary` para resumir los controles de calidad.

Definí la variable objetivo para indicar si el número de reportes de la semana
siguiente superaba la media de las cuatro semanas anteriores. Cuando no existía
información futura o no había suficiente historial, dejé el objetivo como
nulo para no inventar información.

### `script_python/03_script_original_creacion_bigquery.py`

Conservo este script porque fue el archivo histórico desde el que ejecuté las
sentencias de creación y limpieza mediante la herramienta `bq`. Lo incluyo como
evidencia de procedencia, aunque no es necesario volver a ejecutarlo para
revisar los resultados.

## 3. Cómo apliqué el análisis exploratorio de datos

### `script_sql_for_data_cleaning/02_consultas_eda_y_validacion.sql`

Después de crear el esquema limpio ejecuté 20 consultas de EDA y validación.
No utilicé estas consultas para modificar los datos, sino para comprobar el
resultado de la limpieza.

Con ellas revisé:

- Las tablas y columnas del esquema limpio.
- Los conteos y el resumen general de calidad.
- Los valores faltantes en la tabla de hechos y en el Dataset Maestro.
- Los duplicados de claves y del grano semanal.
- La consistencia de fechas, provincias, coordenadas y variable objetivo.
- La distribución temporal y la tendencia semanal.
- Las provincias, tipos de reporte e instituciones con mayor frecuencia.
- La distribución de la variable objetivo.
- Los valores atípicos mediante el rango intercuartílico (IQR).
- Las correlaciones entre variables numéricas.
- El cruce entre provincia y categoría.
- La auditoría de mis decisiones de limpieza.
- La dimensión de grupos de reporte.

El archivo `script_sql_for_data_cleaning/eda_queries.sql` conserva el conjunto
de consultas ejecutables que generé para esta fase.

## 4. Para qué utilicé `script_python`

La carpeta `script_python` forma parte de la evidencia. En ella conservé la
lógica que utilicé para ejecutar el EDA de forma reproducible. Cada archivo
tuvo una función concreta:

### `config.py`

Aquí definí el proyecto `tfm-sbs`, la región, el dataset original
`siiccffaa`, el dataset limpio `siiccffaa_clean` y las rutas donde debían
guardarse los SQL, CSV, figuras e informes. Centralicé estos valores para no
repetirlos en todos los scripts.

### `bigquery_runner.py`

En este archivo implementé la conexión con la API REST de BigQuery mediante
credenciales de servicio. Lo utilicé para enviar cada consulta, esperar su
finalización, recuperar todas las páginas de resultados, convertir las filas en
un `DataFrame` de pandas y guardar cada resultado como CSV.

### `queries.py`

En este archivo definí las 20 consultas del EDA con sus nombres numerados.
Incluí los controles de estructura, calidad, faltantes, duplicados,
consistencia, distribuciones, tendencia, outliers, correlaciones y auditoría.

### `visualizations.py`

Utilicé este módulo para transformar los resultados tabulares en elementos
visuales: tarjetas de indicadores, gráficos de barras, series temporales,
diagramas del proceso y mapas de calor. Las figuras se generaron a partir de
los resultados obtenidos, no de datos inventados manualmente.

### `reporting.py`

Este archivo contiene la lógica para generar informes Markdown y un dashboard
HTML a partir de las métricas producidas por las consultas. En esta copia de la
evidencia conservo los informes Markdown generados, pero no el dashboard HTML.

### `__init__.py`

Utilicé este archivo para identificar `script_python` como un paquete de Python
y poder importar sus módulos desde el script de ejecución.

### Ejecución del flujo

En `script_python/run_eda.py` coordiné todo el proceso: preparé las carpetas de salida,
generé el archivo SQL consolidado, ejecuté las 20 consultas, guardé los CSV,
generé las visualizaciones y construí los informes y el dashboard. Utilicé
`script_python/test_connection.py` para comprobar por separado que la conexión
con BigQuery funcionaba antes de lanzar el análisis completo. El código puede
generar otros archivos de salida al ejecutarse en su estructura original, pero
esta carpeta conserva únicamente los artefactos enumerados en este README.

## 5. Resultados que obtuve

### `data_Generated_csv`

Guardé aquí los 20 CSV resultantes de las consultas. Estos archivos muestran
los conteos, la estructura, los faltantes, los duplicados, la consistencia, las
distribuciones, las tendencias, los outliers, las correlaciones y la auditoría
de limpieza.

Los CSV no realizaron la limpieza. Los conservé como evidencia de los
resultados que obtuve al comprobar el dataset después de transformarlo.

### `informes.md/INFORME_EJECUTIVO_EDA.md`

En este informe resumí los principales hallazgos del análisis exploratorio y
los controles de calidad realizados.

### `informes.md/PLANTILLA_DOCUMENTACION_EDA_COMPLETA.md`

En este archivo organicé la documentación completa de las comprobaciones,
indicadores y resultados del EDA.

### `informes.md/METODOLOGIA_PRACTICA_EDA.md`

En este documento describí el enfoque práctico seguido para revisar la
estructura, la calidad, los faltantes, los duplicados, la consistencia, las
distribuciones, los outliers, las relaciones numéricas y la variable objetivo.

## Cómo interpreto esta evidencia

- Con `Migrator_SqlScript` documento el flujo automatizado de migración desde
  PostgreSQL, pasando por CSV y Cloud Storage, hasta BigQuery, junto con sus
  comprobaciones previas y validaciones posteriores.
- Con `script_sql_for_data_cleaning/01_creacion_limpieza_dataset_maestro.sql`
  documento las reglas de limpieza, transformación y construcción del Dataset
  Maestro aplicadas en BigQuery.
- Con `script_sql_for_data_cleaning/02_consultas_eda_y_validacion.sql` y
  `script_sql_for_data_cleaning/eda_queries.sql` conservo las consultas
  utilizadas para aplicar el EDA y validar el esquema limpio.
- Con `script_python` documento la automatización de las 20 consultas, la
  exportación de resultados y la generación programática de visualizaciones e
  informes.
- Con los 20 CSV de `data_Generated_csv` conservo los resultados tabulares de
  las comprobaciones. Estos archivos muestran resultados; no ejecutan la
  limpieza ni sustituyen las reglas SQL.
- Con los documentos de `informes.md` presento la metodología, los hallazgos,
  las limitaciones y la interpretación ejecutiva de los resultados.

En conjunto, estos archivos permiten seguir la trazabilidad desde la migración
hasta la validación del dataset limpio. La reproducción completa requiere las
fuentes, credenciales, permisos y recursos externos utilizados en PostgreSQL,
Cloud Storage y BigQuery.
