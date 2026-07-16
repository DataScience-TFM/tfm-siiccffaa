from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_ROOT = PROJECT_ROOT / "script_python"
sys.path.insert(0, str(PYTHON_ROOT))

from script_python.bigquery_runner import BigQueryRunner


def main() -> None:
    runner = BigQueryRunner()
    result = runner.query_to_dataframe(
        "SELECT COUNT(*) AS total "
        "FROM `tfm-sbs.siiccffaa_clean.fact_reportes_limpios`"
    )
    print("Conexión REST correcta.")
    print(f"Registros disponibles: {result.iloc[0]['total']}")


if __name__ == "__main__":
    main()
