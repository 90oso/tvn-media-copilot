"""Filtro de descubrimiento por idioma, nunca elimina fuentes del snapshot."""
import re
import unicodedata
import pandas as pd


def is_spanish_news(row: pd.Series) -> bool:
    raw_language = row.get("idioma", "")
    language = "" if pd.isna(raw_language) else str(raw_language).strip().lower()
    normalized = unicodedata.normalize("NFKD", language)
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    title = row.get("titulo", "")
    title = "" if pd.isna(title) else str(title)
    if re.search(r"[\u0400-\u052f]", title):
        return False
    return bool(language == "es" or language.startswith(("es-", "es_")) or normalized in ("spa", "spanish", "espanol"))


def spanish_only(frame: pd.DataFrame) -> pd.DataFrame:
    if "idioma" not in frame.columns:
        return frame.iloc[0:0]
    return frame.loc[frame.apply(is_spanish_news, axis=1)]


def case_languages(frame: pd.DataFrame) -> list[str]:
    if "idioma" not in frame.columns:
        return ["no identificado"]
    vals = {str(v).strip().lower() for v in frame["idioma"].dropna().tolist() if str(v).strip()}
    return sorted(vals) or ["no identificado"]
