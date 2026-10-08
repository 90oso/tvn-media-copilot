from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import re

import feedparser
import pandas as pd

from .common import (
    build_http_session,
    normalize_url,
    stable_news_id,
    utc_now_iso,
    within_date_window,
)


def _entry_date(entry) -> str | None:
    raw = getattr(entry, "published", None) or getattr(entry, "updated", None)
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except Exception:
        parsed = pd.to_datetime(raw, errors="coerce", utc=True)
        if pd.isna(parsed):
            return None
        return parsed.isoformat().replace("+00:00", "Z")


def collect_tvn_rss(
    rss_url: str,
    start_date: str,
    end_date: str,
    user_agent: str,
    timeout: int = 30,
) -> tuple[list[dict], dict, bytes]:
    """Recolecta únicamente metadatos del RSS.

    No descarga el cuerpo completo de los artículos.
    """
    if not rss_url:
        raise ValueError("TVN_RSS_URL está vacío.")

    session = build_http_session(user_agent)
    response = session.get(rss_url, timeout=timeout)
    response.raise_for_status()
    raw_bytes = response.content

    feed = feedparser.parse(raw_bytes)
    extraction = utc_now_iso()
    rows: list[dict] = []

    for entry in feed.entries:
        url = normalize_url(str(getattr(entry, "link", "") or ""))
        title = str(getattr(entry, "title", "") or "").strip()
        published = _entry_date(entry)

        if not url or not title:
            continue
        if not published or not within_date_window(published, start_date, end_date):
            continue

        language = (
            str(getattr(entry, "language", "") or "").strip()
            or str(getattr(feed.feed, "language", "") or "").strip()
            or "es"
        )

        rows.append(
            {
                "id_noticia": stable_news_id(url),
                "titulo": title,
                "url": url,
                "medio": "TVN Panamá",
                "idioma": language,
                "fecha_publicacion": published,
                "fecha_deteccion": extraction,
                "fecha_extraccion": extraction,
                "tema": "sin_clasificar",
                "origen": "TVN RSS",
                "alcance_texto": "titular/metadatos",
            }
        )

    meta = {
        "source": "TVN RSS",
        "url": rss_url,
        "extracted_at_utc": extraction,
        "feed_entries_seen": len(feed.entries),
        "records_in_requested_window": len(rows),
        "requested_start": start_date,
        "requested_end": end_date,
        "warning": (
            "El RSS puede no conservar el histórico completo. "
            "La cobertura efectiva debe registrarse y no inferirse."
        ),
    }
    return rows, meta, raw_bytes
