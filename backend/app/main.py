from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.health import router as health_router
from app.api.routes.news import router as news_router
from app.api.routes.topics import router as topics_router
from app.api.routes.ranking import router as ranking_router
from app.api.routes.generation import router as generation_router
from app.api.routes.agenda import router as agenda_router
from app.api.routes.reviews import router as reviews_router
from app.api.routes.explore import router as explore_router
from app.core.settings import get_settings
s=get_settings(); app=FastAPI(title=s.app_name,version=s.app_version,description='Copiloto editorial: evidencia, contextualización, priorización explicable y generación condicionada por evidencia.')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:3000'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
for r in (health_router,news_router,agenda_router,topics_router,ranking_router,generation_router,reviews_router,explore_router): app.include_router(r)
