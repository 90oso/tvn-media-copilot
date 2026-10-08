from fastapi import APIRouter
from app.core.settings import get_settings
from app.repositories.duckdb_repo import DuckDBRepository
router=APIRouter(tags=['system'])
@router.get('/health')
def health():
    s=get_settings(); return {'status':'ok','app':s.app_name,'version':s.app_version,'llm_provider':s.llm_provider,'database':DuckDBRepository(s.database_path).health()}
