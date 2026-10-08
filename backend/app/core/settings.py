from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import os
from dotenv import load_dotenv
from pydantic import BaseModel

class Settings(BaseModel):
    app_name: str = 'TVN Media Copilot'
    app_version: str = '0.9.1'
    app_env: str = 'development'
    database_path: Path = Path('data/app.duckdb')
    processed_news_csv: Path = Path('data/processed/noticias_ready.csv')
    indicators_csv: Path = Path('data/processed/indicadores_validated.csv')
    llm_provider: str = 'gemini'
    gemini_api_key: str = ''
    gemini_model: str = ''
    gemini_base_url: str = 'https://generativelanguage.googleapis.com/v1beta'
    request_timeout_seconds: int = 30
    gemini_max_retries: int = 4
    gemini_retry_base_seconds: float = 1.0
    generation_cache_dir: Path = Path('data/cache/generation')
    allow_cached_generation: bool = True
    ranking_rules_version: str = 'attention-v0.1-proposed'
    evidence_rules_version: str = 'evidence-v0.1-proposed'

@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        app_name=os.getenv('APP_NAME','TVN Media Copilot'),
        app_version=os.getenv('APP_VERSION','0.9.1'),
        app_env=os.getenv('APP_ENV','development'),
        database_path=Path(os.getenv('DATABASE_PATH','data/app.duckdb')),
        processed_news_csv=Path(os.getenv('PROCESSED_NEWS_CSV','data/processed/noticias_ready.csv')),
        indicators_csv=Path(os.getenv('INDICATORS_CSV','data/processed/indicadores_validated.csv')),
        llm_provider=os.getenv('LLM_PROVIDER','gemini'),
        gemini_api_key=os.getenv('GEMINI_API_KEY',''),
        gemini_model=os.getenv('GEMINI_MODEL',''),
        gemini_base_url=os.getenv('GEMINI_BASE_URL','https://generativelanguage.googleapis.com/v1beta'),
        request_timeout_seconds=int(os.getenv('REQUEST_TIMEOUT_SECONDS','30')),
        gemini_max_retries=int(os.getenv('GEMINI_MAX_RETRIES','4')),
        gemini_retry_base_seconds=float(os.getenv('GEMINI_RETRY_BASE_SECONDS','1.0')),
        generation_cache_dir=Path(os.getenv('GENERATION_CACHE_DIR','data/cache/generation')),
        allow_cached_generation=os.getenv('ALLOW_CACHED_GENERATION','true').strip().lower() not in {'0','false','no','off'},
        ranking_rules_version=os.getenv('RANKING_RULES_VERSION','attention-v0.1-proposed'),
        evidence_rules_version=os.getenv('EVIDENCE_RULES_VERSION','evidence-v0.1-proposed'),
    )
