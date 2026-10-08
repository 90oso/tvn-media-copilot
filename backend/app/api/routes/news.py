from fastapi import APIRouter,Query
from app.core.settings import get_settings
from app.repositories.duckdb_repo import DuckDBRepository
router=APIRouter(prefix='/news',tags=['news'])
@router.get('')
def list_news(limit:int=Query(20,ge=1,le=100)):
    s=get_settings(); df=DuckDBRepository(s.database_path).list_news(limit)
    return {'count':len(df),'items':df.where(df.notna(),None).to_dict(orient='records')}
