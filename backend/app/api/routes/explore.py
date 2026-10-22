from typing import Literal
from datetime import date
from fastapi import HTTPException

from fastapi import APIRouter, Query

from app.core.settings import get_settings
from app.repositories.duckdb_repo import DuckDBRepository
from app.services.exploration import explore_events

router = APIRouter(prefix="/explore", tags=["editorial exploration"])


@router.get("")
def explore(
    q: str = Query("", max_length=240),
    topic: str = Query("", max_length=80),
    evidence: str = Query("", max_length=80),
    language: Literal["es", "all"] = Query("all"),
    limit: int = Query(20, ge=1, le=30),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail='El inicio no puede ser posterior al fin.')
    settings = get_settings()
    return explore_events(
        DuckDBRepository(settings.database_path), settings,
        question=q, topic=topic, evidence=evidence, language=language, limit=limit,
        date_from=date_from, date_to=date_to,
    )
