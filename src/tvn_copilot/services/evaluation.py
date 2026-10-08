from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import pandas as pd


@dataclass(frozen=True)
class PairwiseClusterMetrics:
    n_items: int
    n_pairs: int
    tp: int
    fp: int
    fn: int
    tn: int
    precision: float
    recall: float
    f1: float


def _valid_label(value: object) -> bool:
    if pd.isna(value):
        return False
    text = str(value).strip()
    return bool(text) and text.lower() not in {"nan", "none", "<na>"}


def pairwise_cluster_metrics(
    df: pd.DataFrame,
    human_col: str = "cluster_humano",
    predicted_col: str = "cluster_semantic",
) -> PairwiseClusterMetrics:
    """Evalúa clustering como decisión par-a-par: mismo evento / distinto evento.

    Solo usa filas con `cluster_humano` no vacío.
    Esto permite que el equipo etiquete una muestra y mida precisión, recall y F1
    sin obligar a que los IDs de cluster humanos y predichos usen la misma nomenclatura.
    """
    for col in (human_col, predicted_col):
        if col not in df.columns:
            raise ValueError(f"Falta la columna requerida: {col}")

    labeled = df[df[human_col].map(_valid_label)].copy().reset_index(drop=True)

    tp = fp = fn = tn = 0

    for i, j in combinations(range(len(labeled)), 2):
        human_same = str(labeled.loc[i, human_col]) == str(labeled.loc[j, human_col])
        pred_same = str(labeled.loc[i, predicted_col]) == str(labeled.loc[j, predicted_col])

        if human_same and pred_same:
            tp += 1
        elif not human_same and pred_same:
            fp += 1
        elif human_same and not pred_same:
            fn += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    return PairwiseClusterMetrics(
        n_items=int(len(labeled)),
        n_pairs=int(len(labeled) * (len(labeled) - 1) / 2),
        tp=int(tp),
        fp=int(fp),
        fn=int(fn),
        tn=int(tn),
        precision=round(float(precision), 4),
        recall=round(float(recall), 4),
        f1=round(float(f1), 4),
    )


def compare_clusterings(
    df: pd.DataFrame,
    human_col: str = "cluster_humano",
    baseline_col: str = "cluster_baseline",
    semantic_col: str = "cluster_semantic",
) -> dict:
    result: dict = {
        "human_column": human_col,
        "baseline_column": baseline_col,
        "semantic_column": semantic_col,
    }

    if baseline_col in df.columns:
        baseline = pairwise_cluster_metrics(df, human_col, baseline_col)
        result["baseline"] = baseline.__dict__
    else:
        result["baseline"] = None

    if semantic_col in df.columns:
        semantic = pairwise_cluster_metrics(df, human_col, semantic_col)
        result["semantic"] = semantic.__dict__
    else:
        result["semantic"] = None

    if result["baseline"] and result["semantic"]:
        result["delta_semantic_vs_baseline"] = {
            "precision": round(
                result["semantic"]["precision"] - result["baseline"]["precision"], 4
            ),
            "recall": round(
                result["semantic"]["recall"] - result["baseline"]["recall"], 4
            ),
            "f1": round(
                result["semantic"]["f1"] - result["baseline"]["f1"], 4
            ),
        }
    else:
        result["delta_semantic_vs_baseline"] = None

    return result


def merge_human_labels(
    predictions: pd.DataFrame,
    labels: pd.DataFrame,
) -> pd.DataFrame:
    """Une etiquetas humanas sin sobrescribir columnas del pipeline."""
    required = {"id_noticia", "cluster_humano"}
    missing = required - set(labels.columns)
    if missing:
        raise ValueError(
            "El archivo de etiquetas humanas debe contener: "
            + ", ".join(sorted(required))
        )

    keep_cols = [
        c for c in (
            "id_noticia",
            "tema_humano",
            "cluster_humano",
            "etiquetador",
            "nota",
        )
        if c in labels.columns
    ]

    labels_small = labels[keep_cols].drop_duplicates(subset=["id_noticia"])
    return predictions.merge(
        labels_small,
        on="id_noticia",
        how="left",
        validate="one_to_one",
    )
