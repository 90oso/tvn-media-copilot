"""Exploración editorial sobre metadatos y eventos del snapshot.

No responde preguntas como un LLM: recupera coincidencias trazables. La
ausencia de resultados produce una abstención explícita, no una cifra inferida.
"""
from __future__ import annotations

import re
from datetime import date
import unicodedata

import pandas as pd

from app.core.settings import Settings
from app.repositories.duckdb_repo import DuckDBRepository
from app.services.agenda import _cluster_column, _preview
from app.services.exploration_language import spanish_only, case_languages
from app.services.topic_analysis import analyze_cluster_from_frames

_STOP = {
    "a", "al", "ante", "con", "de", "del", "donde", "el", "en", "es", "hay",
    "la", "las", "lo", "los", "mas", "necesitan", "para", "por", "que",
    "requieren", "sobre", "su", "tema", "temas", "un", "una", "y", "cuales",
    "cual", "como", "puedo", "encontrar", "investigar", "investigacion", "panama",
    "noticias", "noticia", "quiero", "ver", "busca", "buscar", "informacion",
    "actualidad", "reportes", "reportado", "reportadas", "ultimas", "ultimo",
    "cinco", "merecen", "revision", "agenda", "priorizados", "priorizadas", "prioridad",
}
_SYNONYMS = {
    "economico": ("econom",), "economicos": ("econom",),
    "economica": ("econom",), "economicas": ("econom",),
    "inflacion": ("inflacion", "precios"),
    "desempleo": ("desempleo", "empleo", "trabajo"),
    "laboral": ("laboral", "empleo", "trabajo", "desempleo"),
    "laborales": ("laboral", "empleo", "trabajo", "desempleo"),
    "trabajo": ("trabajo", "empleo", "desempleo"),
    "empleo": ("empleo", "desempleo", "trabajo"),
    "canal": ("canal", "transito", "buques", "logistica"),
    "logistico": ("logistica", "canal", "transporte"),
    "turistico": ("turismo", "turista", "visitante"),
    "electricidad": ("electricidad", "energia", "apagones"),
}


def normalize(text: object) -> str:
    raw = unicodedata.normalize("NFKD", str(text or "").lower())
    raw = "".join(c for c in raw if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", raw)).strip()


def search_terms(question: str) -> list[str]:
    result: list[str] = []
    for term in normalize(question).split():
        if len(term) < 3 or term in _STOP:
            continue
        for mapped in _SYNONYMS.get(term, (term,)):
            if mapped not in result:
                result.append(mapped)
    return result


def _column_text(frame: pd.DataFrame, columns: tuple[str, ...]) -> str:
    texts: list[str] = []
    for col in columns:
        if col in frame:
            texts += [str(x) for x in frame[col].dropna().tolist()]
    return normalize(" ".join(texts))


def explore_events(
    repo: DuckDBRepository,
    settings: Settings,
    *,
    question: str = "",
    topic: str = "",
    evidence: str = "",
    language: str = "all",
    limit: int = 20,
    date_from: date | None = None,
    date_to: date | None = None,
    profile: str = "editorial",
) -> dict:
    news = repo.get_all_valid_news()
    col = _cluster_column(news)
    if news.empty or not col:
        return {"items": [], "count": 0, "total_matches": 0, "abstained": bool(question),
                "note": "No hay noticias utilizables en el snapshot."}

    if date_from or date_to:
        # Fecha efectiva: publicación cuando existe; en su defecto detección.
        # No se afirma que fecha_deteccion sea fecha de publicación.
        pub = (pd.to_datetime(news["fecha_publicacion"], errors="coerce", utc=True)
               if "fecha_publicacion" in news else
               pd.Series(pd.NaT, index=news.index, dtype="datetime64[ns, UTC]"))
        seen = (pd.to_datetime(news["fecha_deteccion"], errors="coerce", utc=True)
                if "fecha_deteccion" in news else
                pd.Series(pd.NaT, index=news.index, dtype="datetime64[ns, UTC]"))
        effective = pub.fillna(seen)
        mask = effective.notna()
        if date_from:
            mask &= effective >= pd.Timestamp(date_from.isoformat(), tz="UTC")
        if date_to:
            mask &= effective < pd.Timestamp(date_to.isoformat(), tz="UTC") + pd.Timedelta(days=1)
        news = news.loc[mask].copy()
        if news.empty:
            return {"items": [], "count": 0, "total_matches": 0, "abstained": True,
                    "note": "No hay coincidencias con fechas verificables en el intervalo seleccionado.",
                    "search_mode": "lexical_metadata"}

    terms = search_terms(question)
    normalized_question = normalize(question)
    agenda_intent = bool(question.strip() and not terms and ("agenda" in normalized_question or "cinco temas" in normalized_question or "top 5" in normalized_question))
    topic_norm = normalize(topic)
    # Carga masiva para no reintroducir N+1.
    indicators = repo.get_panama_indicators()
    reference = repo.get_snapshot_reference()
    reviews = repo.get_all_reviews()
    matched = []
    # Token overlap is a fallback when a phrase is absent verbatim.
    # Topic fields remain part of retrieval; the score is not factual confidence.
    for cid, frame in news.groupby(col, sort=False, dropna=True):
        preview_frame = spanish_only(frame) if language == "es" else frame
        if preview_frame.empty:
            continue
        titles = _column_text(preview_frame, ("titulo", "descripcion"))
        topics = _column_text(preview_frame, ("tema", "tema_semantic", "tema_baseline"))
        if topic_norm and topic_norm not in topics:
            continue
        # Recuperación léxica interpretable (no respuesta generativa).
        hits = [term for term in terms if term in titles or term in topics]
        lexical_relevance = len(hits) / max(1, len(terms))
        if terms and not hits:
            continue
        # Si la pregunta está formada solo por stopwords, no se inventa un filtro.
        if question.strip() and not terms and not agenda_intent:
            return {"items": [], "count": 0, "total_matches": 0, "abstained": True,
                    "note": "La consulta no contiene términos concretos para buscar en los titulares. Reformúlala."}

        entry = analyze_cluster_from_frames(
            str(cid), frame.reset_index(drop=True), indicators, settings,
            snapshot_reference=reference, review=reviews.get(str(cid)),
        )
        if evidence and entry["evidence_package"]["evidence_state"] != evidence:
            continue
        entry["decision_support"] = decision_support(entry, profile)
        entry.update(_preview(preview_frame))
        entry["case_languages"] = case_languages(frame)
        entry["search_matches"] = hits
        entry["retrieval"] = {"mode": "lexical_metadata", "term_coverage": round(lexical_relevance, 3), "matched_terms": hits}
        matched.append(entry)

    # Primero la relevancia de la consulta, luego el ranking oficial sin modificar su fórmula.
    matched.sort(key=lambda x: (
        -len(x["search_matches"]), -x["attention"]["score"],
        -x["attention"]["components"]["U"], x["case_id"],
    ))
    effective_limit = min(limit, 5) if agenda_intent and ("cinco" in normalized_question or "5" in normalized_question) else limit
    return {
        "items": matched[:effective_limit],
        "count": min(effective_limit, len(matched)),
        "total_matches": len(matched),
        "abstained": bool(question.strip() and not matched),
        "note": (
            "Sin coincidencias en titulares/metadatos del snapshot. No es posible "
            "responder esa consulta con el corpus disponible."
            if question.strip() and not matched
            else "Agenda priorizada mediante los componentes R/I/U/N/E." if agenda_intent
            else "Búsqueda orientativa por términos en titulares/metadatos: no verifica hechos."
        ),
        "search_mode": "editorial_agenda" if agenda_intent else "lexical_metadata",
    }


def decision_support(entry: dict, profile: str) -> dict:
    """Conservative, auditable decision framing; not autonomous business advice.

    Never transform editorial priority into business impact probability.
    Never claim external verification from a cluster score.
    """
    package = entry.get("evidence_package") or {}
    state = str(package.get("evidence_state") or "desconocido")
    missing = list(package.get("missing_information") or [])
    contradictions = list(package.get("contradictions") or [])
    provenance = int(package.get("independent_provenances") or 0)
    supported = provenance >= 2 and not contradictions and not missing
    actions = {
        "editorial": ("Revisar las fuentes originales y decidir si abrir una investigación editorial.",
                      "Solicitar corroboración adicional antes de publicar."),
        "business": ("Asignar un responsable para evaluar la exposición real de la organización.",
                     "Verificar el alcance geográfico, temporal y operativo antes de actuar."),
        "research": ("Incluir el evento como señal documentada en el análisis sectorial.",
                     "Ampliar la muestra y contrastar fuentes antes de formular conclusiones."),
    }
    primary, cautious = actions.get(profile, actions["editorial"])
    return {
        "profile": profile,
        "assessment": "Evidencia preliminar; requiere validación humana.",
        "evidence_state": state,
        "independent_provenances": provenance,
        "missing_information": missing,
        "contradictions": contradictions,
        "options": [
            {"action": cautious, "type": "verification"},
            {"action": primary, "type": "human_review"},
        ],
        "recommended_next_step": cautious if not supported else primary,
        "limitations": [
            "La prioridad editorial no mide impacto económico ni probabilidad de ocurrencia.",
            "El corpus disponible puede ser incompleto o histórico.",
            "No se ejecutan acciones externas ni se sustituyen decisiones profesionales.",
        ],
        "requires_human_approval": True,
    }
