from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tvn_copilot.services.temporal import effective_event_dates


def build_parser():
    p = argparse.ArgumentParser(
        description="Audita cobertura y composición del corpus real sin modificar datos."
    )
    p.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/noticias_validated.csv"),
    )
    p.add_argument(
        "--report",
        type=Path,
        default=Path("reports/data_quality/corpus_audit.md"),
    )
    return p


def main() -> int:
    args = build_parser().parse_args()
    if not args.input.exists():
        print(f"ERROR: No existe {args.input}")
        return 2

    df = pd.read_csv(args.input, dtype="string")
    dates, date_sources = effective_event_dates(df)

    total = len(df)
    status_counts = (
        df["_validation_status"].value_counts(dropna=False).to_dict()
        if "_validation_status" in df.columns else {}
    )
    origin_counts = (
        df["origen"].fillna("<NA>").value_counts().to_dict()
        if "origen" in df.columns else {}
    )
    language_counts = (
        df["idioma"].fillna("<NA>").value_counts().to_dict()
        if "idioma" in df.columns else {}
    )

    tvn_count = int((df.get("origen", pd.Series("", index=df.index)) == "TVN RSS").sum())
    gdelt_like = total - tvn_count

    effective_nonnull = dates.dropna()
    coverage_min = effective_nonnull.min() if not effective_nonnull.empty else None
    coverage_max = effective_nonnull.max() if not effective_nonnull.empty else None

    months = (
        dates.dt.to_period("M").astype("string").value_counts().sort_index().to_dict()
        if dates.notna().any() else {}
    )

    pub_missing = (
        int(df["fecha_publicacion"].isna().sum())
        if "fecha_publicacion" in df.columns else total
    )
    det_missing = (
        int(df["fecha_deteccion"].isna().sum())
        if "fecha_deteccion" in df.columns else total
    )

    lines = [
        "# Auditoría del corpus real",
        "",
        f"- Registros totales: **{total}**",
        f"- TVN RSS: **{tvn_count}**",
        f"- Otras procedencias/GDELT: **{gdelt_like}**",
        f"- `fecha_publicacion` nula: **{pub_missing}**",
        f"- `fecha_deteccion` nula: **{det_missing}**",
        f"- Cobertura efectiva mínima: **{coverage_min}**",
        f"- Cobertura efectiva máxima: **{coverage_max}**",
        "",
        "> Fecha efectiva = publicación si existe; detección solo como fallback operativo.",
        "",
        "## Estado de validación",
        "",
        "| Estado | Registros |",
        "|---|---:|",
    ]
    for key, value in status_counts.items():
        lines.append(f"| {key} | {value} |")

    lines += [
        "",
        "## Meses cubiertos",
        "",
        "| Mes | Registros |",
        "|---|---:|",
    ]
    for key, value in months.items():
        lines.append(f"| {key} | {value} |")

    lines += [
        "",
        "## Idiomas",
        "",
        "| Idioma | Registros |",
        "|---|---:|",
    ]
    for key, value in sorted(language_counts.items(), key=lambda x: -x[1])[:20]:
        lines.append(f"| {key} | {value} |")

    lines += [
        "",
        "## Principales procedencias",
        "",
        "| Procedencia | Registros |",
        "|---|---:|",
    ]
    for key, value in sorted(origin_counts.items(), key=lambda x: -x[1])[:40]:
        lines.append(f"| {key} | {value} |")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")

    print("=== Auditoría del corpus real ===")
    print(f"Total: {total}")
    print(f"TVN RSS: {tvn_count}")
    print(f"Otras procedencias/GDELT: {gdelt_like}")
    print(f"Publicación nula: {pub_missing}")
    print(f"Detección nula: {det_missing}")
    print(f"Cobertura efectiva: {coverage_min} -> {coverage_max}")
    print(f"Meses: {len(months)}")
    print(f"Reporte: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
