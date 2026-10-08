from fastapi import APIRouter, Query

from app.core.settings import get_settings
from app.repositories.duckdb_repo import DuckDBRepository
from app.services.agenda import build_agenda

router = APIRouter(prefix="/agenda", tags=["agenda"])


@router.get("")
def agenda(limit: int = Query(5, ge=1, le=20)):
    settings = get_settings()
    items = build_agenda(
        DuckDBRepository(settings.database_path),
        settings,
        limit,
    )
    return {
        "count": len(items),
        "items": items,
        "tie_break": "mayor urgencia y luego ID",
        "ranking_note": (
            "La prioridad de atención y la suficiencia de evidencia son ejes separados. "
            "Un caso de atención alta puede quedar en `requiere evidencia`."
        ),
    }
