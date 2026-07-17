from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_id: str = os.getenv("GCP_PROJECT_ID", "tfm-sbs")
    location: str = os.getenv("BIGQUERY_LOCATION", "europe-southwest1")
    model_table: str = os.getenv(
        "MODEL_TABLE", "tfm-sbs.siiccffaa_clean.dataset_maestro_modelado_continuo"
    )
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", "outputs"))
    model_dir: Path = Path(os.getenv("MODEL_DIR", "models"))
    top_k: int = int(os.getenv("TOP_K", "20"))


TARGET = "incremento_actividad_siguiente_periodo"
DATE_COLUMN = "report_week_start"
GROUP_COLUMNS = ["provincia_id", "report_type_id"]
NUMERIC_FEATURES = [
    "reportes_lag_1w",
    "reportes_lag_2w",
    "reportes_lag_4w",
    "reportes_media_4w_previa",
    "reportes_std_4w_previa",
]
CATEGORICAL_FEATURES = ["provincia_id", "report_type_id"]
DERIVED_FEATURES = ["mes", "semana_anio"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES + DERIVED_FEATURES
FORBIDDEN_FEATURES = ["reportes_siguiente_semana", TARGET]


def configure_credentials(project_root: Path | None = None) -> Path:
    """Convierte la credencial configurada a ruta absoluta y valida su existencia."""
    root = project_root or Path(__file__).resolve().parents[1]
    configured = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip().strip('"')
    if not configured:
        local_dir = root / "credentials"
        sibling_dir = root.parent / "Proyecto_Python_Analisis_Exploratorio" / "credentials"
        candidates = [
            local_dir / "tfm-evaluacion-api.json",
            local_dir / "tfm-evaluacion-api.key",
            sibling_dir / "tfm-evaluacion-api.json",
            sibling_dir / "tfm-evaluacion-api.key",
        ]
        candidates.extend(sorted(local_dir.glob("*.json")) if local_dir.is_dir() else [])
        for candidate in candidates:
            if candidate.is_file():
                configured = str(candidate)
                break
        if not configured:
            raise FileNotFoundError(
                "No se definio GOOGLE_APPLICATION_CREDENTIALS y no se encontro una credencial "
                "JSON en la carpeta credentials del proyecto."
            )
    path = Path(configured).expanduser()
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(
            f"No se encontro la credencial en: {path}\n"
            "Cree credentials en la raiz del proyecto y copie alli tfm-evaluacion-api.json."
        )
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(path)
    return path
