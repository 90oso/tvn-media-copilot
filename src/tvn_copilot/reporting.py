from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

from .validator import ValidationResult


def _codes_table(title: str, counts: dict[str, int]) -> list[str]:
    lines = ["", f"### {title}", ""]
    if not counts:
        return lines + ["Ninguno.", ""]
    lines += ["| Código | Filas |", "|---|---:|"]
    for code, count in counts.items():
        lines.append(f"| `{code}` | {count} |")
    lines.append("")
    return lines


def _dataset_md(result: ValidationResult) -> str:
    s = result.summary
    lines = [
        f"## {result.dataset_name}",
        "",
        f"- Archivo: `{result.source_path}`",
        f"- Filas cargadas: **{s['rows_loaded']}**",
        f"- Filas OK: **{s['rows_ok']}**",
        f"- Filas con warning: **{s.get('rows_with_warnings', 0)}**",
        f"- Filas con error: **{s.get('rows_with_errors', s.get('rows_with_issues', 0))}**",
        f"- Filas utilizables: **{s.get('rows_usable', s['rows_ok'])}**",
        f"- Columnas faltantes: **{', '.join(s['schema']['missing_columns']) or 'ninguna'}**",
        f"- Columnas extra: **{', '.join(s['schema']['extra_columns']) or 'ninguna'}**",
        "",
        "### Nulos por columna",
        "",
        "| Campo | Nulos |",
        "|---|---:|",
    ]
    for col, count in s["nulls_by_column"].items():
        lines.append(f"| {col} | {count} |")

    lines += _codes_table("Errores por código", s.get("errors_by_code", {}))
    lines += _codes_table("Warnings por código", s.get("warnings_by_code", {}))

    if s.get("by_origin"):
        lines += [
            "### Calidad por origen",
            "",
            "| Origen | Filas | OK | Warning | Error |",
            "|---|---:|---:|---:|---:|",
        ]
        for origin, values in s["by_origin"].items():
            lines.append(
                f"| {origin} | {values['rows']} | {values['ok']} | "
                f"{values['warning']} | {values['error']} |"
            )
        lines.append("")

    lines += ["", f"> {s['note']}", ""]
    return "\n".join(lines)


def write_outputs(
    news: ValidationResult,
    indicators: ValidationResult,
    processed_dir: Path,
    report_dir: Path,
    rules_version: str,
) -> dict:
    processed_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    news_out = processed_dir / "noticias_validated.csv"
    indicators_out = processed_dir / "indicadores_validated.csv"

    news.dataframe.to_csv(news_out, index=False, encoding="utf-8")
    indicators.dataframe.to_csv(indicators_out, index=False, encoding="utf-8")

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "rules_version": rules_version,
        "datasets": {
            "noticias": news.summary,
            "indicadores": indicators.summary,
        },
        "outputs": {
            "noticias_validated": str(news_out),
            "indicadores_validated": str(indicators_out),
        },
    }

    json_path = report_dir / "data_quality_report.json"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md = [
        "# Reporte de calidad de datos",
        "",
        f"- Generado UTC: `{report['generated_at_utc']}`",
        f"- Versión de reglas: `{rules_version}`",
        "",
        "Este reporte no corrige ni completa silenciosamente los datos.",
        "Los warnings conservan información faltante conocida sin invalidar la fila.",
        "Los errores sí requieren revisión.",
        "",
        _dataset_md(news),
        _dataset_md(indicators),
    ]
    md_path = report_dir / "data_quality_report.md"
    md_path.write_text("\n".join(md), encoding="utf-8")

    return {
        "json": str(json_path),
        "markdown": str(md_path),
        "news_csv": str(news_out),
        "indicators_csv": str(indicators_out),
        "report": report,
    }
