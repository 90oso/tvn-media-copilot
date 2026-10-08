from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tvn_copilot.services.semantic_grouping import (
    SemanticGroupingConfig,
    load_and_group_semantic,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Agrupa noticias por similitud semántica usando embeddings congelados."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/noticias_grouped_baseline.csv"),
    )
    parser.add_argument(
        "--embeddings",
        type=Path,
        default=Path("data/embeddings/news_embeddings.npz"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/noticias_grouped_semantic.csv"),
    )
    parser.add_argument(
        "--pairs-output",
        type=Path,
        default=Path("data/processed/grouping_pairs_semantic.csv"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/semantic_grouping"),
    )
    parser.add_argument("--threshold", type=float, default=0.78)
    parser.add_argument("--max-days", type=int, default=3)
    parser.add_argument(
        "--require-same-topic",
        action="store_true",
        help="Exige mismo tema cuando ambos registros tienen tema disponible.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if not args.input.exists():
        print(f"ERROR: No existe {args.input}.")
        return 2
    if not args.embeddings.exists():
        print(
            f"ERROR: No existe {args.embeddings}. "
            "Ejecuta primero scripts/prepare_embeddings.py."
        )
        return 3

    config = SemanticGroupingConfig(
        similarity_threshold=args.threshold,
        max_days_apart=args.max_days,
        require_same_topic_when_available=args.require_same_topic,
    )

    grouped, pairs = load_and_group_semantic(
        args.input,
        args.embeddings,
        config=config,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    grouped.to_csv(args.output, index=False, encoding="utf-8")
    pairs.to_csv(args.pairs_output, index=False, encoding="utf-8")

    clusters_total = int(grouped["cluster_semantic"].nunique())
    multi = int((grouped.groupby("cluster_semantic").size() >= 2).sum())

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "embedding-cosine-connected-components-v0.1",
        "input": str(args.input),
        "embeddings": str(args.embeddings),
        "rows": int(len(grouped)),
        "clusters_total": clusters_total,
        "clusters_with_2_or_more": multi,
        "parameters": {
            "similarity_threshold": config.similarity_threshold,
            "max_days_apart": config.max_days_apart,
            "require_same_topic_when_available": config.require_same_topic_when_available,
        },
        "pairs_compared_after_temporal_filter": int(len(pairs)),
        "pairs_skipped_outside_temporal_window": int(
            pairs.attrs.get("skipped_temporal_pairs", 0)
        ),
        "warning": (
            "El umbral es una propuesta inicial del equipo. "
            "Debe calibrarse contra cluster_humano. "
            "La detección solo se usa como fallback temporal cuando falta publicación."
        ),
    }

    (args.report_dir / "semantic_grouping_report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (args.report_dir / "semantic_grouping_report.md").write_text(
        "\n".join(
            [
                "# Reporte de agrupación semántica",
                "",
                f"- Noticias: **{len(grouped)}**",
                f"- Clusters: **{clusters_total}**",
                f"- Clusters con 2+ noticias: **{multi}**",
                f"- Umbral coseno: **{config.similarity_threshold}**",
                f"- Ventana temporal: **{config.max_days_apart} días**",
                "",
                "## Interpretación",
                "",
                (
                    "Cada cluster representa una hipótesis de que varias noticias "
                    "se refieren al mismo evento. No implica veracidad ni "
                    "corroboración independiente."
                ),
                "",
                "## Validación pendiente",
                "",
                (
                    "El umbral debe compararse contra `cluster_humano` y reportar "
                    "precision, recall y F1 par-a-par."
                ),
            ]
        ),
        encoding="utf-8",
    )

    print("=== TVN Media Copilot | Clustering semántico ===")
    print(f"Noticias: {len(grouped)}")
    print(f"Clusters: {clusters_total}")
    print(f"Clusters con 2+ noticias: {multi}")
    print(f"Salida: {args.output}")
    print(f"Pares: {args.pairs_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
