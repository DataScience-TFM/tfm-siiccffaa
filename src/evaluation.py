from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    average_precision_score, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score, precision_recall_curve, roc_curve,
)


def metrics_at_threshold(y_true, probability, threshold: float, top_k: int) -> dict:
    y_true = np.asarray(y_true)
    probability = np.asarray(probability)
    pred = (probability >= threshold).astype(int)
    k = min(top_k, len(y_true))
    top_idx = np.argsort(-probability)[:k]
    return {
        "threshold": threshold,
        "precision": precision_score(y_true, pred, zero_division=0),
        "recall": recall_score(y_true, pred, zero_division=0),
        "f1": f1_score(y_true, pred, zero_division=0),
        "pr_auc": average_precision_score(y_true, probability),
        "roc_auc": roc_auc_score(y_true, probability) if len(np.unique(y_true)) == 2 else np.nan,
        f"precision_at_{k}": float(y_true[top_idx].mean()) if k else np.nan,
    }


def choose_threshold(y_true, probability) -> float:
    candidates = np.arange(0.20, 0.81, 0.01)
    scores = [f1_score(y_true, probability >= t, zero_division=0) for t in candidates]
    return float(candidates[int(np.argmax(scores))])


def save_plots(y_true, probability, threshold: float, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    pred = (probability >= threshold).astype(int)
    cm = confusion_matrix(y_true, pred, labels=[0, 1])
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["No incremento", "Incremento"],
                yticklabels=["No incremento", "Incremento"])
    plt.xlabel("Predicción"); plt.ylabel("Valor real"); plt.tight_layout()
    plt.savefig(output_dir / "confusion_matrix.png", dpi=180); plt.close()

    precision, recall, _ = precision_recall_curve(y_true, probability)
    plt.figure(figsize=(6, 5)); plt.plot(recall, precision)
    plt.xlabel("Recall"); plt.ylabel("Precisión"); plt.title("Curva precisión-recall")
    plt.tight_layout(); plt.savefig(output_dir / "precision_recall_curve.png", dpi=180); plt.close()

    fpr, tpr, _ = roc_curve(y_true, probability)
    plt.figure(figsize=(6, 5)); plt.plot(fpr, tpr); plt.plot([0, 1], [0, 1], "--", color="gray")
    plt.xlabel("Tasa de falsos positivos"); plt.ylabel("Tasa de verdaderos positivos")
    plt.title("Curva ROC"); plt.tight_layout()
    plt.savefig(output_dir / "roc_curve.png", dpi=180); plt.close()


def extract_coefficients(pipeline) -> pd.DataFrame:
    names = pipeline.named_steps["preprocess"].get_feature_names_out()
    values = pipeline.named_steps["classifier"].coef_[0]
    result = pd.DataFrame({"variable": names, "coeficiente": values})
    result["odds_ratio"] = np.exp(result["coeficiente"])
    result["magnitud"] = result["coeficiente"].abs()
    return result.sort_values("magnitud", ascending=False).drop(columns="magnitud")

