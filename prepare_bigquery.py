from __future__ import annotations

from pathlib import Path
from google.cloud import bigquery

from src.config import Settings, configure_credentials


def main() -> None:
    settings = Settings()
    credential_path = configure_credentials(Path(__file__).parent)
    sql_path = Path(__file__).parent / "sql" / "01_dataset_semanal_continuo.sql"
    if not sql_path.exists():
        raise FileNotFoundError(f"No existe el archivo SQL: {sql_path}")
    sql = sql_path.read_text(encoding="utf-8")
    client = bigquery.Client(project=settings.project_id, location=settings.location)
    print(f"Credencial localizada: {credential_path.name}")
    print(f"Ejecutando {sql_path.name} en {settings.project_id} ({settings.location})...")
    rows = list(client.query(sql, location=settings.location).result())
    if rows:
        raise RuntimeError(
            f"La auditoría encontró {len(rows)} saltos temporales. "
            "Revise el resultado de la consulta antes de entrenar."
        )
    print("Preparación terminada. La auditoría temporal devolvió cero saltos.")


if __name__ == "__main__":
    main()
