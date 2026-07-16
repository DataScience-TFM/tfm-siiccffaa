from __future__ import annotations

import math
import textwrap
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from .config import FIGURES_DIR


PALETTE = {
    "blue": "#1F4D78",
    "light_blue": "#E8EEF5",
    "green": "#2E7D32",
    "gold": "#B7791F",
    "red": "#9B1C1C",
    "gray": "#5F6B7A",
    "light_gray": "#F4F6F9",
    "ink": "#172033",
    "white": "#FFFFFF",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "arialbd.ttf" if bold else "arial.ttf",
        "calibrib.ttf" if bold else "calibri.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def to_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def draw_wrapped(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], width: int, fnt, fill: str) -> int:
    x, y = xy
    approx_chars = max(12, int(width / max(8, fnt.size * 0.55)))
    for line in textwrap.wrap(str(text), width=approx_chars):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += int(fnt.size * 1.25)
    return y


def save_canvas(path: Path, width: int = 1400, height: int = 850) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (width, height), PALETTE["white"])
    return img, ImageDraw.Draw(img)


def title(draw: ImageDraw.ImageDraw, text: str, subtitle: str | None = None) -> None:
    draw.text((55, 42), text, font=font(34, True), fill=PALETTE["blue"])
    if subtitle:
        draw.text((58, 86), subtitle, font=font(18), fill=PALETTE["gray"])


def bar_chart(
    df: pd.DataFrame,
    label_col: str,
    value_col: str,
    chart_title: str,
    filename: str,
    max_items: int = 12,
    horizontal: bool = True,
) -> None:
    data = df.head(max_items).copy()
    if data.empty:
        return
    data[value_col] = data[value_col].map(to_float)
    values = data[value_col].tolist()
    labels = data[label_col].astype(str).tolist()
    max_value = max(values) if values else 1
    max_value = max(max_value, 1)

    img, draw = save_canvas(FIGURES_DIR / filename)
    title(draw, chart_title)
    if horizontal:
        left, top, bar_w, bar_h, gap = 420, 140, 820, 34, 18
        for idx, (lab, val) in enumerate(zip(labels, values)):
            y = top + idx * (bar_h + gap)
            draw_wrapped(draw, lab, (55, y - 2), 330, font(16), PALETTE["ink"])
            width = int(bar_w * val / max_value)
            draw.rounded_rectangle([left, y, left + bar_w, y + bar_h], radius=8, fill="#EEF2F6")
            draw.rounded_rectangle([left, y, left + width, y + bar_h], radius=8, fill=PALETTE["blue"])
            draw.text((left + width + 12, y + 5), f"{int(val):,}", font=font(15, True), fill=PALETTE["ink"])
    else:
        left, top, bottom, plot_w = 110, 145, 710, 1180
        bar_gap = 18
        bar_w = max(32, int((plot_w - bar_gap * (len(values) - 1)) / len(values)))
        for idx, (lab, val) in enumerate(zip(labels, values)):
            x = left + idx * (bar_w + bar_gap)
            h = int((bottom - top) * val / max_value)
            draw.rounded_rectangle([x, bottom - h, x + bar_w, bottom], radius=6, fill=PALETTE["blue"])
            draw.text((x, bottom + 12), str(lab)[:10], font=font(13), fill=PALETTE["ink"])
            draw.text((x, bottom - h - 24), f"{int(val):,}", font=font(12, True), fill=PALETTE["ink"])
    img.save(FIGURES_DIR / filename)


def line_chart(df: pd.DataFrame, x_col: str, y_col: str, chart_title: str, filename: str) -> None:
    if df.empty:
        return
    data = df.copy()
    data[y_col] = data[y_col].map(to_float)
    values = data[y_col].tolist()
    labels = data[x_col].astype(str).tolist()
    max_v = max(values) if values else 1
    min_v = min(values) if values else 0
    span = max(max_v - min_v, 1)

    img, draw = save_canvas(FIGURES_DIR / filename)
    title(draw, chart_title)
    left, right, top, bottom = 90, 1300, 145, 710
    draw.line([left, bottom, right, bottom], fill="#B8C2CC", width=2)
    draw.line([left, top, left, bottom], fill="#B8C2CC", width=2)
    points = []
    for idx, value in enumerate(values):
        x = left + int(idx * (right - left) / max(1, len(values) - 1))
        y = bottom - int((value - min_v) * (bottom - top) / span)
        points.append((x, y))
    if len(points) > 1:
        draw.line(points, fill=PALETTE["blue"], width=4)
    for x, y in points[:: max(1, len(points) // 20)]:
        draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=PALETTE["gold"])
    draw.text((left, bottom + 28), labels[0], font=font(14), fill=PALETTE["gray"])
    draw.text((right - 90, bottom + 28), labels[-1], font=font(14), fill=PALETTE["gray"])
    draw.text((left + 10, top - 32), f"Máx: {int(max_v):,}", font=font(14, True), fill=PALETTE["ink"])
    draw.text((left + 10, bottom - 28), f"Mín: {int(min_v):,}", font=font(14), fill=PALETTE["gray"])
    img.save(FIGURES_DIR / filename)


def metric_cards(metrics: dict[str, str | int | float], filename: str) -> None:
    img, draw = save_canvas(FIGURES_DIR / filename, 1400, 900)
    title(draw, "Resumen de calidad del dataset limpio", "Indicadores principales usados para documentar el EDA")
    cards = list(metrics.items())
    x0, y0, w, h = 70, 150, 390, 150
    for idx, (label, value) in enumerate(cards):
        row, col = divmod(idx, 3)
        x = x0 + col * 430
        y = y0 + row * 185
        draw.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=PALETTE["light_gray"], outline="#CBD5E1", width=2)
        draw_wrapped(draw, label, (x + 24, y + 22), w - 48, font(17, True), PALETTE["blue"])
        draw.text((x + 24, y + 88), str(value), font=font(28, True), fill=PALETTE["ink"])
    img.save(FIGURES_DIR / filename)


def process_diagram(filename: str) -> None:
    img, draw = save_canvas(FIGURES_DIR / filename, 1500, 620)
    title(draw, "Ciclo práctico realizado de Ciencia de Datos", "Desde BigQuery limpio hasta documentación, visualización y modelado")
    steps = [
        ("Carga", "BigQuery\nsiiccffaa_clean"),
        ("Estructura", "Tipos, claves\ny tablas"),
        ("Calidad", "Nulos, duplicados,\nconsistencia"),
        ("EDA", "Distribuciones,\nrelaciones, outliers"),
        ("Entrega", "Reportes,\nfiguras y SQL"),
    ]
    x, y, w, h, gap = 70, 220, 235, 175, 48
    for idx, (name, desc) in enumerate(steps):
        x1 = x + idx * (w + gap)
        draw.rounded_rectangle([x1, y, x1 + w, y + h], radius=20, fill=PALETTE["light_blue"], outline=PALETTE["blue"], width=3)
        draw.text((x1 + 26, y + 26), name, font=font(23, True), fill=PALETTE["blue"])
        draw_wrapped(draw, desc, (x1 + 26, y + 72), w - 52, font(17), PALETTE["ink"])
        if idx < len(steps) - 1:
            ax = x1 + w + 8
            ay = y + h // 2
            draw.line([ax, ay, ax + gap - 16, ay], fill=PALETTE["gold"], width=5)
            draw.polygon([(ax + gap - 16, ay - 10), (ax + gap + 2, ay), (ax + gap - 16, ay + 10)], fill=PALETTE["gold"])
    img.save(FIGURES_DIR / filename)


def heatmap_from_cross(df: pd.DataFrame, filename: str) -> None:
    if df.empty:
        return
    data = df.copy()
    data["reportes"] = data["reportes"].map(to_float)
    top_prov = data.groupby("provincia_name")["reportes"].sum().sort_values(ascending=False).head(10).index.tolist()
    top_cat = data.groupby("report_type_category")["reportes"].sum().sort_values(ascending=False).head(8).index.tolist()
    matrix = data[data["provincia_name"].isin(top_prov) & data["report_type_category"].isin(top_cat)]
    pivot = matrix.pivot_table(index="provincia_name", columns="report_type_category", values="reportes", aggfunc="sum", fill_value=0)
    pivot = pivot.reindex(index=top_prov, columns=top_cat, fill_value=0)
    max_v = max(float(pivot.values.max()), 1.0)

    img, draw = save_canvas(FIGURES_DIR / filename, 1600, 900)
    title(draw, "Cruce provincia vs categoría de reporte", "Mapa de intensidad para priorizar revisión operativa")
    left, top, cell_w, cell_h = 360, 180, 135, 56
    for c_idx, col in enumerate(pivot.columns):
        draw_wrapped(draw, str(col), (left + c_idx * cell_w, 112), cell_w - 8, font(11, True), PALETTE["ink"])
    for r_idx, idx in enumerate(pivot.index):
        y = top + r_idx * cell_h
        draw_wrapped(draw, str(idx), (55, y + 10), 280, font(14), PALETTE["ink"])
        for c_idx, col in enumerate(pivot.columns):
            val = float(pivot.loc[idx, col])
            intensity = int(240 - 150 * (val / max_v))
            fill = (intensity, intensity + 8 if intensity < 245 else 245, 255)
            x = left + c_idx * cell_w
            draw.rectangle([x, y, x + cell_w - 4, y + cell_h - 4], fill=fill, outline="#FFFFFF")
            if val > 0:
                draw.text((x + 10, y + 18), f"{int(val):,}", font=font(11, True), fill=PALETTE["ink"])
    img.save(FIGURES_DIR / filename)


def generate_all_figures(results: dict[str, pd.DataFrame]) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    process_diagram("01_ciclo_practico_ciencia_datos.png")

    quality = results.get("03_resumen_calidad", pd.DataFrame())
    metrics: dict[str, str] = {}
    if not quality.empty:
        q = dict(zip(quality["metric"], quality["value"]))
        for key, label in [
            ("reports_original_total", "Reportes originales"),
            ("fact_reportes_limpios_total", "Reportes limpios"),
            ("dataset_maestro_modelado_total", "Filas Dataset Maestro"),
            ("dataset_maestro_con_target", "Filas con target"),
            ("fact_reportes_sin_provincia", "Reportes sin provincia"),
            ("fact_reportes_con_coordenadas_validas", "Coordenadas válidas"),
        ]:
            if key in q:
                metrics[label] = f"{to_int(q[key]):,}"
    metric_cards(metrics, "02_resumen_calidad_dataset.png")

    year_month = results["08_distribucion_anio_mes"].copy()
    year_month["reportes"] = year_month["reportes"].map(to_float)
    by_year = year_month.groupby("report_year", as_index=False)["reportes"].sum()
    bar_chart(by_year, "report_year", "reportes", "Reportes por año", "03_reportes_por_anio.png", horizontal=False)
    line_chart(results["09_tendencia_semanal"], "report_week_start", "reportes", "Tendencia semanal de reportes", "04_tendencia_semanal.png")
    bar_chart(results["10_top_provincias"], "provincia_name", "reportes", "Top provincias por volumen de reportes", "05_top_provincias.png")
    bar_chart(results["11_top_tipos_reporte"], "report_type_name", "reportes", "Top tipos de reporte", "06_top_tipos_reporte.png")
    bar_chart(results["12_top_instituciones"], "company_name", "reportes", "Top instituciones reportantes", "07_top_instituciones.png")
    bar_chart(results["04_faltantes_fact_reportes"], "column_name", "missing_count", "Valores faltantes en campos clave", "08_faltantes_fact_reportes.png")
    bar_chart(results["05_faltantes_dataset_maestro"], "column_name", "missing_count", "Faltantes en Dataset Maestro", "09_faltantes_dataset_maestro.png")
    bar_chart(results["14_distribucion_target"], "target_class", "filas", "Distribución de la variable objetivo", "10_distribucion_target.png")
    bar_chart(results["16_correlaciones_numericas"], "variable", "corr_with_reportes_semana", "Correlación con reportes_semana", "11_correlaciones_numericas.png")
    bar_chart(results["07_consistencia"], "check_name", "affected_rows", "Reglas de consistencia revisadas", "12_consistencia.png")
    heatmap_from_cross(results["17_cruce_provincia_categoria"], "13_heatmap_provincia_categoria.png")
