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

from tvn_copilot.config import get_settings
from tvn_copilot.services.classification import (
    OFFICIAL_TOPICS,
    classify_dataframe_baseline,
    evaluate_against_reference,
)
from tvn_copilot.validator import validate_news


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Clasificación temática baseline por reglas/palabras clave."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help=(
            "CSV de noticias. Si se omite, usa "
            "data/processed/noticias_validated.csv si existe; "
            "de lo contrario valida NEWS_CSV."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/noticias_classified_baseline.csv"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/baseline"),
    )
    return parser


def _load_input(input_path: Path | None) -> tuple[pd.DataFrame, Path, str]:
    settings = get_settings()
    validated = Path("data/processed/noticias_validated.csv")

    if input_path is not None:
        if not input_path.exists():
            raise FileNotFoundError(f"No existe el archivo: {input_path}")
        return pd.read_csv(input_path, dtype="string"), input_path, "provided"

    if validated.exists():
        return pd.read_csv(validated, dtype="string"), validated, "validated"

    result = validate_news(settings.news_csv)
    validated.parent.mkdir(parents=True, exist_ok=True)
    result.dataframe.to_csv(validated, index=False, encoding="utf-8")
    return result.dataframe, validated, "validated_now"


def _write_report(
    df: pd.DataFrame,
    source: Path,
    output: Path,
    report_dir: Path,
) -> dict:
    report_dir.mkdir(parents=True, exist_ok=True)

    counts = (
        df["tema_baseline"]
        .value_counts(dropna=False)
        .to_dict()
    )
    status_counts = (
        df["baseline_estado"]
        .value_counts(dropna=False)
        .to_dict()
    )
    metrics = evaluate_against_reference(df)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_version": "keyword-rules-v0.1",
        "purpose": (
            "Baseline simple para comparación posterior con una capacidad NLP/ML. "
            "No constituye por sí solo el uso sustantivo de IA."
        ),
        "input": str(source),
        "output": str(output),
        "official_topics": list(OFFICIAL_TOPICS),
        "rows": int(len(df)),
        "prediction_counts": {str(k): int(v) for k, v in counts.items()},
        "status_counts": {str(k): int(v) for k, v in status_counts.items()},
        "evaluation": metrics,
        "limitations": [
            "Clasifica solo con el título disponible en el contrato actual.",
            "No entiende contexto ni polisemia.",
            "Puede abstenerse ante ausencia de palabras clave o empate.",
            "Las palabras clave son una propuesta técnica del equipo, no un requisito del reto.",
            "`sin_clasificar` es un estado técnico y no una séptima categoría.",
        ],
    }

    json_path = report_dir / "baseline_classification_report.json"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Reporte baseline de clasificación temática",
        "",
        f"- Generado UTC: `{payload['generated_at_utc']}`",
        "- Versión: `keyword-rules-v0.1`",
        f"- Entrada: `{source}`",
        f"- Filas: **{len(df)}**",
        "",
        "## Propósito",
        "",
        (
            "Este baseline simple se conserva para compararlo posteriormente "
            "contra una capacidad NLP/ML. **No se presenta como IA**."
        ),
        "",
        "## Distribución",
        "",
        "| Tema baseline | Registros |",
        "|---|---:|",
    ]
    for topic, count in counts.items():
        lines.append(f"| {topic} | {count} |")

    lines += [
        "",
        "## Estados",
        "",
        "| Estado | Registros |",
        "|---|---:|",
    ]
    for status, count in status_counts.items():
        lines.append(f"| {status} | {count} |")

    lines += ["", "## Evaluación contra `tema`", ""]
    if metrics.get("available"):
        lines += [
            f"- Etiquetas disponibles: **{metrics['n_labeled']}**",
            f"- Cobertura de clasificación: **{metrics['classification_coverage']:.2%}**",
            f"- Macro-F1: **{metrics['macro_f1']:.4f}**",
            f"- Macro-precision: **{metrics['macro_precision']:.4f}**",
            f"- Macro-recall: **{metrics['macro_recall']:.4f}**",
            "",
            f"> {metrics['warning']}",
        ]
    else:
        lines += [
            f"- Métricas no disponibles: {metrics.get('reason', 'sin etiquetas')}",
            "",
            (
                "Las métricas finales deben calcularse contra etiquetas creadas "
                "por revisión humana."
            ),
        ]

    lines += [
        "",
        "## Limitaciones",
        "",
        "- Solo usa el título.",
        "- No interpreta contexto o polisemia.",
        "- Puede abstenerse si no encuentra señal suficiente.",
        "- Puede abstenerse si dos o más temas empatan.",
        "- Las palabras clave son una propuesta del equipo.",
        "",
        "## Siguiente comparación",
        "",
        (
            "Implementar una clasificación o similitud semántica con NLP/ML y "
            "comparar cobertura, macro-F1/precision/recall y errores cualitativos."
        ),
    ]

    md_path = report_dir / "baseline_classification_report.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "json": json_path,
        "markdown": md_path,
        "payload": payload,
    }


def main() -> int:
    args = build_parser().parse_args()

    try:
        df, source, mode = _load_input(args.input)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 2

    classified = classify_dataframe_baseline(df)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    classified.to_csv(args.output, index=False, encoding="utf-8")

    report = _write_report(
        classified,
        source,
        args.output,
        args.report_dir,
    )

    classified_count = int(
        classified["tema_baseline"].isin(OFFICIAL_TOPICS).sum()
    )
    unclassified_count = int(len(classified) - classified_count)

    print("=== TVN Media Copilot | Bloque 2: baseline temático ===")
    print(f"Entrada: {source} ({mode})")
    print(f"Filas: {len(classified)}")
    print(f"Clasificadas en los 6 temas: {classified_count}")
    print(f"Sin clasificación/empate: {unclassified_count}")
    print(f"Salida: {args.output}")
    print(f"Reporte MD: {report['markdown']}")
    print(f"Reporte JSON: {report['json']}")

    metrics = report["payload"]["evaluation"]
    if metrics.get("available"):
        print(
            "Métrica de desarrollo contra `tema`: "
            f"macro-F1={metrics['macro_f1']:.4f} "
            f"(n={metrics['n_labeled']})"
        )
        print(
            "ADVERTENCIA: solo tratarla como métrica final si `tema` fue "
            "etiquetado por revisión humana."
        )
    else:
        print("No hay etiquetas humanas válidas suficientes para evaluar.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
