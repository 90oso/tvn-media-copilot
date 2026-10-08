from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# Windows: cargar torch primero para evitar el conflicto DLL ya diagnosticado.
if sys.platform.startswith("win"):
    try:
        import torch  # noqa: F401
    except Exception:
        pass

import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tvn_copilot.services.classification import OFFICIAL_TOPICS
from tvn_copilot.services.embeddings import load_embeddings
from tvn_copilot.services.semantic_classification import (
    SemanticClassificationConfig,
    classify_with_topic_centroids,
)


def build_parser():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/noticias_grouped_semantic.csv"),
    )
    p.add_argument(
        "--embeddings",
        type=Path,
        default=Path("data/embeddings/news_embeddings.npz"),
    )
    p.add_argument(
        "--labels",
        type=Path,
        default=Path("data/etiquetas_humanas.csv"),
    )
    p.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/noticias_ready.csv"),
    )
    p.add_argument(
        "--report",
        type=Path,
        default=Path("reports/evaluation/semantic_classification.json"),
    )
    p.add_argument("--min-similarity", type=float, default=0.45)
    p.add_argument("--min-margin", type=float, default=0.04)
    p.add_argument("--min-seeds", type=int, default=5)
    return p


def _human_evaluation(result: pd.DataFrame, labels_path: Path) -> dict:
    if not labels_path.exists():
        return {"available": False, "reason": "No existe archivo de etiquetas humanas."}

    labels = pd.read_csv(labels_path, dtype="string")
    if "tema_humano" not in labels.columns:
        return {"available": False, "reason": "No existe columna tema_humano."}

    valid = labels[
        labels["tema_humano"].astype("string").isin(OFFICIAL_TOPICS)
    ][["id_noticia", "tema_humano"]].drop_duplicates("id_noticia")

    if len(valid) < 2:
        return {
            "available": False,
            "reason": "No hay suficientes etiquetas tema_humano válidas.",
            "n_labeled": int(len(valid)),
        }

    merged = result.merge(valid, on="id_noticia", how="inner")
    y_true = merged["tema_humano"].astype(str)
    y_pred = merged["tema_final"].astype(str)

    return {
        "available": True,
        "n_labeled": int(len(merged)),
        "coverage_on_labeled": round(
            float(y_pred.isin(OFFICIAL_TOPICS).mean()), 4
        ),
        "macro_precision": round(
            float(
                precision_score(
                    y_true,
                    y_pred,
                    labels=list(OFFICIAL_TOPICS),
                    average="macro",
                    zero_division=0,
                )
            ),
            4,
        ),
        "macro_recall": round(
            float(
                recall_score(
                    y_true,
                    y_pred,
                    labels=list(OFFICIAL_TOPICS),
                    average="macro",
                    zero_division=0,
                )
            ),
            4,
        ),
        "macro_f1": round(
            float(
                f1_score(
                    y_true,
                    y_pred,
                    labels=list(OFFICIAL_TOPICS),
                    average="macro",
                    zero_division=0,
                )
            ),
            4,
        ),
    }


def main() -> int:
    args = build_parser().parse_args()

    if not args.input.exists():
        print(f"ERROR: No existe {args.input}")
        return 2
    if not args.embeddings.exists():
        print(f"ERROR: No existe {args.embeddings}")
        return 3

    df = pd.read_csv(args.input, dtype="string")
    ids, vectors = load_embeddings(args.embeddings)

    config = SemanticClassificationConfig(
        min_similarity=args.min_similarity,
        min_margin=args.min_margin,
        min_seed_items_per_topic=args.min_seeds,
    )

    result, summary = classify_with_topic_centroids(
        df,
        ids,
        vectors,
        config=config,
    )

    human_eval = _human_evaluation(result, args.labels)
    summary["human_evaluation"] = human_eval

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False, encoding="utf-8")
    args.report.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=== TVN Media Copilot | Clasificación semántica temática ===")
    print(f"Noticias: {summary['rows']}")
    print(f"Baseline clasificadas: {summary['baseline_classified']}")
    print(f"Semántico clasificadas: {summary['semantic_classified']}")
    print(f"Final clasificadas: {summary['final_classified']}")
    print(f"Final sin clasificar: {summary['final_unclassified']}")
    print(f"Cobertura final: {summary['final_coverage']:.2%}")
    print(f"Conflictos baseline/semántico: {summary['baseline_semantic_conflicts']}")
    print(f"Salida: {args.output}")
    print(f"Reporte: {args.report}")

    if human_eval.get("available"):
        print(
            "Evaluación tema_humano: "
            f"P={human_eval['macro_precision']:.4f} "
            f"R={human_eval['macro_recall']:.4f} "
            f"F1={human_eval['macro_f1']:.4f}"
        )
    else:
        print(
            "Evaluación temática humana no disponible: "
            f"{human_eval.get('reason')}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
