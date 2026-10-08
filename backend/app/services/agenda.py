from app.core.settings import Settings
from app.repositories.duckdb_repo import DuckDBRepository
from app.services.topic_analysis import analyze_cluster

def build_agenda(repo:DuckDBRepository,settings:Settings,limit:int=5)->list[dict]:
    items=[analyze_cluster(cid,repo,settings) for cid in repo.list_cluster_ids()]
    items.sort(key=lambda x:(-x["attention"]["score"],-x["attention"]["components"]["U"],x["case_id"]))
    return items[:limit]
