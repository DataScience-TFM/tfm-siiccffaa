from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_ROOT = PROJECT_ROOT / "script_python"
sys.path.insert(0, str(PYTHON_ROOT))

from script_python.bigquery_runner import BigQueryRunner
from script_python.config import DATA_DIR, DOCS_DIR, FIGURES_DIR, REPORTS_DIR, SQL_DIR
from script_python.queries import QUERIES
from script_python.reporting import generate_dashboard_html, generate_markdown_reports
from script_python.visualizations import generate_all_figures


def ensure_directories() -> None:
    for path in [SQL_DIR, DATA_DIR, FIGURES_DIR, REPORTS_DIR, DOCS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def write_sql_bundle() -> None:
    chunks = []
    for name, sql in QUERIES.items():
        chunks.append(f"-- {name}\n{sql.strip()}\n")
    (SQL_DIR / "eda_queries.sql").write_text("\n\n".join(chunks), encoding="utf-8")


def main() -> None:
    ensure_directories()
    write_sql_bundle()
    runner = BigQueryRunner()
    results = {}
    print("Iniciando EDA práctico contra BigQuery...")
    for name, sql in QUERIES.items():
        print(f"  Ejecutando {name}...")
        results[name] = runner.save_query(name, sql)
    print("Generando visualizaciones...")
    generate_all_figures(results)
    print("Generando reportes...")
    generate_markdown_reports(results)
    generate_dashboard_html()
    print("\nProyecto EDA ejecutado correctamente.")
    print(f"CSV:      {DATA_DIR}")
    print(f"Figuras:  {FIGURES_DIR}")
    print(f"Reportes: {REPORTS_DIR}")
    print(f"SQL:      {SQL_DIR / 'eda_queries.sql'}")


if __name__ == "__main__":
    main()
