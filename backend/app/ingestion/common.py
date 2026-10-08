from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import json

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_news_id(url: str) -> str:
    return "NEWS-" + sha256(url.strip().encode("utf-8")).hexdigest()[:16]


def normalize_url(url: str) -> str:
    """Normalización conservadora para deduplicación.

    Elimina fragmentos y parámetros UTM conocidos, pero no altera path/dominio.
    """
    if not url:
        return ""
    p = urlsplit(url.strip())
    params = [
        (k, v)
        for k, v in parse_qsl(p.query, keep_blank_values=True)
        if not k.lower().startswith("utm_")
        and k.lower() not in {"fbclid", "gclid"}
    ]
    return urlunsplit(
        (p.scheme.lower(), p.netloc.lower(), p.path, urlencode(params), "")
    )


def file_sha256(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_http_session(user_agent: str) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        status=4,
        backoff_factor=0.7,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        raise_on_status=False,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": user_agent})
    return session


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def within_date_window(
    value: object,
    start_date: str,
    end_date: str,
) -> bool:
    if value is None or pd.isna(value) or str(value).strip() == "":
        return False
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return False
    start = pd.Timestamp(start_date, tz="UTC")
    end_exclusive = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    return start <= parsed < end_exclusive
