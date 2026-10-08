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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Genera una muestra de revisión humana para comparar baseline y "
            "clustering semántico."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/noticias_grouped_semantic.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/etiquetas_humanas.csv"),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=120,
        help=(
            "Tamaño operativo recomendado para revisión rápida. "
            "Es una propuesta del equipo, no un requisito del reto. "
            "Usa 0 para incluir todo el corpus."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20261007,
    )
    parser.add_argument(
        "--mode",
        choices=("disagreement", "random", "all"),
        default="disagreement",
        help=(
            "disagreement prioriza casos donde baseline y semántico difieren; "
            "random toma una muestra aleatoria; all incluye todo."
        ),
    )
    return parser


def _same_partition_signal(df: pd.DataFrame) -> pd.Series:
    """Marca filas en clusters donde baseline/semántico muestran estructura distinta."""
    if "cluster_baseline" not in df.columns or "cluster_semantic" not in df.columns:
        return pd.Series(False, index=df.index)

    baseline_size = (
        df.groupby("cluster_baseline")["id_noticia"]
        .transform("size")
        .fillna(1)
        .astype(int)
    )
    semantic_size = (
        df.groupby("cluster_semantic")["id_noticia"]
        .transform("size")
        .fillna(1)
        .astype(int)
    )

    # Casos informativos:
    # - uno de los métodos agrupa y el otro deja singleton;
    # - tamaños diferentes;
    # - asociaciones cruzadas distintas.
    baseline_multi = baseline_size > 1
    semantic_multi = semantic_size > 1

    return (
        (baseline_multi != semantic_multi)
        | (baseline_size != semantic_size)
        | (
            df["cluster_baseline"].astype("string")
            != df["cluster_semantic"].astype("string")
        )
    )


def _balanced_sample(df: pd.DataFrame, limit: int, seed: int) -> pd.DataFrame:
    if limit <= 0 or limit >= len(df):
        return df.copy()

    disagreement = _same_partition_signal(df)
    informative = df.loc[disagreement].copy()
    rest = df.loc[~disagreement].copy()

    # Priorizamos desacuerdos, pero reservamos ~25% para controles donde ambos
    # métodos no muestran una diferencia obvia.
    target_control = max(1, int(round(limit * 0.25)))
    target_informative = limit - target_control

    take_info = min(target_informative, len(informative))
    take_control = min(target_control, len(rest))

    parts = []
    if take_info:
        parts.append(
            informative.sample(n=take_info, random_state=seed)
        )
    if take_control:
        parts.append(
            rest.sample(n=take_control, random_state=seed + 1)
        )

    current = sum(len(p) for p in parts)
    if current < limit:
        selected_ids = set()
        for part in parts:
            selected_ids.update(part.index.tolist())
        remaining = df.loc[~df.index.isin(selected_ids)]
        extra = min(limit - current, len(remaining))
        if extra:
            parts.append(
                remaining.sample(n=extra, random_state=seed + 2)
            )

    return pd.concat(parts, axis=0)


def main() -> int:
    args = build_parser().parse_args()

    if not args.input.exists():
        print(f"ERROR: No existe {args.input}.")
        print("Ejecuta primero scripts\\cluster_semantic.py.")
        return 2

    df = pd.read_csv(args.input, dtype="string")

    required = {"id_noticia", "titulo", "cluster_semantic"}
    missing = required - set(df.columns)
    if missing:
        print(
            "ERROR: faltan columnas necesarias: "
            + ", ".join(sorted(missing))
        )
        return 3

    effective_date, date_source = effective_event_dates(df)
    work = df.copy()
    work["fecha_efectiva_revision"] = effective_date.astype("string")
    work["fuente_fecha_revision"] = date_source

    if args.mode == "all" or args.limit == 0:
        sample = work.copy()
    elif args.mode == "random":
        n = min(args.limit, len(work))
        sample = work.sample(n=n, random_state=args.seed)
    else:
        sample = _balanced_sample(work, args.limit, args.seed)

    context_cols = [
        c for c in (
            "id_noticia",
            "titulo",
            "medio",
            "origen",
            "idioma",
            "fecha_publicacion",
            "fecha_deteccion",
            "fecha_efectiva_revision",
            "fuente_fecha_revision",
            "tema_baseline",
            "cluster_baseline",
            "cluster_size_baseline",
            "cluster_semantic",
            "cluster_size_semantic",
            "procedencias_independientes_baseline",
            "procedencias_independientes_semantic",
            "_validation_status",
        )
        if c in sample.columns
    ]

    sample = sample[context_cols].copy()

    # Orden visual: primero cluster semántico, luego fecha, luego ID.
    sort_cols = [
        c for c in (
            "cluster_semantic",
            "fecha_efectiva_revision",
            "id_noticia",
        )
        if c in sample.columns
    ]
    if sort_cols:
        sample = sample.sort_values(sort_cols)

    # Columnas humanas. Nunca se prellenan.
    sample["mismo_evento_revision"] = ""
    sample["tema_humano"] = ""
    sample["cluster_humano"] = ""
    sample["etiquetador"] = ""
    sample["nota"] = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(args.output, index=False, encoding="utf-8-sig")

    print("=== Plantilla de etiquetado humano v0.6.5 ===")
    print(f"Corpus: {len(df)}")
    print(f"Modo: {args.mode}")
    print(f"Filas para revisar: {len(sample)}")
    print(f"Salida: {args.output}")
    print("")
    print("Cómo etiquetar:")
    print(
        "- `cluster_humano`: mismo ID para noticias que describen el MISMO evento."
    )
    print(
        "- Eventos diferentes deben tener IDs diferentes aunque compartan tema."
    )
    print(
        "- `tema_humano` es opcional para la evaluación de clustering."
    )
    print(
        "- No copies automáticamente cluster_baseline ni cluster_semantic."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
