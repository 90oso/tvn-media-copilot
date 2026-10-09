from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Header

from app.core.settings import get_settings
from app.core.editor_auth import require_editor_access
from app.repositories.duckdb_repo import DuckDBRepository
from app.schemas.review import ReviewRequest
from app.services.topic_analysis import analyze_cluster

router = APIRouter(prefix="/reviews", tags=["reviews"])

STATE_BY_ACTION = {
    "approve": "aprobado como borrador",
    "correct": "en revisión",
    "discard": "descartado",
}

@router.get("/{case_id}")
def get_review(case_id: str):
    settings = get_settings()
    repo = DuckDBRepository(settings.database_path)
    record = repo.get_review(case_id)
    if not record:
        return {"case_id": case_id, "review": None}
    return {"case_id": case_id, "review": record}

@router.post("/{case_id}")
def save_review(case_id: str, body: ReviewRequest, x_editor_key: str | None = Header(None)):
    require_editor_access(x_editor_key)
    settings = get_settings()
    repo = DuckDBRepository(settings.database_path)
    analysis = analyze_cluster(case_id, repo, settings)
    if analysis["news_count"] == 0:
        raise HTTPException(404, "Cluster no encontrado.")

    if body.action == "approve" and not analysis["workflow"]["draft_enabled"]:
        raise HTTPException(
            422,
            detail={
                "message": "No puede aprobarse como borrador mientras la evidencia sea insuficiente o parcial.",
                "evidence_state": analysis["evidence_package"]["evidence_state"],
            },
        )

    if body.action == "correct" and not body.note.strip():
        raise HTTPException(422, "La corrección requiere una nota del revisor.")

    state = STATE_BY_ACTION[body.action]
    record = repo.save_review(
        case_id=case_id,
        action=body.action,
        state=state,
        reviewer=body.reviewer.strip(),
        note=body.note.strip(),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    return {
        "case_id": case_id,
        "review": record,
        "publication_enabled": False,
    }
