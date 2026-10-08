from __future__ import annotations

from pathlib import Path
import argparse

import pandas as pd


def _stats(df: pd.DataFrame, cluster_col: str) -> dict:
    sizes = df[cluster_col].value_counts()
    return {
        "clusters": int(len(sizes)),
        "singletons": int((sizes == 1).sum()),
        "multi_clusters": int((sizes >= 2).sum()),
        "items_in_multi_clusters": int(sizes[sizes >= 2].sum()),
        "largest_cluster": int(sizes.max()) if len(sizes) else 0,
        "median_cluster_size": float(sizes.median()) if len(sizes) else 0.0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/noticias_grouped_semantic.csv"),
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input, dtype="string")

    baseline = _stats(df, "cluster_baseline")
    semantic = _stats(df, "cluster_semantic")

    print("=== Comparación estructural baseline vs semántico ===")
    print("")
    print("Baseline:")
    for k, v in baseline.items():
        print(f"  {k}: {v}")

    print("")
    print("Semántico:")
    for k, v in semantic.items():
        print(f"  {k}: {v}")

    print("")
    print("Cambios semántico - baseline:")
    for k in (
        "clusters",
        "singletons",
        "multi_clusters",
        "items_in_multi_clusters",
        "largest_cluster",
    ):
        print(f"  {k}: {semantic[k] - baseline[k]:+}")

    print("")
    print(
        "Nota: más o menos clusters NO implica mejor calidad. "
        "La conclusión final depende de cluster_humano."
    )


if __name__ == "__main__":
    main()
