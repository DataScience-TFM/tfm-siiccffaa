# Dashboard interactivo SIICCFFAA

## Finalidad

He desarrollado esta aplicación para consultar en vivo el dataset analítico `tfm-sbs.siiccffaa_clean` de BigQuery y presentar los resultados del análisis mediante gráficos Plotly y tablas interactivas.

Esta carpeta contiene solamente los componentes necesarios para ejecutar el dashboard. La evidencia de preparación, limpieza y análisis exploratorio se entrega en la carpeta independiente `Evidencia_EDA`, situada al mismo nivel que este proyecto.

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

```text
Proyecto_Python_Analisis_Exploratorio/
├── .env
├── .gitignore
├── README.md
├── requirements.txt
├── run_web.ps1
├── web_app.py
├── credentials/                 # Se crea al recibir la credencial
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── bigquery_runner.py
│   └── queries.py
├── templates/
│   └── index.html
└── static/
    ├── styles.css
    └── live.css
```

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

## Funcionamiento interno

```text
.env y cuenta de servicio
          ↓
src/bigquery_runner.py
          ↓
src/queries.py
          ↓
API REST HTTPS de BigQuery
          ↓
DataFrames en memoria
          ↓
web_app.py / Flask
          ↓
Plotly en el navegador
```

La dirección `127.0.0.1` indica que el servidor se ejecuta en el ordenador del evaluador. Los datos se siguen consultando en BigQuery por Internet.

## Caché y actualización

Los resultados se conservan durante 15 minutos para reducir latencia y consultas repetidas. El botón **Actualizar desde BigQuery** fuerza una ejecución nueva de las 20 consultas.

## Evidencia entregada por separado

La carpeta hermana `Evidencia_EDA` contiene:

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
