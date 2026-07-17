from __future__ import annotations

import json
import io
import shutil
import subprocess
import tempfile
from pathlib import Path
from flask import Flask, abort, jsonify, render_template, send_file, send_from_directory
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
MODELS = ROOT / "models"

app = Flask(__name__)

ARTIFACTS = {
    "confusion_matrix.png",
    "precision_recall_curve.png",
    "roc_curve.png",
}


def clean_text(value):
    """Repara texto UTF-8 leído previamente como Windows-1252, cuando aplica."""
    if not isinstance(value, str):
        return value
    if any(marker in value for marker in ("Ã", "Â", "â€")):
        try:
            return value.encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return value
    return value


def read_csv(name: str) -> pd.DataFrame:
    path = OUTPUTS / name
    if not path.is_file():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path)
    for column in frame.select_dtypes(include="object"):
        frame[column] = frame[column].map(clean_text)
    return frame


def load_dashboard():
    comparison = read_csv("model_comparison.csv")
    predictions = read_csv("predictions_test.csv")
    coefficients = read_csv("coefficients.csv")
    metadata_path = MODELS / "metadata.json"
    if not metadata_path.is_file():
        raise FileNotFoundError(metadata_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    logistic = comparison.loc[comparison["modelo"].eq("regresion_logistica")].iloc[0]
    comparison_display = comparison.copy()
    labels = {
        "clase_mayoritaria": "Clase mayoritaria",
        "regla_persistencia": "Regla de persistencia",
        "regresion_logistica": "Regresión logística",
    }
    comparison_display["nombre"] = comparison_display["modelo"].map(labels)
    metric_columns = ["precision", "recall", "f1", "pr_auc", "roc_auc", "precision_at_20"]
    for column in metric_columns:
        comparison_display[column] = comparison_display[column].astype(float)

    coefficients = coefficients.head(15).copy()
    coefficients["sentido"] = coefficients["coeficiente"].apply(
        lambda value: "Aumenta" if value > 0 else "Reduce"
    )
    predictions["report_week_start"] = pd.to_datetime(
        predictions["report_week_start"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    predictions = predictions.sort_values("probabilidad_incremento", ascending=False)
    top_predictions = predictions.head(200).copy()

    return {
        "comparison": comparison_display.to_dict("records"),
        "metrics": {
            "threshold": float(logistic["threshold"]),
            "precision": float(logistic["precision"]),
            "recall": float(logistic["recall"]),
            "f1": float(logistic["f1"]),
            "pr_auc": float(logistic["pr_auc"]),
            "roc_auc": float(logistic["roc_auc"]),
            "precision_at_20": float(logistic["precision_at_20"]),
        },
        "metadata": metadata,
        "coefficients": coefficients.to_dict("records"),
        "predictions": top_predictions.to_dict("records"),
        "total_predictions": len(predictions),
        "positive_predictions": int(predictions["prediccion"].sum()),
        "actual_increments": int(predictions["valor_real"].sum()),
        "last_week": predictions["report_week_start"].max(),
    }


def load_diario():
    path = OUTPUTS / "diario_ejecutivo.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def browser_executable() -> Path:
    candidates = [
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("No se encontró Microsoft Edge ni Google Chrome para generar el PDF.")


@app.get("/")
def index():
    try:
        return render_template("model_dashboard.html", **load_dashboard())
    except FileNotFoundError as exc:
        return render_template("model_dashboard.html", load_error=f"Falta el archivo: {exc}"), 503


@app.get("/artifact/<name>")
def artifact(name: str):
    if name not in ARTIFACTS:
        abort(404)
    return send_from_directory(OUTPUTS, name)


@app.get("/api/summary")
def api_summary():
    data = load_dashboard()
    return jsonify({
        "metrics": data["metrics"],
        "metadata": data["metadata"],
        "comparison": data["comparison"],
        "total_predictions": data["total_predictions"],
    })


@app.get("/diario")
def diario():
    try:
        return render_template("diario_ejecutivo.html", report=load_diario(), print_mode=False)
    except FileNotFoundError as exc:
        return render_template("diario_ejecutivo.html", load_error=f"Falta el archivo: {exc}", print_mode=False), 503


@app.get("/diario/print")
def diario_print():
    return render_template("diario_ejecutivo.html", report=load_diario(), print_mode=True)


@app.get("/diario/pdf")
def diario_pdf():
    browser = browser_executable()
    (ROOT / "tmp").mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="diario_pdf_", dir=ROOT / "tmp"))
    pdf_path = temp_dir / "Diario_Ejecutivo_SIICCFFAA.pdf"
    profile = temp_dir / "browser_profile"
    command = [
        str(browser), "--headless", "--disable-gpu", "--no-pdf-header-footer",
        f"--user-data-dir={profile}", f"--print-to-pdf={pdf_path}",
        "http://127.0.0.1:8001/diario/print",
    ]
    try:
        subprocess.run(command, check=True, timeout=75, capture_output=True)
        if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
            raise RuntimeError("El navegador no produjo el archivo PDF.")
        content = pdf_path.read_bytes()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    return send_file(
        io.BytesIO(content), mimetype="application/pdf", as_attachment=True,
        download_name="Diario_Ejecutivo_SIICCFFAA.pdf",
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8001, debug=False)
