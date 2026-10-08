from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import time

import pandas as pd

from .common import (
    build_http_session,
    normalize_url,
    stable_news_id,
    utc_now_iso,
)


DEFAULT_QUERIES = {
    "panama": "Panama",
    "logistica": 'Panama (canal OR logistics OR shipping OR maritime)',
    "turismo": 'Panama (tourism OR tourist OR hotel)',
    "economia": 'Panama (economy OR GDP OR inflation OR unemployment OR exports)',
    "eventos_naturales": 'Panama (earthquake OR flood OR storm OR drought OR landslide)',
}


def _parse_seen_date(value: object) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S"):
        try:
            dt = datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
            return dt.isoformat().replace("+00:00", "Z")
        except ValueError:
            pass
    parsed = pd.to_datetime(text, errors="coerce", utc=True)
    if pd.isna(parsed):
        return None
    return parsed.isoformat().replace("+00:00", "Z")


def _iter_windows(start_date: str, end_date: str, chunk_days: int):
    start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    end_inclusive = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
    cursor = start
    while cursor <= end_inclusive:
        chunk_end = min(
            cursor + timedelta(days=chunk_days) - timedelta(seconds=1),
            end_inclusive + timedelta(days=1) - timedelta(seconds=1),
        )
        yield cursor, chunk_end
        cursor = chunk_end + timedelta(seconds=1)


def collect_gdelt(
    base_url: str,
    start_date: str,
    end_date: str,
    user_agent: str,
    raw_dir: Path,
    chunk_days: int = 7,
    request_delay_seconds: float = 0.25,
    max_records: int = 250,
    queries: dict[str, str] | None = None,
    timeout: int = 45,
) -> tuple[list[dict], list[dict], list[str]]:
    """Consulta DOC 2.0 por ventanas y conserva `seendate` como detección.

    Importante: no copia `seendate` en `fecha_publicacion`.
    Si GDELT no expone una fecha de publicación distinta, `fecha_publicacion`
    queda nula.
    """
    queries = queries or DEFAULT_QUERIES
    session = build_http_session(user_agent)
    raw_dir.mkdir(parents=True, exist_ok=True)

    extraction = utc_now_iso()
    rows: list[dict] = []
    query_log: list[dict] = []
    warnings: list[str] = []

    for query_name, query_text in queries.items():
        for start_dt, end_dt in _iter_windows(start_date, end_date, chunk_days):
            params = {
                "query": query_text,
                "mode": "ArtList",
                "maxrecords": max_records,
                "format": "json",
                "startdatetime": start_dt.strftime("%Y%m%d%H%M%S"),
                "enddatetime": end_dt.strftime("%Y%m%d%H%M%S"),
                "sort": "DateAsc",
            }

            response = session.get(base_url, params=params, timeout=timeout)
            status = response.status_code

            query_entry = {
                "query_name": query_name,
                "query": query_text,
                "startdatetime": params["startdatetime"],
                "enddatetime": params["enddatetime"],
                "status_code": status,
                "requested_maxrecords": max_records,
            }

            if status != 200:
                query_entry["error"] = response.text[:500]
                query_log.append(query_entry)
                warnings.append(
                    f"GDELT {query_name} {params['startdatetime']}–{params['enddatetime']}: HTTP {status}"
                )
                time.sleep(request_delay_seconds)
                continue

            try:
                payload = response.json()
            except Exception:
                query_entry["error"] = "Respuesta no JSON"
                query_log.append(query_entry)
                warnings.append(
                    f"GDELT {query_name} devolvió una respuesta no JSON."
                )
                time.sleep(request_delay_seconds)
                continue

            raw_path = raw_dir / (
                f"gdelt_{query_name}_{params['startdatetime']}_{params['enddatetime']}.json"
            )
            raw_path.write_text(
                __import__("json").dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            articles = payload.get("articles", []) if isinstance(payload, dict) else []
            query_entry["records_returned"] = len(articles)
            query_log.append(query_entry)

            if len(articles) >= max_records:
                warnings.append(
                    f"GDELT {query_name} alcanzó maxrecords={max_records} en "
                    f"{params['startdatetime']}–{params['enddatetime']}; considerar reducir la ventana."
                )

            for article in articles:
                url = normalize_url(str(article.get("url", "") or ""))
                title = str(article.get("title", "") or "").strip()
                if not url or not title:
                    continue

                detected = _parse_seen_date(article.get("seendate"))
                language = str(article.get("language", "") or "").strip() or "desconocido"
                domain = str(article.get("domain", "") or "").strip() or "GDELT"

                rows.append(
                    {
                        "id_noticia": stable_news_id(url),
                        "titulo": title,
                        "url": url,
                        "medio": domain,
                        "idioma": language,
                        # No inventamos publicación a partir de seendate.
                        "fecha_publicacion": None,
                        "fecha_deteccion": detected,
                        "fecha_extraccion": extraction,
                        "tema": "sin_clasificar",
                        "origen": domain,
                        "alcance_texto": "titular/metadatos",
                        "_gdelt_query": query_name,
                    }
                )

            time.sleep(request_delay_seconds)

    return rows, query_log, warnings
