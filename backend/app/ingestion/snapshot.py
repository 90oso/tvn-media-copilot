from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

import pandas as pd

from .common import file_sha256, normalize_url, save_json, utc_now_iso, within_date_window


NEWS_COLUMNS = [
    "id_noticia",
    "titulo",
    "url",
    "medio",
    "idioma",
    "fecha_publicacion",
    "fecha_deteccion",
    "fecha_extraccion",
    "tema",
    "origen",
    "alcance_texto",
]


def _coverage(df: pd.DataFrame) -> dict:
    result = {
        "fecha_publicacion_min": None,
        "fecha_publicacion_max": None,
        "fecha_deteccion_min": None,
        "fecha_deteccion_max": None,
    }
    for col in ("fecha_publicacion", "fecha_deteccion"):
        if col not in df.columns:
            continue
        parsed = pd.to_datetime(df[col], errors="coerce", utc=True).dropna()
        if not parsed.empty:
            result[f"{col}_min"] = parsed.min().isoformat()
            result[f"{col}_max"] = parsed.max().isoformat()
    return result


def build_news_snapshot(
    tvn_rows: list[dict],
    gdelt_rows: list[dict],
    start_date: str,
    end_date: str,
) -> tuple[pd.DataFrame, dict]:
    all_rows = tvn_rows + gdelt_rows
    if not all_rows:
        return pd.DataFrame(columns=NEWS_COLUMNS), {
            "input_records": 0,
            "output_records": 0,
            "duplicates_removed_by_url": 0,
            "coverage": {},
        }

    df = pd.DataFrame(all_rows)
    for col in NEWS_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    df["url_normalized"] = df["url"].fillna("").map(normalize_url)
    before = len(df)

    # Prefer TVN record when the same normalized URL appears from multiple collectors.
    df["_source_priority"] = df["origen"].eq("TVN RSS").map({True: 0, False: 1})
    df = (
        df.sort_values(["url_normalized", "_source_priority"])
        .drop_duplicates(subset=["url_normalized"], keep="first")
        .drop(columns=["_source_priority"])
    )
    after_dedupe = len(df)

    # Filtro temporal:
    # - si existe fecha_publicacion, se usa;
    # - si no existe (p.ej. GDELT), se usa fecha_deteccion sin confundir ambas columnas.
    pub = pd.to_datetime(df["fecha_publicacion"], errors="coerce", utc=True)
    det = pd.to_datetime(df["fecha_deteccion"], errors="coerce", utc=True)
    effective = pub.fillna(det)

    start = pd.Timestamp(start_date, tz="UTC")
    end_exclusive = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    mask = effective.notna() & (effective >= start) & (effective < end_exclusive)
    df = df.loc[mask].copy()

    df = df[NEWS_COLUMNS].sort_values(
        ["fecha_publicacion", "fecha_deteccion", "id_noticia"],
        na_position="last",
    ).reset_index(drop=True)

    meta = {
        "input_records": before,
        "output_records": len(df),
        "duplicates_removed_by_url": before - after_dedupe,
        "records_removed_outside_window_or_without_effective_date": after_dedupe - len(df),
        "coverage": _coverage(df),
        "requested_window": {
            "start": start_date,
            "end": end_date,
        },
    }
    return df, meta


def write_snapshot_files(
    news_df: pd.DataFrame,
    indicators_df: pd.DataFrame,
    snapshot_dir: Path,
) -> dict:
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    news_csv = snapshot_dir / "noticias.csv"
    news_parquet = snapshot_dir / "noticias.parquet"
    indicators_csv = snapshot_dir / "indicadores.csv"
    indicators_parquet = snapshot_dir / "indicadores.parquet"

    news_df.to_csv(news_csv, index=False, encoding="utf-8")
    indicators_df.to_csv(indicators_csv, index=False, encoding="utf-8")

    files = {
        "noticias.csv": news_csv,
        "indicadores.csv": indicators_csv,
    }

    # Parquet es la salida preferida. Si el entorno no instaló todavía pyarrow,
    # no perdemos el snapshot CSV; la instalación oficial sí incluye pyarrow.
    try:
        news_df.to_parquet(news_parquet, index=False)
        indicators_df.to_parquet(indicators_parquet, index=False)
        files["noticias.parquet"] = news_parquet
        files["indicadores.parquet"] = indicators_parquet
    except ImportError:
        pass

    return files


def write_manifest(
    snapshot_dir: Path,
    files: dict[str, Path],
    source_meta: dict,
    query_logs: dict,
    transformations: list[str],
    warnings: list[str],
    version: str,
    requested_window: dict,
) -> Path:
    manifest = {
        "version": version,
        "fecha_corte_UTC": utc_now_iso(),
        "requested_news_window": requested_window,
        "fuentes": source_meta,
        "consultas": query_logs,
        "cantidad_por_archivo": {},
        "licencia_condiciones": {
            "TVN": "Metadatos RSS; no asumir derechos sobre artículos, imágenes o videos.",
            "GDELT": "Metadatos/enlaces; GDELT no transfiere derechos de los medios enlazados.",
            "Banco Mundial": "CC BY 4.0 general; revisar excepciones de terceros.",
        },
        "sha256": {},
        "transformaciones": transformations,
        "warnings": warnings,
    }

    for name, path in files.items():
        manifest["sha256"][name] = file_sha256(path)
        if name.endswith(".csv"):
            try:
                manifest["cantidad_por_archivo"][name] = int(len(pd.read_csv(path)))
            except Exception:
                manifest["cantidad_por_archivo"][name] = None

    path = snapshot_dir / "manifest.json"
    save_json(path, manifest)
    return path
