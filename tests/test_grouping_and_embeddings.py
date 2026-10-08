from pathlib import Path

import numpy as np
import pandas as pd

from tvn_copilot.services.grouping import GroupingConfig, group_news_baseline
from tvn_copilot.services.embeddings import save_embeddings, load_embeddings


def _fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id_noticia": "A1",
                "titulo": "Canal de Panamá ajusta tránsito de buques por fuertes lluvias",
                "fecha_publicacion": "2026-09-10T10:00:00Z",
                "tema_baseline": "logística/Canal",
                "origen": "Agencia X",
                "medio": "Medio A",
            },
            {
                "id_noticia": "A2",
                "titulo": "Fuertes lluvias obligan al Canal de Panamá a ajustar el tránsito de buques",
                "fecha_publicacion": "2026-09-10T11:00:00Z",
                "tema_baseline": "logística/Canal",
                "origen": "Agencia X",
                "medio": "Medio B",
            },
            {
                "id_noticia": "A3",
                "titulo": "Canal ajusta tránsito de buques debido a fuertes lluvias",
                "fecha_publicacion": "2026-09-10T12:00:00Z",
                "tema_baseline": "logística/Canal",
                "origen": "Medio C",
                "medio": "Medio C",
            },
            {
                "id_noticia": "B1",
                "titulo": "Inflación anual muestra variación en Panamá",
                "fecha_publicacion": "2026-09-10T13:00:00Z",
                "tema_baseline": "economía",
                "origen": "Medio D",
                "medio": "Medio D",
            },
        ]
    )


def test_t02_three_records_same_event_form_one_cluster():
    grouped, pairs = group_news_baseline(
        _fixture(),
        config=GroupingConfig(similarity_threshold=0.35, max_days_apart=2),
    )

    event_clusters = grouped.loc[
        grouped["id_noticia"].isin(["A1", "A2", "A3"]),
        "cluster_baseline",
    ].unique()

    assert len(event_clusters) == 1
    cluster = event_clusters[0]
    rows = grouped[grouped["cluster_baseline"] == cluster]
    assert len(rows) == 3


def test_replicated_agency_does_not_count_as_three_independent_sources():
    grouped, _ = group_news_baseline(
        _fixture(),
        config=GroupingConfig(similarity_threshold=0.35, max_days_apart=2),
    )

    a1 = grouped[grouped["id_noticia"] == "A1"].iloc[0]
    # A1 y A2 comparten Agencia X; A3 tiene otra procedencia.
    assert int(a1["procedencias_independientes_baseline"]) == 2


class FakeEmbeddingProvider:
    model_name = "fake-test-model"

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.asarray(
            [[float(i), float(i + 1), 1.0] for i, _ in enumerate(texts)],
            dtype=np.float32,
        )


def test_embedding_artifact_is_reproducible_and_mapped(tmp_path: Path):
    df = _fixture().iloc[:3].copy()
    artifact = save_embeddings(
        df=df,
        provider=FakeEmbeddingProvider(),
        output_dir=tmp_path,
    )

    ids, vectors = load_embeddings(artifact.vectors_path)
    assert ids.tolist() == ["A1", "A2", "A3"]
    assert vectors.shape == (3, 3)
    assert artifact.dimensions == 3


def test_detection_date_prevents_cross_month_baseline_grouping():
    df = pd.DataFrame(
        [
            {
                "id_noticia": "G1",
                "titulo": "Canal de Panamá ajusta tránsito de buques",
                "fecha_publicacion": None,
                "fecha_deteccion": "2026-06-01T10:00:00Z",
                "tema_baseline": "logística/Canal",
                "origen": "A",
            },
            {
                "id_noticia": "G2",
                "titulo": "Canal de Panamá ajusta tránsito de buques",
                "fecha_publicacion": None,
                "fecha_deteccion": "2026-08-01T10:00:00Z",
                "tema_baseline": "logística/Canal",
                "origen": "B",
            },
        ]
    )
    grouped, pairs = group_news_baseline(
        df,
        config=GroupingConfig(similarity_threshold=0.1, max_days_apart=3),
    )
    assert grouped["cluster_baseline"].nunique() == 2
    assert len(pairs) == 0
