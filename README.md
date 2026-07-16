# Dashboard interactivo SIICCFFAA

## Finalidad

He desarrollado esta aplicación para consultar en vivo el dataset analítico `tfm-sbs.siiccffaa_clean` de BigQuery y presentar los resultados del análisis mediante gráficos Plotly y tablas interactivas.

Esta carpeta contiene solamente los componentes necesarios para ejecutar el dashboard. La evidencia de preparación, limpieza y análisis exploratorio se entrega en la carpeta independiente `Evidencia_Migration_and_Data_Cleaning`, situada al mismo nivel que este proyecto.

## Objetivo del análisis

El análisis explora la calidad, distribución temporal, concentración territorial y comportamiento operacional de los reportes del SIICCFFAA. También prepara y revisa un Dataset Maestro de granularidad semanal por provincia y tipo de reporte para anticipar incrementos de actividad y apoyar la planificación operativa del C5i.

## Variable objetivo

La variable objetivo es `incremento_actividad_siguiente_periodo`. Convierte la necesidad de anticipar aumentos de reportes en un problema de clasificación binaria:

- `1` (`incremento`): los reportes de la semana siguiente son mayores que la media de las cuatro semanas anteriores.
- `0` (`no_incremento`): los reportes de la semana siguiente no superan esa media histórica.
- `NULL` (`sin_target`): no existe una semana siguiente o no hay historial suficiente para calcular la referencia.

Se eligió porque permite anticipar si la actividad de una combinación de provincia y tipo de reporte aumentará respecto a su comportamiento reciente. Esta señal puede ayudar a priorizar seguimiento y recursos. Las filas sin target se conservan para auditoría, pero no deben utilizarse como observaciones etiquetadas durante el entrenamiento supervisado.

## Fuente de los datos

- Proyecto de Google Cloud: `tfm-sbs`.
- Dataset original: `siiccffaa`.
- Dataset consultado por el dashboard: `siiccffaa_clean`.
- Ubicación: `europe-southwest1`.

La aplicación no consulta CSV locales. Python envía las 20 consultas definidas en `src/queries.py` directamente a la API REST HTTPS de BigQuery. Los resultados se mantienen temporalmente en memoria y se entregan al navegador para construir los gráficos.

## Credencial de la cuenta de servicio

El archivo de credenciales pertenece a una cuenta de servicio autorizada para ejecutar consultas y leer los datos necesarios de BigQuery. La credencial será enviada por correo electrónico al profesor Jaime.

Después de recibirla debe:

1. Crear una carpeta llamada `credentials` dentro de este proyecto.
2. Guardar el archivo recibido con el nombre `tfm-evaluacion-api.key`.
3. Comprobar que `.env` contiene:

```dotenv
GOOGLE_APPLICATION_CREDENTIALS=credentials/tfm-evaluacion-api.key
```

La ruta es relativa y funciona con independencia del usuario de Windows, de la unidad o de la ubicación donde se copie el proyecto.

## Requisitos

- Windows 10 u 11.
- Python 3.12 o compatible.
- PowerShell.
- Conexión a Internet.
- Credenciales válidas de la cuenta de servicio.
- Permisos para consultar BigQuery.

No es necesario instalar Google Cloud SDK, `gcloud`, `bq` ni `google-cloud-bigquery`.

## Cómo ejecutar el dashboard

1. Descomprimir la carpeta del proyecto.
2. Incorporar las credenciales siguiendo la sección anterior.
3. Abrir esta carpeta en el Explorador de archivos.
4. Escribir `powershell` en la barra de la ruta y pulsar `Enter`.
5. Ejecutar:

```powershell
.\run_web.ps1
```

El lanzador realiza automáticamente estas tareas:

- Lee `.env`.
- Resuelve la ruta de las credenciales desde la carpeta del proyecto.
- Crea `.venv` si no existe.
- Prepara `pip` cuando es necesario.
- Instala las dependencias que falten.
- Abre el navegador.
- Inicia Flask en `http://127.0.0.1:8000`.

Si PowerShell bloquea la ejecución de scripts, se puede autorizar únicamente la sesión actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_web.ps1
```

Para detener la aplicación se debe volver a PowerShell y pulsar `Ctrl+C`.

## Estructura actual

![alt text](image.png)

## Función de cada archivo

### `.env`

Define la ubicación portable del archivo de credenciales. No contiene la clave privada.

### `.gitignore`

Evita publicar credenciales, entornos virtuales, cachés y configuraciones locales.

### `requirements.txt`

Contiene las bibliotecas necesarias para el dashboard:

- `pandas`: organiza resultados en DataFrames.
- `Flask`: sirve la aplicación web.
- `plotly`: dibuja gráficos interactivos.
- `google-auth`: obtiene tokens temporales de autenticación.
- `requests`: se comunica con la API REST de BigQuery.

### `run_web.ps1`

Es el lanzador recomendado para Windows. Automatiza la preparación del entorno y el inicio del servidor.

### `web_app.py`

Es la aplicación principal. Ejecuta las consultas, prepara los indicadores, mantiene una caché de 15 minutos y ofrece cuatro rutas:

- `/`: dashboard principal.
- `/refresh`: actualización forzada desde BigQuery.
- `/plotly.js`: biblioteca gráfica.
- `/data/<consulta>`: resultado estructurado de una consulta.

### `src/config.py`

Define el proyecto, datasets, ubicación y nombres utilizados por las consultas.

### `src/bigquery_runner.py`

Lee las credenciales, obtiene un token OAuth temporal, envía el SQL a BigQuery, espera el job, recupera todas las páginas y devuelve DataFrames.

### `src/queries.py`

Contiene las 20 consultas del dashboard: calidad, faltantes, duplicados, consistencia, tendencias, territorio, operación, target, IQR y correlaciones.

### `src/__init__.py`

Permite utilizar `src` como paquete de Python.

### `templates/index.html`

Define la estructura de la página, los filtros, los contenedores Plotly y la tabla de resultados.

### `static/styles.css` y `static/live.css`

Definen el diseño visual general y los ajustes específicos de la aplicación conectada en vivo.

## Contenido del análisis exploratorio

El dashboard cubre los siguientes apartados:

1. Objetivo del análisis y contexto operativo.
2. Carga en vivo del dataset limpio desde BigQuery.
3. Validación de calidad: estructura, faltantes, duplicados y consistencia.
4. Análisis univariante de tiempo, territorio, tipos, instituciones, estados y target.
5. Análisis bivariante y multivariante mediante cruces territoriales y correlaciones.
6. Detección de valores atípicos mediante el rango intercuartílico (IQR).
7. Visualizaciones interactivas con Plotly.
8. Hallazgos principales calculados automáticamente a partir de los resultados actuales.
9. Limitaciones metodológicas y de calidad de los datos.

### Valores atípicos mediante IQR

La consulta `15_outliers_iqr_reportes_semana` calcula Q1, Q3 y el rango intercuartílico (`IQR = Q3 - Q1`). Se consideran posibles valores atípicos aquellos situados fuera de `Q1 - 1,5 × IQR` y `Q3 + 1,5 × IQR`. El dashboard representa cuántas filas permanecen dentro de esos límites y cuántas quedan fuera. Un valor atípico no se considera automáticamente un error: puede reflejar un evento operativo real que requiere revisión.

### Hallazgos principales

La sección de hallazgos se actualiza con los datos obtenidos de BigQuery y resume la provincia y el tipo de reporte con mayor frecuencia, la proporción de la clase incremento, la cantidad y porcentaje de atípicos y la correlación lineal de mayor magnitud con `reportes_semana`. Son resultados descriptivos y no demuestran causalidad.

### Limitaciones

- La calidad de las conclusiones depende de la integridad y exactitud de los datos originales.
- Los registros sin provincia, las coordenadas no válidas y los valores ausentes pueden reducir la representatividad de algunos cruces.
- El IQR identifica observaciones inusuales, pero no determina por sí mismo si son errores.
- Las correlaciones describen asociaciones y no relaciones causales.
- Las primeras semanas pueden carecer de retardos o medias móviles, y el último periodo puede no tener target conocido.
- Los resultados corresponden a la versión de BigQuery disponible al ejecutar las consultas y pueden cambiar tras nuevas cargas o correcciones.

## Funcionamiento interno

```text
1- .env y cuenta de servicio
          
2- src/bigquery_runner.py
          
3- src/queries.py
          
4- API REST HTTPS de BigQuery
          
5- DataFrames en memoria
          
6- web_app.py / Flask
          
7- Plotly en el navegador
```

La dirección `127.0.0.1` indica que el servidor se ejecuta en el ordenador del evaluador. Los datos se siguen consultando en BigQuery por Internet.

## Caché y actualización

Los resultados se conservan durante 15 minutos para reducir latencia y consultas repetidas. El botón **Actualizar desde BigQuery** fuerza una ejecución nueva de las 20 consultas.

## Evidencia entregada por separado

La carpeta hermana `Evidencia_Migration_and_Data_Cleaning` contiene:

- Las sentencias reales de preparación y limpieza.
- La creación de dimensiones y de `fact_reportes_limpios`.
- La construcción de `agg_reportes_semanal`.
- La construcción de `dataset_maestro_modelado` y de la variable objetivo.
- Las 20 consultas EDA.
- Los CSV resultantes.
- Los informes y el dashboard estático.
- Los scripts utilizados para generar la evidencia.
- Un documento Word que explica paso a paso la limpieza de los datos originales.

El dashboard no necesita esa carpeta para funcionar. Se entrega por separado para que el profesor pueda auditar cómo se prepararon y validaron los datos.

## Errores frecuentes

### No existe el archivo de credenciales

Comprobar:

```text
credentials/tfm-evaluacion-api.key
```

### Error 403

La cuenta se ha autenticado, pero no tiene permisos suficientes para crear jobs o leer alguna tabla.

### El navegador no se abre

Escribir manualmente:

```text
http://127.0.0.1:8000
```

### Los datos no cambian

Pulsar **Actualizar desde BigQuery** para evitar la caché de 15 minutos.
