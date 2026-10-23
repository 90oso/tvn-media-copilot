"""Conservative, bounded research workflow over the existing evidence corpus.

This is a deterministic tool orchestration, not an autonomous web-browsing agent.
"""
from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.settings import get_settings
from app.repositories.duckdb_repo import DuckDBRepository
from app.services.exploration import explore_events

router = APIRouter(prefix="/research", tags=["decision intelligence"])


class ResearchRequest(BaseModel):
    objective: str = Field(min_length=8, max_length=240)
    profile: Literal["editorial", "business", "research"] = "business"
    date_from: date | None = None
    date_to: date | None = None
    limit: int = Field(default=5, ge=1, le=10)


@router.post("/investigate")
def investigate(request: ResearchRequest):
    if request.date_from and request.date_to and request.date_from > request.date_to:
        raise HTTPException(422, "La fecha inicial debe ser anterior a la final.")
    settings = get_settings()
    repo = DuckDBRepository(settings.database_path)
    # Bounded sequence: retrieve, rank, inspect evidence, propose supervised follow-up.
    result = explore_events(
        repo, settings, question=request.objective, profile=request.profile,
        date_from=request.date_from, date_to=request.date_to, limit=request.limit,
    )
    items = result.get("items", [])
    steps = [
        {"tool": "explore_events", "status": "completed", "purpose": "Recuperar acontecimientos del corpus existente"},
        {"tool": "evidence_review", "status": "completed", "purpose": "Identificar vacíos y contrastes disponibles"},
        {"tool": "decision_support", "status": "completed", "purpose": "Preparar próximos pasos para aprobación humana"},
    ]
    return {
        "objective": request.objective, "profile": request.profile,
        "status": "evidence_found" if items else "insufficient_evidence",
        "steps": steps, "cases": items,
        "limitations": [
            "Investigación acotada al corpus local, no a la web en vivo.",
            "La recuperación inicial es léxica; puede omitir relaciones semánticas.",
            "Las recomendaciones son pasos de verificación, no decisiones automáticas.",
        ],
        "requires_human_approval": True,
    }
