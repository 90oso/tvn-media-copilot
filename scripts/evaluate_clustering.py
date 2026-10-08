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

from tvn_copilot.services.evaluation import (
    compare_clusterings,
    merge_human_labels,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evalúa agrupación baseline y semántica contra cluster_humano."
    )
    parser.add_argument(
        "--predictions",
        type=Path,
        default=Path("data/processed/noticias_grouped_semantic.csv"),
    )
    parser.add_argument(
        "--labels",
        type=Path,
        default=Path("data/etiquetas_humanas.csv"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/evaluation"),
    )
    parser.add_argument(
        "--merged-output",
        type=Path,
        default=Path("data/processed/clustering_evaluation_rows.csv"),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if not args.predictions.exists():
        print(f"ERROR: No existe {args.predictions}.")
        return 2
    if not args.labels.exists():
        print(
            f"ERROR: No existe {args.labels}. "
            "Completa primero las etiquetas humanas."
        )
        return 3

    pred = pd.read_csv(args.predictions, dtype="string")
    labels = pd.read_csv(args.labels, dtype="string")
    merged = merge_human_labels(pred, labels)

    labeled = merged["cluster_humano"].notna() & (
        merged["cluster_humano"].astype("string").str.strip() != ""
    )

    if int(labeled.sum()) < 2:
        print(
            "ERROR: Se necesitan al menos 2 noticias con cluster_humano para evaluar."
        )
        return 4

    result = compare_clusterings(merged)

    args.report_dir.mkdir(parents=True, exist_ok=True)
    args.merged_output.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.merged_output, index=False, encoding="utf-8")

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "labeled_items": int(labeled.sum()),
        "metrics": result,
        "metric_definition": (
            "Evaluación par-a-par: para cada par de noticias etiquetadas, "
            "se compara si humano y sistema consideran que pertenecen al mismo evento."
        ),
        "warning": (
            "No usar esta métrica como resultado final si las etiquetas no fueron "
            "producidas mediante revisión humana."
        ),
    }

    json_path = args.report_dir / "clustering_evaluation.json"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    baseline = result.get("baseline")
    semantic = result.get("semantic")
    delta = result.get("delta_semantic_vs_baseline")

    lines = [
        "# Evaluación de agrupación contra `cluster_humano`",
        "",
        f"- Noticias con etiqueta humana: **{payload['labeled_items']}**",
        "",
        "## Métrica",
        "",
        (
            "Se evalúan pares de noticias: `mismo evento` vs `evento distinto`. "
            "Esto evita exigir que el sistema y el etiquetador utilicen el mismo "
            "nombre de cluster."
        ),
        "",
        "| Método | Precision | Recall | F1 | TP | FP | FN |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    if baseline:
        lines.append(
            f"| Baseline | {baseline['precision']:.4f} | "
            f"{baseline['recall']:.4f} | {baseline['f1']:.4f} | "
            f"{baseline['tp']} | {baseline['fp']} | {baseline['fn']} |"
        )
    if semantic:
        lines.append(
            f"| Semántico | {semantic['precision']:.4f} | "
            f"{semantic['recall']:.4f} | {semantic['f1']:.4f} | "
            f"{semantic['tp']} | {semantic['fp']} | {semantic['fn']} |"
        )

    if delta:
        lines += [
            "",
            "## Cambio semántico vs baseline",
            "",
            f"- Δ precision: **{delta['precision']:+.4f}**",
            f"- Δ recall: **{delta['recall']:+.4f}**",
            f"- Δ F1: **{delta['f1']:+.4f}**",
        ]

    lines += [
        "",
        "> Solo presentar estas cifras como evaluación real si `cluster_humano` "
        "fue construido mediante revisión humana.",
    ]

    md_path = args.report_dir / "clustering_evaluation.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print("=== TVN Media Copilot | Evaluación de clustering ===")
    print(f"Etiquetas humanas válidas: {payload['labeled_items']}")
    if baseline:
        print(
            "Baseline: "
            f"P={baseline['precision']:.4f} "
            f"R={baseline['recall']:.4f} "
            f"F1={baseline['f1']:.4f}"
        )
    if semantic:
        print(
            "Semántico: "
            f"P={semantic['precision']:.4f} "
            f"R={semantic['recall']:.4f} "
            f"F1={semantic['f1']:.4f}"
        )
    if delta:
        print(f"ΔF1 semántico-baseline: {delta['f1']:+.4f}")
    print(f"Reporte: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
