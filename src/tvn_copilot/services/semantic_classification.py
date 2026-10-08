from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

from .classification import OFFICIAL_TOPICS


@dataclass(frozen=True)
class SemanticClassificationConfig:
    # PROPUESTA DEL EQUIPO: debe validarse con tema_humano si se dispone.
    min_similarity: float = 0.45
    min_margin: float = 0.04
    min_seed_items_per_topic: int = 5


def _normalize_rows(vectors: np.ndarray) -> np.ndarray:
    vectors = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def build_topic_centroids(
    df: pd.DataFrame,
    ids: np.ndarray,
    vectors: np.ndarray,
    topic_column: str = "tema_baseline",
    config: SemanticClassificationConfig | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, int]]:
    config = config or SemanticClassificationConfig()

    id_to_vec = {
        str(id_): vec
        for id_, vec in zip(ids.astype(str), _normalize_rows(vectors))
    }

    centroids: dict[str, np.ndarray] = {}
    seed_counts: dict[str, int] = {}

    for topic in OFFICIAL_TOPICS:
        topic_rows = df[df[topic_column].astype("string") == topic]
        topic_vectors = [
            id_to_vec[str(row["id_noticia"])]
            for _, row in topic_rows.iterrows()
            if str(row["id_noticia"]) in id_to_vec
        ]
        seed_counts[topic] = len(topic_vectors)

        if len(topic_vectors) < config.min_seed_items_per_topic:
            continue

        centroid = np.mean(np.stack(topic_vectors), axis=0)
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm
        centroids[topic] = centroid.astype(np.float32)

    return centroids, seed_counts


def classify_with_topic_centroids(
    df: pd.DataFrame,
    ids: np.ndarray,
    vectors: np.ndarray,
    config: SemanticClassificationConfig | None = None,
) -> tuple[pd.DataFrame, dict]:
    config = config or SemanticClassificationConfig()

    required = {"id_noticia", "tema_baseline"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            "Faltan columnas para clasificación semántica: "
            + ", ".join(sorted(missing))
        )

    norm_vectors = _normalize_rows(vectors)
    id_to_vec = {
        str(id_): vec
        for id_, vec in zip(ids.astype(str), norm_vectors)
    }

    centroids, seed_counts = build_topic_centroids(
        df,
        ids,
        vectors,
        topic_column="tema_baseline",
        config=config,
    )

    out = df.copy()
    semantic_topic: list[str] = []
    semantic_similarity: list[float] = []
    semantic_margin: list[float] = []
    semantic_status: list[str] = []
    final_topic: list[str] = []
    final_source: list[str] = []
    conflicts: list[str] = []

    for _, row in out.iterrows():
        news_id = str(row["id_noticia"])
        baseline_topic = str(row.get("tema_baseline", "sin_clasificar"))
        vec = id_to_vec.get(news_id)

        ranked: list[tuple[str, float]] = []
        if vec is not None:
            ranked = sorted(
                (
                    (topic, float(np.dot(vec, centroid)))
                    for topic, centroid in centroids.items()
                ),
                key=lambda item: item[1],
                reverse=True,
            )

        if ranked:
            best_topic, best_score = ranked[0]
            second_score = ranked[1][1] if len(ranked) > 1 else -1.0
            margin = best_score - second_score
        else:
            best_topic, best_score, margin = "sin_clasificar", 0.0, 0.0

        accepted = (
            best_topic in OFFICIAL_TOPICS
            and best_score >= config.min_similarity
            and margin >= config.min_margin
        )

        semantic_topic.append(best_topic if accepted else "sin_clasificar")
        semantic_similarity.append(round(float(best_score), 6))
        semantic_margin.append(round(float(margin), 6))
        semantic_status.append("clasificado" if accepted else "abstencion")

        if baseline_topic in OFFICIAL_TOPICS:
            final_topic.append(baseline_topic)
            final_source.append("baseline")
            if accepted and best_topic != baseline_topic:
                conflicts.append(f"{baseline_topic} <> {best_topic}")
            else:
                conflicts.append("")
        elif accepted:
            final_topic.append(best_topic)
            final_source.append("semantic_centroid")
            conflicts.append("")
        else:
            final_topic.append("sin_clasificar")
            final_source.append("abstencion")
            conflicts.append("")

    out["tema_semantic"] = semantic_topic
    out["semantic_similarity"] = semantic_similarity
    out["semantic_margin"] = semantic_margin
    out["semantic_estado"] = semantic_status
    out["tema_final"] = final_topic
    out["tema_fuente"] = final_source
    out["tema_conflicto"] = conflicts

    summary = {
        "rows": int(len(out)),
        "baseline_classified": int(out["tema_baseline"].isin(OFFICIAL_TOPICS).sum()),
        "semantic_classified": int(out["tema_semantic"].isin(OFFICIAL_TOPICS).sum()),
        "final_classified": int(out["tema_final"].isin(OFFICIAL_TOPICS).sum()),
        "final_unclassified": int((out["tema_final"] == "sin_clasificar").sum()),
        "final_coverage": round(
            float(out["tema_final"].isin(OFFICIAL_TOPICS).mean()),
            4,
        ),
        "baseline_semantic_conflicts": int(
            (out["tema_conflicto"].astype("string").str.strip() != "").sum()
        ),
        "seed_counts": seed_counts,
        "config": {
            "min_similarity": config.min_similarity,
            "min_margin": config.min_margin,
            "min_seed_items_per_topic": config.min_seed_items_per_topic,
        },
        "warning": (
            "Los centroides se construyen a partir de etiquetas baseline, por lo que "
            "esta etapa es una propuesta de ampliación semántica y debe validarse "
            "contra tema_humano antes de presentarla como métrica final."
        ),
    }
    return out, summary
