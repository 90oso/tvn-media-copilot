from pathlib import Path

import pandas as pd

from app.ingestion.common import normalize_url, stable_news_id
from app.ingestion.snapshot import build_news_snapshot
from app.ingestion.worldbank import COUNTRIES, INDICATORS


def test_url_normalization_removes_tracking():
    value = normalize_url(
        "https://Example.org/a?utm_source=x&keep=1#fragment"
    )
    assert value == "https://example.org/a?keep=1"


def test_stable_id_is_deterministic():
    assert stable_news_id("https://example.org/a") == stable_news_id(
        "https://example.org/a"
    )


def test_snapshot_deduplicates_by_normalized_url_and_keeps_dates_separate():
    tvn = [
        {
            "id_noticia": "TVN1",
            "titulo": "Título TVN",
            "url": "https://example.org/a?utm_source=x",
            "medio": "TVN Panamá",
            "idioma": "es",
            "fecha_publicacion": "2026-06-01T12:00:00Z",
            "fecha_deteccion": "2026-06-01T13:00:00Z",
            "fecha_extraccion": "2026-06-01T13:00:00Z",
            "tema": "sin_clasificar",
            "origen": "TVN RSS",
            "alcance_texto": "titular/metadatos",
        }
    ]
    gdelt = [
        {
            "id_noticia": "G1",
            "titulo": "Título GDELT",
            "url": "https://example.org/a",
            "medio": "example.org",
            "idioma": "Spanish",
            "fecha_publicacion": None,
            "fecha_deteccion": "2026-06-01T14:00:00Z",
            "fecha_extraccion": "2026-06-01T15:00:00Z",
            "tema": "sin_clasificar",
            "origen": "example.org",
            "alcance_texto": "titular/metadatos",
        }
    ]

    df, meta = build_news_snapshot(
        tvn,
        gdelt,
        "2025-10-02",
        "2026-09-30",
    )

    assert len(df) == 1
    assert meta["duplicates_removed_by_url"] == 1
    assert meta["records_removed_outside_window_or_without_effective_date"] == 0
    assert df.iloc[0]["titulo"] == "Título TVN"
    assert df.iloc[0]["fecha_publicacion"] == "2026-06-01T12:00:00Z"
    assert df.iloc[0]["fecha_deteccion"] == "2026-06-01T13:00:00Z"


def test_world_bank_enumerated_grid_is_540():
    years = list(range(2010, 2025))
    assert len(COUNTRIES) * len(INDICATORS) * len(years) == 540
