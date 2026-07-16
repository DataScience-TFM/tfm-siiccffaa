# Evidencia de migración, limpieza y análisis exploratorio de datos

Este repositorio conserva la trazabilidad técnica de un flujo de datos desde
PostgreSQL hasta BigQuery: migración, limpieza, construcción de un Dataset
Maestro, análisis exploratorio (EDA) y controles de calidad. Incluye los
scripts utilizados, 20 resultados tabulares en CSV y tres informes de apoyo.

> **Alcance:** esta carpeta es una instantánea de evidencia y auditoría. No es
> un paquete autónomo listo para ejecutar de principio a fin, porque no incluye
> los datos fuente, credenciales ni todos los recursos del pipeline original.

## Documentos principales

- [Informe ejecutivo del EDA](informes.md/INFORME_EJECUTIVO_EDA.md)
- [Metodología práctica del EDA](informes.md/METODOLOGIA_PRACTICA_EDA.md)
- [Documentación completa de limpieza y EDA](informes.md/PLANTILLA_DOCUMENTACION_EDA_COMPLETA.md)

## Flujo documentado

```text
PostgreSQL
    ↓ extracción
CSV
    ↓ carga mediante Cloud Storage
BigQuery: tfm-sbs.siiccffaa
    ↓ limpieza y transformación SQL
BigQuery: tfm-sbs.siiccffaa_clean
    ↓ agregación semanal e ingeniería de variables
Dataset Maestro
    ↓ 20 consultas de EDA y validación
CSV e informes Markdown
```

La limpieza real se ejecuta en BigQuery. Los CSV de este repositorio son
resultados de comprobación: no sustituyen ni realizan la transformación.

## Estructura del repositorio

```text
.
├── Migrator_PowerShell_Scripts/   # Orquestación PostgreSQL → GCS → BigQuery
├── SqlScript_Cleaning_Data/       # Limpieza, Dataset Maestro y consultas EDA
├── Python_Scripts/                # Ejecución del EDA y generación de salidas
├── data_Generated_csv/            # 20 resultados tabulares del EDA
├── informes.md/                   # Informes metodológicos y ejecutivos
├── image.png                      # Captura ilustrativa de la organización
└── README.md
```

## Contenido técnico

### 1. Migración

`Migrator_PowerShell_Scripts/` contiene cuatro etapas y un orquestador:

- `00_check_local_requirements.ps1`: comprueba `gcloud`, `bq`, CSV y esquemas.
- `03_extract_from_postgresql_local.ps1`: invoca el pipeline PostgreSQL
  original, copia sus salidas y transforma la matriz de cobertura a formato
  largo.
- `01_upload_and_load_bigquery.ps1`: crea o reutiliza bucket y dataset, sube
  CSV, reemplaza tablas y crea vistas.
- `02_validate_bigquery.ps1`: ejecuta las consultas de validación posteriores
  a la carga.
- `00_migracion_completa_postgresql_a_bigquery.ps1`: coordina todo el flujo y
  permite activar explícitamente la autenticación y la extracción.

Las cargas usan `bq load --replace`; por tanto, reemplazan las tablas de destino
con el mismo nombre. Ningún script guarda la contraseña de PostgreSQL.

### 2. Limpieza y Dataset Maestro

El archivo
[`01_creacion_limpieza_dataset_maestro.sql`](SqlScript_Cleaning_Data/01_creacion_limpieza_dataset_maestro.sql)
crea el esquema `tfm-sbs.siiccffaa_clean` y:

1. Deduplica dimensiones con `ROW_NUMBER` y marcas temporales.
2. Normaliza textos, estados y plataformas.
3. Excluye identificadores nulos, eliminados lógicos y fechas fuera del rango
   operativo.
4. Enmascara patrones de correo y teléfono en texto libre.
5. Resuelve provincia desde el reporte o desde `reports__provincias`.
6. Separa coordenadas originales y coordenadas válidas para el rango geográfico
   aproximado de República Dominicana.
7. Construye `fact_reportes_limpios` y `agg_reportes_semanal`.
8. Calcula rezagos de 1, 2 y 4 semanas, media y desviación de las cuatro semanas
   anteriores, y variaciones porcentuales.
9. Construye `dataset_maestro_modelado` con grano
   `semana + provincia + tipo de reporte`.
10. Define `incremento_actividad_siguiente_periodo`: vale 1 cuando los reportes
    de la semana siguiente superan la media de las cuatro semanas previas; queda
    nulo si falta futuro o historial suficiente.
11. Genera `data_quality_summary`.

[`corregir_duplicados_dataset_maestro.sql`](SqlScript_Cleaning_Data/corregir_duplicados_dataset_maestro.sql)
es una corrección posterior para semanas que cruzan el cambio de año. Crea
copias de respaldo, reconstruye la agregación usando año ISO y verifica que el
grano quede sin duplicados.

### 3. EDA y validación

[`02_consultas_eda_y_validacion.sql`](SqlScript_Cleaning_Data/02_consultas_eda_y_validacion.sql)
y [`eda_queries.sql`](SqlScript_Cleaning_Data/eda_queries.sql) reúnen 20
consultas de solo lectura sobre:

- estructura y conteos de tablas;
- resumen de calidad, faltantes y duplicados;
- consistencia temporal, territorial y de coordenadas;
- distribuciones, tendencia semanal y categorías principales;
- variable objetivo, outliers IQR y correlaciones;
- auditoría de decisiones de limpieza y grupos de reporte.

### 4. Automatización Python

`Python_Scripts/` conserva la implementación usada para consultar BigQuery por
su API REST, convertir resultados a `pandas.DataFrame`, exportar CSV y generar
figuras, informes Markdown y un dashboard HTML.

Dependencias inferidas del código:

```text
pandas
requests
google-auth
Pillow
```

La autenticación espera una cuenta de servicio indicada mediante
`GOOGLE_APPLICATION_CREDENTIALS`, ya sea como variable de entorno o dentro de
un archivo `.env`. No se deben versionar el JSON de credenciales ni el `.env`.

## Resultados incluidos

La instantánea contiene los siguientes indicadores:

| Indicador | Resultado |
|---|---:|
| Registros originales | 175.317 |
| Reportes limpios | 175.292 |
| Registros excluidos por fecha | 25 |
| Filas del Dataset Maestro | 20.147 |
| Filas con variable objetivo | 18.128 (89,98 %) |
| `report_id` duplicados | 0 |
| Reportes sin provincia | 87.006 (49,63 %) |
| Reportes con coordenadas válidas | 12 |
| Descripciones faltantes | 9.807 (5,59 %) |
| Outliers semanales según IQR | 2.358 (11,70 %) |

Principales limitaciones observadas:

- El 49,63 % de los reportes no tiene provincia, lo que restringe el análisis
  territorial.
- Solo 12 registros tienen coordenadas válidas bajo el criterio aplicado; no
  hay cobertura suficiente para un análisis geoespacial fiable.
- El 10,02 % del Dataset Maestro no tiene etiqueta futura y el 5,60 % carece de
  historial para el rezago de una semana.
- `report_code` no es una clave única (4.590 repeticiones), mientras
  `report_id` sí lo es en la tabla limpia.
- El 11,70 % de las filas semanales supera el umbral IQR; debe estudiarse como
  señal operativa antes de tratarlo como error.

## Estado de consistencia de la evidencia

Los CSV incluidos fueron generados **antes** de aplicar la corrección del grano
semanal: `06_duplicados.csv` registra 59 duplicados y
`18_detalle_duplicados_grano.csv` conserva su detalle. El script correctivo
está incluido, pero en esta instantánea no se aportan CSV regenerados que
demuestren su resultado. Para cerrar esa validación se debe ejecutar la
corrección en BigQuery y volver a generar las 20 consultas.

## Reproducción y requisitos externos

Para reproducir el flujo original se necesitan:

- Windows PowerShell, PostgreSQL/`psql`, Python y Google Cloud CLI (`gcloud` y
  `bq`);
- acceso autorizado a PostgreSQL, Cloud Storage y BigQuery;
- el pipeline PostgreSQL original;
- los CSV de carga, el manifiesto, los esquemas JSON y los SQL de creación de
  vistas/validación esperados por los scripts de migración;
- permisos para habilitar APIs, crear recursos y ejecutar trabajos BigQuery;
- una cuenta de servicio para la automatización Python.

Esta copia no incluye varios de esos recursos. Además, `run_eda.py`,
`test_connection.py` y `config.py` conservan nombres y rutas de la estructura
original (`script_python`, `script_sql`, `outputs`), mientras aquí los archivos
se encuentran en `Python_Scripts`, `SqlScript_Cleaning_Data`,
`data_Generated_csv` e `informes.md`. Por ello, **no deben ejecutarse sin
adaptar primero las rutas o restaurar la estructura original**.

Cuando se disponga del proyecto completo y se hayan ajustado proyecto, región,
datasets y rutas, el orden lógico es:

1. Ejecutar la migración PowerShell.
2. Ejecutar `01_creacion_limpieza_dataset_maestro.sql` en BigQuery.
3. Aplicar `corregir_duplicados_dataset_maestro.sql` si corresponde.
4. Probar la conexión de Python.
5. Ejecutar el EDA y regenerar CSV e informes.
6. Confirmar que la consulta 18 no devuelve filas y que los duplicados del
   grano en la consulta 06 son cero.

## Trazabilidad

En conjunto, el repositorio permite auditar las reglas aplicadas y relacionar
cada control con su resultado. La reproducibilidad completa depende de los
recursos externos y de la estructura original descritos en la sección
anterior.
