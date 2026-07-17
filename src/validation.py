from __future__ import annotations

import pandas as pd

from .config import DATE_COLUMN, GROUP_COLUMNS, TARGET


def validate_schema(df: pd.DataFrame, required: list[str]) -> None:
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"Faltan columnas obligatorias: {missing}")
    if df.empty:
        raise ValueError("El dataset está vacío.")


def audit_weekly_continuity(df: pd.DataFrame) -> pd.DataFrame:
    """Localiza saltos: el registro previo del grupo debería estar a 7 días."""
    ordered = df.sort_values(GROUP_COLUMNS + [DATE_COLUMN]).copy()
    ordered["fecha_anterior"] = ordered.groupby(GROUP_COLUMNS)[DATE_COLUMN].shift(1)
    ordered["dias_desde_anterior"] = (
        ordered[DATE_COLUMN] - ordered["fecha_anterior"]
    ).dt.days
    gaps = ordered[
        ordered["dias_desde_anterior"].notna()
        & ordered["dias_desde_anterior"].ne(7)
    ]
    return gaps[
        GROUP_COLUMNS + [DATE_COLUMN, "fecha_anterior", "dias_desde_anterior"]
    ].reset_index(drop=True)


def prepare_labeled_rows(df: pd.DataFrame) -> pd.DataFrame:
    result = df[df[TARGET].notna()].copy()
    result[TARGET] = result[TARGET].astype("int8")
    if not set(result[TARGET].unique()).issubset({0, 1}):
        raise ValueError("El target debe contener únicamente 0, 1 o NULL.")
    duplicated = result.duplicated([DATE_COLUMN] + GROUP_COLUMNS).sum()
    if duplicated:
        raise ValueError(f"Se detectaron {duplicated} filas duplicadas en el grano analítico.")
    return result

