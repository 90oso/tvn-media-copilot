from __future__ import annotations

import hashlib
import re
import unicodedata

import pandas as pd

from app.schemas.evidence import EvidenceItem, EvidencePackage
from app.services.contextualization import contextualize_case


def _safe(value):
    return "" if pd.isna(value) else str(value)


def _eid(prefix: str, *parts: str) -> str:
    return f"{prefix}-" + hashlib.sha1(
        "|".join(parts).encode("utf-8")
    ).hexdigest()[:12]


def _provenances(news: pd.DataFrame) -> int:
    if news.empty:
        return 0
    column = (
        "origen"
        if "origen" in news.columns
        else ("medio" if "medio" in news.columns else None)
    )
    if not column:
        return 0
    return len(
        {
            str(value).strip()
            for value in news[column].dropna()
            if str(value).strip()
        }
    )


def determine_evidence_state(
    provenance_count: int,
    official_context_count: int,
) -> str:
    # PROPUESTA: el reto define los estados, no estos umbrales.
    if provenance_count <= 0:
        return "insuficiente"
    if provenance_count == 1 and official_context_count == 0:
        return "insuficiente"
    if provenance_count >= 3 or (
        provenance_count >= 2 and official_context_count >= 1
    ):
        return "suficiente para el borrador"
    return "parcial"


def _norm(value: object) -> str:
    text = _safe(value).lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9ñ\s]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


_STOPWORDS = {
    "de", "la", "el", "los", "las", "un", "una", "y", "o", "en", "a",
    "para", "por", "con", "del", "al", "que", "se", "su", "sus", "panama",
    "panamá", "the", "a", "an", "of", "and", "in", "to", "for", "on",
}


# Reglas transparentes de contradicción potencial.
# No declaran que una fuente sea falsa; solo marcan versiones incompatibles
# que deben mostrarse y verificarse.
_OPPOSITION_RULES = (
    {
        "label": "reactivación/reapertura vs cierre",
        "left": (
            "reactivar", "reactivacion", "reabrir", "reapertura",
            "reiniciar", "reanudar",
        ),
        "right": (
            "cerrar", "cierre", "clausurar", "clausura",
            "desmantelar",
        ),
    },
    {
        "label": "aumento vs reducción",
        "left": (
            "aumenta", "aumento", "sube", "incrementa", "incremento",
        ),
        "right": (
            "reduce", "reduccion", "baja", "disminuye", "cae",
        ),
    },
    {
        "label": "aprobación/autorización vs rechazo",
        "left": (
            "aprueba", "aprobacion", "autoriza", "autorizacion",
        ),
        "right": (
            "rechaza", "rechazo", "niega", "deniega",
        ),
    },
)


def _content_tokens(text: str) -> set[str]:
    return {
        token
        for token in _norm(text).split()
        if len(token) >= 4 and token not in _STOPWORDS
    }


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    normalized = _norm(text)
    return any(term in normalized for term in terms)


def detect_potential_contradictions(
    news: pd.DataFrame,
    news_evidence_ids: dict[str, str],
) -> list[str]:
    """Detecta señales léxicas opuestas dentro de un cluster.

    Es deliberadamente conservador:
    - exige una regla de oposición explícita;
    - exige al menos dos tokens de contenido compartidos entre titulares.
    """
    if len(news) < 2:
        return []

    rows = []
    for _, row in news.iterrows():
        news_id = _safe(row.get("id_noticia"))
        title = _safe(row.get("titulo"))
        if not news_id or not title:
            continue
        rows.append(
            {
                "news_id": news_id,
                "title": title,
                "tokens": _content_tokens(title),
                "evidence_id": news_evidence_ids.get(news_id, news_id),
            }
        )

    contradictions: list[str] = []
    seen = set()

    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a = rows[i]
            b = rows[j]
            shared = a["tokens"] & b["tokens"]
            if len(shared) < 2:
                continue

            for rule in _OPPOSITION_RULES:
                opposite = (
                    _has_any(a["title"], rule["left"])
                    and _has_any(b["title"], rule["right"])
                ) or (
                    _has_any(a["title"], rule["right"])
                    and _has_any(b["title"], rule["left"])
                )

                if not opposite:
                    continue

                key = (
                    rule["label"],
                    min(a["evidence_id"], b["evidence_id"]),
                    max(a["evidence_id"], b["evidence_id"]),
                )
                if key in seen:
                    continue
                seen.add(key)

                contradictions.append(
                    "Posible contradicción "
                    f"({rule['label']}): "
                    f"[{a['evidence_id']}] «{a['title']}» frente a "
                    f"[{b['evidence_id']}] «{b['title']}». "
                    "No se determina cuál versión es correcta; requiere verificación "
                    "de contexto, fecha y fuente primaria."
                )

    return contradictions


def build_evidence_package(
    case_id: str,
    news: pd.DataFrame,
    indicators: pd.DataFrame,
    rules_version: str,
) -> EvidencePackage:
    if news.empty:
        return EvidencePackage(
            case_id=case_id,
            evidence_state="insuficiente",
            rules_version=rules_version,
            missing_information=[
                "No se encontraron noticias para el caso solicitado."
            ],
        )

    topic_column = (
        "tema_final"
        if "tema_final" in news.columns
        else (
            "tema_semantic"
            if "tema_semantic" in news.columns
            else (
                "tema_baseline"
                if "tema_baseline" in news.columns
                else ("tema" if "tema" in news.columns else None)
            )
        )
    )

    topic_values = (
        [str(value) for value in news[topic_column].dropna()]
        if topic_column
        else []
    )
    topic = topic_values[0] if topic_values else None

    evidence: list[EvidenceItem] = []
    missing: list[str] = []
    news_evidence_ids: dict[str, str] = {}

    for _, row in news.iterrows():
        news_id = _safe(row.get("id_noticia"))
        title = _safe(row.get("titulo"))
        scope = _safe(row.get("alcance_texto"))

        if title:
            evidence_id = _eid(
                "NEWS",
                news_id,
                _safe(row.get("url")),
                title,
            )
            news_evidence_ids[news_id] = evidence_id

            evidence.append(
                EvidenceItem(
                    evidence_id=evidence_id,
                    source_type="news",
                    source_name=(
                        _safe(row.get("medio"))
                        or _safe(row.get("origen"))
                        or "fuente pública"
                    ),
                    url=_safe(row.get("url")) or None,
                    period=_safe(row.get("fecha_publicacion")) or None,
                    field="titulo",
                    value=title,
                    scope_note=(
                        "Basado únicamente en titular/metadatos."
                        if (
                            "titular" in scope.lower()
                            or "metadatos" in scope.lower()
                        )
                        else (scope or None)
                    ),
                )
            )
        else:
            missing.append(f"{news_id}: falta titular.")

    contexts, notes = contextualize_case(topic, news, indicators)
    missing += notes

    for context in contexts:
        evidence.append(
            EvidenceItem(
                evidence_id=_eid(
                    "WB",
                    context["indicator_id"],
                    context["year"],
                ),
                source_type="official_indicator",
                source_name="Banco Mundial",
                url=context["source_url"] or None,
                period=context["year"],
                unit=context["unit"] or None,
                field=context["indicator_id"],
                value=context["value"],
                scope_note=context["scope_note"],
            )
        )

    provenance_count = _provenances(news)
    if provenance_count <= 1:
        missing.append(
            "La procedencia independiente es limitada; "
            "se requiere corroboración adicional."
        )

    contradictions = detect_potential_contradictions(
        news,
        news_evidence_ids,
    )

    return EvidencePackage(
        case_id=case_id,
        topic=topic,
        news_ids=[
            _safe(value)
            for value in news["id_noticia"].tolist()
        ],
        evidence=evidence,
        missing_information=sorted(set(missing)),
        contradictions=contradictions,
        evidence_state=determine_evidence_state(
            provenance_count,
            len(contexts),
        ),
        independent_provenances=provenance_count,
        rules_version=rules_version,
    )
