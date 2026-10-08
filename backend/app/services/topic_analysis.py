from __future__ import annotations

import pandas as pd

from app.core.settings import Settings
from app.repositories.duckdb_repo import DuckDBRepository
from app.services.evidence_engine import build_evidence_package
from app.services.ranking import propose_components, explain_components


def _workflow(
    evidence_state: str,
    contradiction_count: int = 0,
) -> dict:
    if evidence_state == "suficiente para el borrador":
        action = (
            "Puede generarse un borrador que exponga las versiones "
            "contradictorias; deben verificarse antes de aprobación humana."
            if contradiction_count
            else (
                "Puede generarse un borrador asistido, "
                "sujeto a revisión humana."
            )
        )
        return {
            "state": "en revisión",
            "recommended_action": action,
            "draft_enabled": True,
            "publication_enabled": False,
        }

    return {
        "state": "requiere evidencia",
        "recommended_action": (
            "Corroborar con más procedencias/evidencia "
            "antes de generar borrador."
        ),
        "draft_enabled": False,
        "publication_enabled": False,
    }


def analyze_cluster_from_frames(
    cluster_id: str,
    news: pd.DataFrame,
    indicators: pd.DataFrame,
    settings: Settings,
    *,
    snapshot_reference=None,
    review: dict | None = None,
) -> dict:
    """Analiza un cluster usando frames ya cargados.

    Esta función permite que `/agenda` cargue noticias/indicadores una sola vez
    y procese todos los clusters en memoria.
    """
    package = build_evidence_package(
        cluster_id,
        news,
        indicators,
        settings.evidence_rules_version,
    )

    components = propose_components(
        news,
        package,
        snapshot_reference,
    )
    explanations = explain_components(
        news,
        package,
        components,
    )

    workflow = _workflow(
        package.evidence_state,
        len(package.contradictions),
    )

    if review:
        workflow = {
            **workflow,
            "state": review["state"],
            "human_review": review,
        }

    return {
        "case_id": cluster_id,
        "news_count": int(len(news)),
        "evidence_package": package.model_dump(),
        "workflow": workflow,
        "attention": {
            "score": components.total,
            "band": components.band,
            "components": {
                "R": components.relevance,
                "I": components.impact,
                "U": components.urgency,
                "N": components.novelty,
                "E": components.evidence,
            },
            "formula": "P = 30R + 25I + 20U + 15N + 10E",
            "rules_version": settings.ranking_rules_version,
            "explanations": explanations,
            "warning": (
                "El puntaje ordena atención; no representa probabilidad de "
                "verdad ni habilita publicación. El estado de evidencia "
                "se evalúa por separado."
            ),
        },
    }


def analyze_cluster(
    cluster_id: str,
    repo: DuckDBRepository,
    settings: Settings,
) -> dict:
    """Ruta de detalle: conserva el comportamiento anterior."""
    news = repo.get_cluster_news(cluster_id)
    indicators = repo.get_panama_indicators()
    snapshot_reference = repo.get_snapshot_reference()
    review = repo.get_review(cluster_id)

    return analyze_cluster_from_frames(
        cluster_id,
        news,
        indicators,
        settings,
        snapshot_reference=snapshot_reference,
        review=review,
    )
