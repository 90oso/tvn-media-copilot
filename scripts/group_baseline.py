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

from tvn_copilot.services.grouping import (
    GroupingConfig,
    cluster_summary,
    group_news_baseline,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Agrupación baseline de noticias potencialmente referidas al mismo evento."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/noticias_classified_baseline.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/noticias_grouped_baseline.csv"),
    )
    parser.add_argument(
        "--pairs-output",
        type=Path,
        default=Path("data/processed/grouping_pairs_baseline.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("data/processed/grouping_clusters_baseline.csv"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/grouping"),
    )
    parser.add_argument("--threshold", type=float, default=0.42)
    parser.add_argument("--max-days", type=int, default=3)
    parser.add_argument(
        "--ignore-topic",
        action="store_true",
        help="No exigir compatibilidad temática cuando hay tema disponible.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if not args.input.exists():
        print(f"ERROR: No existe {args.input}. Ejecuta primero el Bloque 2.")
        return 2

    df = pd.read_csv(args.input, dtype="string")
    config = GroupingConfig(
        similarity_threshold=args.threshold,
        max_days_apart=args.max_days,
        require_same_topic_when_available=not args.ignore_topic,
    )

    grouped, pairs = group_news_baseline(df, config=config)
    summary = cluster_summary(grouped)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    grouped.to_csv(args.output, index=False, encoding="utf-8")
    pairs.to_csv(args.pairs_output, index=False, encoding="utf-8")
    summary.to_csv(args.summary_output, index=False, encoding="utf-8")

    clusters_total = int(grouped["cluster_baseline"].nunique())
    multi = int(
        (grouped.groupby("cluster_baseline").size() >= 2).sum()
    )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_version": "tfidf-char-cosine-v0.1",
        "input": str(args.input),
        "rows": int(len(grouped)),
        "clusters_total": clusters_total,
        "clusters_with_2_or_more": multi,
        "parameters": {
            "similarity_threshold": config.similarity_threshold,
            "max_days_apart": config.max_days_apart,
            "require_same_topic_when_available": config.require_same_topic_when_available,
        },
        "method": [
            "TF-IDF de caracteres 3-5 sobre título",
            "similitud coseno",
            "ventana temporal sobre fecha_publicacion o fecha_deteccion como fallback operativo",
            "compatibilidad temática cuando está disponible",
            "componentes conectados",
        ],
        "pairs_compared_after_temporal_filter": int(len(pairs)),
        "pairs_skipped_outside_temporal_window": int(
            pairs.attrs.get("skipped_temporal_pairs", 0)
        ),
        "limitations": [
            "Los umbrales son una propuesta del equipo y deben calibrarse con etiquetas humanas.",
            "El baseline usa solo el título.",
            "Un cluster no prueba verdad ni corroboración independiente.",
            "La procedencia se cuenta aparte para evitar confundir repetición con corroboración.",
        ],
    }

    json_path = args.report_dir / "grouping_baseline_report.json"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md_path = args.report_dir / "grouping_baseline_report.md"
    md_path.write_text(
        "\n".join(
            [
                "# Reporte baseline de agrupación",
                "",
                f"- Versión: `{payload['baseline_version']}`",
                f"- Filas: **{payload['rows']}**",
                f"- Clusters totales: **{clusters_total}**",
                f"- Clusters con 2+ noticias: **{multi}**",
                f"- Umbral: **{config.similarity_threshold}**",
                f"- Ventana temporal: **{config.max_days_apart} días**",
                "",
                "## Método",
                "",
                "- TF-IDF de caracteres 3-5 sobre titular.",
                "- Similitud coseno.",
                "- Filtro temporal usando publicación; detección solo como fallback operativo.",
                "- Compatibilidad temática cuando existe.",
                "- Componentes conectados para formar clusters.",
                "",
                "## Interpretación",
                "",
                (
                    "El cluster indica **posible pertenencia al mismo evento**, "
                    "no veracidad ni corroboración independiente."
                ),
                "",
                (
                    "La cantidad de procedencias independientes se registra por separado "
                    "para no convertir múltiples reproducciones de una misma procedencia "
                    "en evidencia adicional."
                ),
                "",
                "## Próximo paso",
                "",
                (
                    "Comparar este baseline con agrupación por embeddings semánticos "
                    "sobre una muestra etiquetada por humanos."
                ),
            ]
        ),
        encoding="utf-8",
    )

    print("=== TVN Media Copilot | Bloque 3: agrupación baseline ===")
    print(f"Noticias: {len(grouped)}")
    print(f"Clusters: {clusters_total}")
    print(f"Clusters con 2+ noticias: {multi}")
    print(f"Salida: {args.output}")
    print(f"Pares: {args.pairs_output}")
    print(f"Resumen: {args.summary_output}")
    print(f"Reporte: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
