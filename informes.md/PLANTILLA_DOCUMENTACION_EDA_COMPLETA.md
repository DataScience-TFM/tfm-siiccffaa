# Documentación completa de la limpieza y del EDA

[← Volver al README principal](../README.md)

## Finalidad del documento

En este documento explico cómo preparé, limpié y validé los datos utilizados
en mi trabajo. También aclaro la función de cada uno de los dos proyectos que
entrego:

- En `Evidencia_EDA` conservo la trazabilidad técnica: scripts de migración,
  SQL de limpieza, consultas del EDA, resultados CSV e informes.
- En `Proyecto_Python_Analisis_Exploratorio` implementé la aplicación con la
  que consulto BigQuery y visualizo de manera interactiva la limpieza y la
  metodología EDA.

No considero esta carpeta de evidencia una aplicación visual. Su finalidad es
permitir que se pueda auditar qué hice, con qué consultas lo hice y qué
resultados obtuve. La experiencia visual e interactiva se encuentra en el
proyecto Python independiente.

## Flujo completo que seguí

```text
Datos originales en PostgreSQL
              ↓
Exportación a CSV
              ↓
Migración automatizada mediante Cloud Storage y BigQuery
              ↓
Tablas originales en tfm-sbs.siiccffaa
              ↓
Limpieza y transformación mediante SQL
              ↓
Esquema limpio tfm-sbs.siiccffaa_clean
              ↓
Dataset Maestro y variable objetivo
              ↓
20 consultas de EDA y validación
              ↓
Resultados CSV conservados en Evidencia_EDA
              ↓
Visualización en Proyecto_Python_Analisis_Exploratorio
```

## 1. Preparación y limpieza de los datos

Partí de los datos que había migrado desde PostgreSQL hacia BigQuery. Utilicé
`script_sql_for_data_cleaning/01_creacion_limpieza_dataset_maestro.sql` para
crear el esquema limpio `tfm-sbs.siiccffaa_clean` y materializar las tablas
analíticas.

### Reglas que apliqué

| Área | Decisión que tomé | Motivo |
|---|---|---|
| Identificadores | Conservé reportes con `report_id` disponible. | Necesitaba una clave trazable para cada reporte. |
| Fechas | Conservé fechas desde el 1 de enero de 2021 hasta la fecha de ejecución. | Evité incorporar registros fuera del periodo operativo definido. |
| Registros eliminados | Excluí los reportes marcados como eliminados. | No debían formar parte del esquema analítico activo. |
| Dimensiones | Conservé la versión más reciente mediante `ROW_NUMBER`, `updated_at` y `created_at`. | Evité múltiples versiones de una misma entidad. |
| Textos | Apliqué `TRIM` y `REGEXP_REPLACE`. | Eliminé espacios innecesarios y unifiqué el contenido textual. |
| Datos personales | Sustituí patrones de correo y teléfono por marcadores. | Reduje la exposición de información sensible. |
| Provincia | Utilicé la provincia directa o la relación `reports__provincias`. | Aproveché únicamente evidencia territorial disponible. |
| Provincia ausente | Conservé el valor nulo cuando no encontré evidencia. | No quise inventar una ubicación. |
| Coordenadas | Acepté como limpias solo las ubicadas en el rango aproximado de la República Dominicana. | Evité utilizar puntos geográficos incoherentes. |
| Estados y plataformas | Normalicé sus valores. | Reduje variaciones de escritura y categorías equivalentes. |

### Tablas que construí

Creé dimensiones limpias para región, provincia, municipio, tipo de
reporte, institución, sucursal, departamento y grupo de reporte. Después
construí:

- `fact_reportes_limpios`, con un registro por `report_id`.
- `agg_reportes_semanal`, agregada por semana, provincia y tipo de reporte.
- `dataset_maestro_modelado`, con variables temporales y el grano destinado al
  modelado.
- `data_quality_summary`, con indicadores generales de calidad.

### Variables temporales y objetivo

Calculé rezagos de una, dos y cuatro semanas, la media de las cuatro semanas
anteriores, la desviación estándar y variaciones porcentuales.

Definí `incremento_actividad_siguiente_periodo` para indicar si el volumen de
la semana siguiente superaba la media de las cuatro semanas anteriores. Cuando
no existía suficiente historial o información futura, dejé el target como nulo
para no generar una etiqueta artificial.

## 2. Metodología EDA que apliqué

Después de crear el esquema limpio ejecuté las 20 consultas contenidas en
`script_sql_for_data_cleaning/02_consultas_eda_y_validacion.sql`. Utilicé estas
consultas para analizar y validar el resultado; no las utilicé para volver a
limpiar o modificar los datos.

### Comprobaciones realizadas

1. Inventarié las tablas limpias y sus cantidades de registros.
2. Revisé las columnas, los tipos de datos y la posibilidad de valores nulos.
3. Consulté el resumen general de calidad.
4. Calculé faltantes en `fact_reportes_limpios`.
5. Calculé faltantes en `dataset_maestro_modelado`.
6. Comprobé duplicados de `report_id`, repeticiones de `report_code` y
   duplicados del grano semanal.
7. Revisé la consistencia de fechas, provincias, coordenadas, rezagos y target.
8. Analicé la distribución por año y mes.
9. Analicé la tendencia semanal.
10. Identifiqué las provincias con mayor volumen.
11. Identifiqué los tipos de reporte principales.
12. Identifiqué las instituciones con mayor número de reportes.
13. Comprobé la distribución de los estados normalizados.
14. Revisé la distribución de la variable objetivo.
15. Detecté valores atípicos mediante el rango intercuartílico (IQR).
16. Calculé correlaciones entre el volumen semanal y las variables derivadas.
17. Crucé provincia y categoría de reporte.
18. Conservé el detalle de las combinaciones duplicadas del grano semanal.
19. Generé una auditoría de las decisiones de limpieza.
20. Verifiqué la integridad de `dim_report_group`.

## 3. Resultados principales

| Indicador | Resultado | Interpretación que realicé |
|---|---:|---|
| Registros originales | 175.317 | Volumen disponible antes del filtro temporal. |
| Reportes limpios | 175.292 | Conservé el 99,986 % del origen. |
| Registros excluidos por fecha | 25 | No cumplían el intervalo operativo. |
| Duplicados de `report_id` | 0 | La clave principal quedó única. |
| Filas del Dataset Maestro | 20.147 | Combinaciones semanales preparadas para análisis. |
| Filas con target | 18.128 | El 89,98 % tiene una etiqueta disponible. |
| Filas sin target | 2.019 | No deben utilizarse como observaciones etiquetadas. |
| Reportes sin provincia | 87.006 | El 49,63 % limita el análisis territorial. |
| Coordenadas válidas | 12 | La cobertura es insuficiente para un análisis geoespacial fiable. |
| Duplicados del grano semanal | 59 | Deben consolidarse antes del modelado. |
| Outliers semanales por IQR | 2.358 | Representan el 11,70 % del Dataset Maestro. |

### Valores faltantes

Comprobé que `report_id`, `report_code`, `report_date`, `report_type_name` y
`company_name` no tenían valores faltantes. Las principales limitaciones se
concentraron en:

- Provincia: 87.006 valores ausentes, equivalentes al 49,63 %.
- Latitud y longitud limpias: 175.280 valores ausentes o no válidos, un
  99,99 %.
- Descripción limpia: 9.807 valores ausentes, un 5,59 %.
- Target: 2.019 filas sin etiqueta, un 10,02 % del Dataset Maestro.
- Rezago de una semana y media previa: 1.128 valores nulos, un 5,60 %.

No imputé estos campos de forma generalizada. Preferí mantener los nulos
cuando no disponía de una fuente verificable para completarlos.

### Duplicados

Confirmé que `report_id` era único. Encontré 4.590 repeticiones de
`report_code`, pero no las traté como duplicados automáticos porque el código
repetido no implica necesariamente que dos reportes sean idénticos.

En el Dataset Maestro encontré 20.147 filas y 20.088 combinaciones distintas
del grano semana, provincia y tipo. Documenté las 59 filas adicionales para su
consolidación antes del entrenamiento.

### Distribución de la variable objetivo

| Clase | Filas | Porcentaje sobre target conocido |
|---|---:|---:|
| Sin incremento | 11.933 | 65,83 % |
| Incremento | 6.195 | 34,17 % |
| Sin target | 2.019 | No aplica |

Identifiqué un desequilibrio moderado entre las clases conocidas. Por este
motivo consideré necesario utilizar métricas como precisión, exhaustividad, F1
y matriz de confusión, además de una validación temporal.

### Valores atípicos y relaciones temporales

Mediante IQR obtuve un límite superior de 11 reportes semanales e identifiqué
2.358 observaciones atípicas. No las eliminé automáticamente porque podían
representar semanas de actividad operativa real.

Las correlaciones más altas con `reportes_semana` fueron:

| Variable | Correlación |
|---|---:|
| Media de las cuatro semanas anteriores | 0,884 |
| Rezago de una semana | 0,867 |
| Rezago de dos semanas | 0,845 |
| Rezago de cuatro semanas | 0,825 |

Interpreté estas relaciones como persistencia temporal, no como causalidad. Al
utilizar estas variables debo asegurarme de que solo incorporen información
anterior a la observación que se quiere predecir.

## 4. Evidencia conservada en `Evidencia_EDA`

En esta carpeta conservo:

- Los scripts utilizados para migrar los datos desde PostgreSQL hasta BigQuery.
- El SQL con el que construí el esquema limpio y el Dataset Maestro.
- Las 20 consultas utilizadas para aplicar el EDA y validar la limpieza.
- Los 20 CSV numerados de `data_Generated`.
- El informe ejecutivo y la metodología narrada.
- El documento Word con la explicación paso a paso de la limpieza.
- El código histórico que utilicé para ejecutar consultas y generar la
  evidencia.

Los archivos de esta carpeta permiten revisar el proceso sin necesidad de
ejecutar la aplicación visual.

## 5. Visualización en `Proyecto_Python_Analisis_Exploratorio`

La visualización de la limpieza y de la metodología EDA no se encuentra dentro
de `Evidencia_EDA`. Para esa finalidad desarrollé el proyecto independiente
`Proyecto_Python_Analisis_Exploratorio`, situado al mismo nivel que esta
carpeta.

En ese proyecto implementé una aplicación web con Flask y Plotly que consulta
directamente el esquema `tfm-sbs.siiccffaa_clean` mediante la API REST HTTPS de
BigQuery. La aplicación no utiliza los CSV guardados en `data_Generated`; ejecuta
las 20 consultas en vivo y mantiene temporalmente los resultados en memoria.

### Componentes de la aplicación visual

| Componente | Función que implementé |
|---|---|
| `web_app.py` | Coordiné las consultas, preparé indicadores, gestioné una caché de 15 minutos y expuse las rutas web. |
| `src/config.py` | Definí el proyecto, el dataset original, el dataset limpio y la región. |
| `src/bigquery_runner.py` | Implementé la autenticación y la ejecución de consultas contra BigQuery. |
| `src/queries.py` | Conservé las 20 consultas que alimentan la visualización. |
| `templates/index.html` | Definí la estructura del dashboard, los filtros, gráficos y tablas. |
| `static/styles.css` y `static/live.css` | Definí el diseño visual y los estilos de la aplicación. |
| `run_web.ps1` | Automaticé la preparación del entorno y el inicio del servidor local. |

El flujo de visualización es:

```text
Cuenta de servicio
        ↓
API REST HTTPS de BigQuery
        ↓
20 consultas EDA
        ↓
DataFrames mantenidos en memoria
        ↓
Flask
        ↓
Gráficos Plotly y tablas en el navegador
```

La aplicación se ejecuta localmente en `http://127.0.0.1:8000`. Desde ella
puedo consultar los indicadores y forzar una actualización desde BigQuery. La
caché de 15 minutos evita repetir consultas innecesarias, pero el botón de
actualización permite solicitar resultados nuevos.

## 6. Diferencia entre evidencia y visualización

| Aspecto | `Evidencia_EDA` | `Proyecto_Python_Analisis_Exploratorio` |
|---|---|---|
| Finalidad | Auditar y documentar el proceso. | Consultar y visualizar los resultados. |
| Fuente conservada | SQL, scripts, CSV e informes. | Consultas en Python y componentes de la aplicación web. |
| Acceso a BigQuery | No es necesario para revisar los archivos ya generados. | Es necesario para obtener los datos en vivo. |
| Resultados | CSV estáticos que demuestran las comprobaciones ejecutadas. | DataFrames temporales generados en cada consulta o actualización. |
| Presentación | Documentación técnica en Markdown y Word. | Dashboard interactivo con Flask y Plotly. |
| Credenciales | No incluyo credenciales como parte de la evidencia. | Requiere una cuenta de servicio autorizada para consultar BigQuery. |

Esta separación me permite entregar una evidencia auditable sin depender de
la disponibilidad de la aplicación y, al mismo tiempo, presentar el análisis de
forma interactiva cuando existen conexión y credenciales válidas.

## 7. Limitaciones que documenté

1. Casi la mitad de los reportes no dispone de provincia.
2. La cobertura de coordenadas es insuficiente para un análisis geoespacial.
3. Existen 59 filas adicionales respecto al grano único del Dataset Maestro.
4. La serie semanal disponible termina en febrero de 2024, mientras que la
   distribución mensual llega hasta mayo de 2026; debo revisar el alcance de la
   agregación antes del modelado definitivo.
5. El 10,02 % del Dataset Maestro no tiene target disponible.
6. La variable objetivo presenta un desequilibrio moderado entre las clases.
7. Los outliers pueden representar actividad real y no deben eliminarse sin
   una revisión contextual.

## 8. Conclusión

Con la limpieza construí una base analítica trazable y con el EDA comprobé su
estructura, calidad y limitaciones. En `Evidencia_EDA` dejé los elementos que
permiten verificar el trabajo realizado. En
`Proyecto_Python_Analisis_Exploratorio` desarrollé la visualización interactiva
para consultar directamente BigQuery y presentar los resultados.

De esta manera separé correctamente la evidencia del proceso y la aplicación
de visualización: una demuestra cómo trabajé con los datos y la otra permite
explorar visualmente los resultados obtenidos.
