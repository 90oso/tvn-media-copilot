from fastapi import APIRouter,HTTPException
from app.core.settings import get_settings
from app.repositories.duckdb_repo import DuckDBRepository
from app.services.topic_analysis import analyze_cluster
router=APIRouter(prefix='/topics',tags=['topics'])
@router.get('/{cluster_id}/analysis')
def topic_analysis(cluster_id:str):
    s=get_settings(); r=analyze_cluster(cluster_id,DuckDBRepository(s.database_path),s)
    if r['news_count']==0: raise HTTPException(404,'Cluster no encontrado.')
    return r
