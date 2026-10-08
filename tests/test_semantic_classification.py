import numpy as np
import pandas as pd

from tvn_copilot.services.semantic_classification import (
    SemanticClassificationConfig,
    classify_with_topic_centroids,
)


def test_semantic_fills_only_unclassified_rows():
    rows = []
    ids = []
    vectors = []

    # 5 semillas economía
    for i in range(5):
        ids.append(f"E{i}")
        rows.append(
            {
                "id_noticia": f"E{i}",
                "tema_baseline": "economía",
                "titulo": "economía",
            }
        )
        vectors.append([1.0, 0.0])

    # 5 semillas turismo
    for i in range(5):
        ids.append(f"T{i}")
        rows.append(
            {
                "id_noticia": f"T{i}",
                "tema_baseline": "turismo",
                "titulo": "turismo",
            }
        )
        vectors.append([0.0, 1.0])

    ids.append("U1")
    rows.append(
        {
            "id_noticia": "U1",
            "tema_baseline": "sin_clasificar",
            "titulo": "sin etiqueta",
        }
    )
    vectors.append([0.99, 0.01])

    df = pd.DataFrame(rows)

    out, summary = classify_with_topic_centroids(
        df,
        np.asarray(ids),
        np.asarray(vectors, dtype=np.float32),
        SemanticClassificationConfig(
            min_similarity=0.8,
            min_margin=0.1,
            min_seed_items_per_topic=5,
        ),
    )

    row = out[out["id_noticia"] == "U1"].iloc[0]
    assert row["tema_final"] == "economía"
    assert row["tema_fuente"] == "semantic_centroid"
    assert summary["final_classified"] == 11


def test_baseline_is_not_overwritten_by_semantic():
    rows = []
    ids = []
    vectors = []

    for i in range(5):
        ids.append(f"E{i}")
        rows.append({"id_noticia": f"E{i}", "tema_baseline": "economía"})
        vectors.append([1.0, 0.0])

    for i in range(5):
        ids.append(f"T{i}")
        rows.append({"id_noticia": f"T{i}", "tema_baseline": "turismo"})
        vectors.append([0.0, 1.0])

    # Baseline dice economía pero embedding se parece a turismo.
    ids.append("X")
    rows.append({"id_noticia": "X", "tema_baseline": "economía"})
    vectors.append([0.0, 1.0])

    out, _ = classify_with_topic_centroids(
        pd.DataFrame(rows),
        np.asarray(ids),
        np.asarray(vectors, dtype=np.float32),
        SemanticClassificationConfig(
            min_similarity=0.8,
            min_margin=0.1,
            min_seed_items_per_topic=5,
        ),
    )

    row = out[out["id_noticia"] == "X"].iloc[0]
    assert row["tema_final"] == "economía"
    assert row["tema_fuente"] == "baseline"
    assert row["tema_conflicto"] != ""
