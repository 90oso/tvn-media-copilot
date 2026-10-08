from __future__ import annotations

import pandas as pd

from app.core.settings import Settings
from app.repositories.duckdb_repo import DuckDBRepository
from app.services.topic_analysis import analyze_cluster_from_frames
from app.services.exploration_language import spanish_only, case_languages


def _cluster_column(news: pd.DataFrame) -> str | None:
    if "cluster_semantic" in news.columns:
        return "cluster_semantic"
    if "cluster_baseline" in news.columns:
        return "cluster_baseline"
    return None



def _preview(frame: pd.DataFrame) -> dict:
    """Titular/fecha de portada, distinguiendo publicación de detección.

    No rebautiza `seendate`/fecha de detección como fecha de publicación.
    """
    if frame.empty:
        return {"headline": "Caso sin titular", "source": "No disponible", "date": None, "date_origin": None}
    candidates = frame.copy()
    for col in ("fecha_publicacion", "fecha_deteccion"):
        if col not in candidates:
            candidates[col] = None
    pub = pd.to_datetime(candidates["fecha_publicacion"], errors="coerce", utc=True)
    det = pd.to_datetime(candidates["fecha_deteccion"], errors="coerce", utc=True)
    candidates["_effective_date"] = pub.fillna(det)
    candidates["_publication_date"] = pub
    candidates = candidates.sort_values("_effective_date", ascending=False, na_position="last")
    row = candidates.iloc[0]

    def safe_text(value, fallback: str) -> str:
        return fallback if value is None or pd.isna(value) or not str(value).strip() else str(value)

    date = row["_effective_date"]
    return {
        "headline": safe_text(row.get("titulo"), "Caso sin titular"),
        "source": safe_text(row.get("medio"), safe_text(row.get("origen"), "Fuente no identificada")),
        "date": date.isoformat() if pd.notna(date) else None,
        "date_origin": "publicación" if pd.notna(row["_publication_date"]) else "detección" if pd.notna(date) else None,
    }

def build_agenda(
    repo: DuckDBRepository,
    settings: Settings,
    limit: int = 5,
    language: str = "all",
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
        preview_frame = spanish_only(cluster_news) if language == "es" else cluster_news
        if preview_frame.empty:
            continue
        entry = analyze_cluster_from_frames(
                cid,
                cluster_news.reset_index(drop=True),
                indicators,
                settings,
                snapshot_reference=snapshot_reference,
                review=reviews.get(cid),
        )
        entry.update(_preview(preview_frame))
        entry["case_languages"] = case_languages(cluster_news)
        items.append(entry)

    items.sort(
        key=lambda item: (
            -item["attention"]["score"],
            -item["attention"]["components"]["U"],
            item["case_id"],
        )
    )

    return items[:limit]
