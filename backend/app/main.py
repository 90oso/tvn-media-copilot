from __future__ import annotations

import os

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

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Copiloto editorial: evidencia, contextualización, priorización explicable y generación condicionada por evidencia.",
)

# Las URLs públicas deben indicarse explícitamente en el hosting.
# No usamos '*' en CORS y mantenemos el frontend local para desarrollo.
origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
origins.extend(
    origin.strip().rstrip("/")
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    health_router,
    news_router,
    agenda_router,
    topics_router,
    ranking_router,
    generation_router,
    reviews_router,
    explore_router,
):
    app.include_router(router)
