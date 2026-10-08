from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--evaluation",
        type=Path,
        default=Path("reports/evaluation/clustering_evaluation.json"),
    )
    p.add_argument(
        "--output",
        type=Path,
        default=Path("reports/evaluation/clustering_selection.json"),
    )
    args = p.parse_args()

    if not args.evaluation.exists():
        print(f"ERROR: No existe {args.evaluation}")
        return 2

    payload = json.loads(args.evaluation.read_text(encoding="utf-8"))
    metrics = payload["metrics"]
    baseline = metrics["baseline"]
    semantic = metrics["semantic"]

    selected = "semantic" if semantic["f1"] >= baseline["f1"] else "baseline"

    selection = {
        "selected": selected,
        "criterion": "mayor F1 par-a-par contra cluster_humano",
        "labeled_items": payload.get("labeled_items"),
        "baseline": baseline,
        "semantic": semantic,
        "delta_semantic_vs_baseline": metrics.get("delta_semantic_vs_baseline"),
        "note": (
            "La selección aplica al MVP y a esta muestra humana. "
            "No implica una afirmación universal sobre todo el corpus."
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(selection, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=== Selección de clustering para MVP ===")
    print(f"Seleccionado: {selected}")
    print(f"Baseline F1: {baseline['f1']:.4f}")
    print(f"Semántico F1: {semantic['f1']:.4f}")
    print(f"Salida: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
