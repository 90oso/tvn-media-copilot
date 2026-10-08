from __future__ import annotations

import argparse
from pathlib import Path
import platform
import sys

# IMPORTANTE EN WINDOWS:
# Algunos builds recientes de PyTorch pueden fallar con WinError 1114 si otras
# librerías nativas se cargan antes. Como el diagnóstico del entorno demuestra
# que `import torch` funciona aislado, lo precargamos antes de pandas/numpy.
if platform.system() == "Windows":
    try:
        import torch  # noqa: F401
    except OSError as exc:
        print("ERROR: PyTorch no pudo precargarse antes de pandas/numpy.")
        print(f"Detalle: {exc}")
        print(
            "Ejecuta: python scripts\\diagnose_torch_import_order.py "
            "y comparte la salida."
        )
        raise SystemExit(4)

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tvn_copilot.services.embeddings import (
    SentenceTransformerProvider,
    save_embeddings,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepara embeddings semánticos congelados para noticias."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/noticias_grouped_baseline.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/embeddings"),
    )
    parser.add_argument(
        "--model",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help=(
            "Modelo propuesto del equipo. Puede cambiarse sin alterar el contrato "
            "de artefactos."
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if not args.input.exists():
        print(f"ERROR: No existe {args.input}. Ejecuta primero group_baseline.py.")
        return 2

    df = pd.read_csv(args.input, dtype="string")
    provider = SentenceTransformerProvider(args.model)

    try:
        artifact = save_embeddings(
            df=df,
            provider=provider,
            output_dir=args.output_dir,
            source_path=args.input,
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 3

    print("=== TVN Media Copilot | Preparación de embeddings ===")
    print(f"Modelo: {artifact.model_name}")
    print(f"Noticias: {artifact.count}")
    print(f"Dimensiones: {artifact.dimensions}")
    print(f"Vectores: {artifact.vectors_path}")
    print(f"Metadata: {artifact.metadata_path}")
    print(
        "Los embeddings quedaron congelados para que la demo posterior pueda "
        "trabajar offline."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
