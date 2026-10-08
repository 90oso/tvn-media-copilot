from __future__ import annotations

import pandas as pd

from app.core.settings import Settings
from app.repositories.duckdb_repo import DuckDBRepository
from app.services.topic_analysis import analyze_cluster_from_frames


def _cluster_column(news: pd.DataFrame) -> str | None:
    if "cluster_semantic" in news.columns:
        return "cluster_semantic"
    if "cluster_baseline" in news.columns:
        return "cluster_baseline"
    return None


def build_agenda(
    repo: DuckDBRepository,
    settings: Settings,
    limit: int = 5,
) -> list[dict]:
    """Construye la agenda en batch.

    v0.9.1 elimina el patrón N+1 de la versión anterior:
    antes se abría/consultaba la base varias veces por cada cluster.
    Ahora noticias, indicadores, referencia temporal y revisiones se cargan
    una sola vez por petición.
    """
    news = repo.get_all_valid_news()
    if news.empty:
        return []

    cluster_col = _cluster_column(news)
    if not cluster_col:
        return []

    indicators = repo.get_panama_indicators()
    snapshot_reference = repo.get_snapshot_reference()
    reviews = repo.get_all_reviews()

    items: list[dict] = []

    # sort=False evita ordenamientos intermedios; el ranking final se ordena
    # explícitamente después.
    for cluster_id, cluster_news in news.groupby(
        cluster_col,
        sort=False,
        dropna=True,
    ):
        cid = str(cluster_id)
        items.append(
            analyze_cluster_from_frames(
                cid,
                cluster_news.reset_index(drop=True),
                indicators,
                settings,
                snapshot_reference=snapshot_reference,
                review=reviews.get(cid),
            )
        )

    items.sort(
        key=lambda item: (
            -item["attention"]["score"],
            -item["attention"]["components"]["U"],
            item["case_id"],
        )
    )

    return items[:limit]
