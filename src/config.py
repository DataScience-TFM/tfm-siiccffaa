from __future__ import annotations

from pathlib import Path


PROJECT_ID = "tfm-sbs"
LOCATION = "europe-southwest1"
SOURCE_DATASET = "siiccffaa"
CLEAN_DATASET = "siiccffaa_clean"

BASE_DIR = Path(__file__).resolve().parents[1]
SQL_DIR = BASE_DIR / "sql"
OUTPUT_DIR = BASE_DIR / "outputs"
DATA_DIR = OUTPUT_DIR / "data"
FIGURES_DIR = OUTPUT_DIR / "figures"
REPORTS_DIR = OUTPUT_DIR / "reports"
DOCS_DIR = BASE_DIR / "docs"

SOURCE = f"`{PROJECT_ID}.{SOURCE_DATASET}`"
CLEAN = f"`{PROJECT_ID}.{CLEAN_DATASET}`"

