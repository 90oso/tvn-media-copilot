from pathlib import Path

import numpy as np
import pandas as pd

from tvn_copilot.services.semantic_grouping import (
    SemanticGroupingConfig,
    group_news_semantic,
)
from tvn_copilot.services.evaluation import (
    pairwise_cluster_metrics,
    compare_clusterings,
    merge_human_labels,
)


def _predictions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id_noticia": "S1",
                "titulo": "Canal ajusta tránsito por lluvias",
                "fecha_publicacion": "2026-09-10T10:00:00Z",
                "origen": "Agencia X",
                "cluster_baseline": "B1",
            },
            {
                "id_noticia": "S2",
                "titulo": "Lluvias obligan a modificar el paso de barcos",
                "fecha_publicacion": "2026-09-10T11:00:00Z",
                "origen": "Agencia X",
                "cluster_baseline": "B2",
            },
            {
                "id_noticia": "S3",
                "titulo": "Canal cambia tránsito marítimo por clima",
                "fecha_publicacion": "2026-09-10T12:00:00Z",
                "origen": "Medio C",
                "cluster_baseline": "B1",
            },
            {
                "id_noticia": "S4",
                "titulo": "Inflación anual muestra variación",
                "fecha_publicacion": "2026-09-10T13:00:00Z",
                "origen": "Medio D",
                "cluster_baseline": "B4",
            },
        ]
    )


def test_semantic_clustering_groups_paraphrases():
    df = _predictions()
    ids = np.array(["S1", "S2", "S3", "S4"])
    vectors = np.array(
        [
            [1.00, 0.00],
            [0.99, 0.03],
            [0.97, 0.05],
            [0.00, 1.00],
        ],
        dtype=np.float32,
    )

    grouped, pairs = group_news_semantic(
        df,
        ids,
        vectors,
        SemanticGroupingConfig(
            similarity_threshold=0.95,
            max_days_apart=2,
        ),
    )

    same = grouped[grouped["id_noticia"].isin(["S1", "S2", "S3"])]
    assert same["cluster_semantic"].nunique() == 1
    assert grouped[grouped["id_noticia"] == "S4"]["cluster_semantic"].iloc[0] != same["cluster_semantic"].iloc[0]


def test_pairwise_metrics_do_not_require_same_cluster_names():
    df = pd.DataFrame(
        {
            "id_noticia": ["A", "B", "C"],
            "cluster_humano": ["H1", "H1", "H2"],
            "cluster_semantic": ["XYZ", "XYZ", "OTHER"],
        }
    )
    m = pairwise_cluster_metrics(df)
    assert m.precision == 1.0
    assert m.recall == 1.0
    assert m.f1 == 1.0


def test_semantic_can_improve_over_baseline_in_fixture():
    pred = _predictions()
    pred["cluster_semantic"] = ["SAME", "SAME", "SAME", "OTHER"]

    labels = pd.DataFrame(
        {
            "id_noticia": ["S1", "S2", "S3", "S4"],
            "cluster_humano": ["H1", "H1", "H1", "H2"],
            "tema_humano": ["logística/Canal", "logística/Canal", "logística/Canal", "economía"],
        }
    )

    merged = merge_human_labels(pred, labels)
    result = compare_clusterings(merged)

    assert result["semantic"]["f1"] == 1.0
    assert result["baseline"]["f1"] < result["semantic"]["f1"]
    assert result["delta_semantic_vs_baseline"]["f1"] > 0


def test_detection_date_prevents_cross_month_semantic_grouping():
    df = pd.DataFrame(
        [
            {
                "id_noticia": "G1",
                "titulo": "Canal cambia tránsito",
                "fecha_publicacion": None,
                "fecha_deteccion": "2026-06-01T10:00:00Z",
                "origen": "A",
            },
            {
                "id_noticia": "G2",
                "titulo": "Canal cambia tránsito",
                "fecha_publicacion": None,
                "fecha_deteccion": "2026-08-01T10:00:00Z",
                "origen": "B",
            },
        ]
    )
    ids = np.array(["G1", "G2"])
    vectors = np.array([[1.0, 0.0], [1.0, 0.0]], dtype=np.float32)

    grouped, pairs = group_news_semantic(
        df,
        ids,
        vectors,
        SemanticGroupingConfig(
            similarity_threshold=0.1,
            max_days_apart=3,
        ),
    )

    assert grouped["cluster_semantic"].nunique() == 2
    assert len(pairs) == 0
