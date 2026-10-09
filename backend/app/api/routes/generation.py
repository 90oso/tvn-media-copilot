from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Header

from app.core.settings import get_settings
from app.core.editor_auth import require_editor_access
from app.repositories.duckdb_repo import DuckDBRepository
from app.repositories.editorial_store import EditorialStore
from app.services.editorial_generation import _fingerprint
from app.schemas.evidence import EvidencePackage
from app.services.editorial_generation import (
    generate_editorial,
    load_cache,
    save_cache,
)
from app.services.llm_provider import build_llm_provider
from app.services.topic_analysis import analyze_cluster

router = APIRouter(prefix="/generate", tags=["generation"])


@router.get("/{cluster_id}/saved")
def saved_drafts(cluster_id: str):
    """Solo borradores validados para la huella ACTUAL de las evidencias."""
    settings = get_settings()
    analysis = analyze_cluster(cluster_id, DuckDBRepository(settings.database_path), settings)
    if analysis["news_count"] == 0:
        raise HTTPException(404, "Cluster no encontrado.")
    package = EvidencePackage(**analysis["evidence_package"])
    if package.evidence_state != "suficiente para el borrador":
        return {"case_id": cluster_id, "drafts": {}}
    store = EditorialStore()
    drafts = {}
    for mode in ("brief", "script", "digital"):
        fingerprint = _fingerprint(package, mode)
        data = store.get_draft(cluster_id, mode, fingerprint)
        if data is not None:
            drafts[mode] = {**data, "cached": True, "cache_source": "persistent_database"}
    return {"case_id": cluster_id, "drafts": drafts}


@router.post("/{cluster_id}")
def generate(
    cluster_id: str,
    mode: Literal["brief", "script", "digital"] = Query("brief"),
    x_editor_key: str | None = Header(None),
):
    require_editor_access(x_editor_key)
    settings = get_settings()
    analysis = analyze_cluster(
        cluster_id,
        DuckDBRepository(settings.database_path),
        settings,
    )

    if analysis["news_count"] == 0:
        raise HTTPException(404, "Cluster no encontrado.")

    package = EvidencePackage(**analysis["evidence_package"])

    if package.evidence_state != "suficiente para el borrador":
        raise HTTPException(
            422,
            detail={
                "message": (
                    "La evidencia todavía no es suficiente para "
                    "el borrador editorial."
                ),
                "missing_information": package.missing_information,
                "contradictions": package.contradictions,
            },
        )

    fingerprint = _fingerprint(package, mode)
    store = EditorialStore()
    if settings.allow_cached_generation:
        stored = store.get_draft(cluster_id, mode, fingerprint)
        if stored is not None:
            return {**stored, "case_id": cluster_id, "cached": True,
                    "cache_source": "persistent_database",
                    "review_required": True, "publication_enabled": False}
        cached = load_cache(settings.generation_cache_dir, package, mode)
        if cached is not None:
            result_cached = {**cached, "case_id": cluster_id, "cached": True,
                             "cache_source": "snapshot",
                             "review_required": True, "publication_enabled": False}
            store.save_draft(cluster_id, mode, fingerprint, result_cached)
            return result_cached

    try:
        result = generate_editorial(
            build_llm_provider(settings),
            mode,
            package,
        )
    except RuntimeError as exc:
        if settings.allow_cached_generation:
            cached = load_cache(
                settings.generation_cache_dir,
                package,
                mode,
            )
            if cached is not None:
                return {
                    **cached,
                    "case_id": cluster_id,
                    "evidence_state": package.evidence_state,
                    "review_required": True,
                    "publication_enabled": False,
                    "cached": True,
                    "cache_fallback_reason": str(exc),
                }

        raise HTTPException(
            status_code=502,
            detail={
                "message": (
                    "No fue posible generar el borrador con Gemini."
                ),
                "provider_detail": str(exc),
            },
        ) from exc

    cache_file = save_cache(
        settings.generation_cache_dir,
        package,
        result,
    )

    payload = {
        "mode": result.mode,
        "draft": result.draft,
        "text": result.rendered_text,
        "quality": result.quality,
        "provider": result.provider,
        "model": result.model,
        "attempts": result.attempts,
        "generation_rounds": result.generation_rounds,
        "evidence_state": package.evidence_state,
        "case_id": cluster_id,
        "contradictions": package.contradictions,
        "review_required": True,
        "publication_enabled": False,
        "cached": False,
        "cache_file": str(cache_file),
    }
    store.save_draft(cluster_id, mode, fingerprint, payload)
    return payload
