from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score

# Categorías exigidas por el documento para la etapa "Organizar".
OFFICIAL_TOPICS = (
    "economía",
    "logística/Canal",
    "turismo",
    "servicios públicos",
    "eventos naturales",
    "regulación",
)

# PROPUESTA DEL EQUIPO:
# baseline simple por palabras/frases clave. No es IA y no pretende ser perfecto.
# Se conserva precisamente para poder compararlo después con una capacidad NLP/ML.
BASELINE_KEYWORDS = {
    "economía": (
        "economía",
        "económico",
        "económica",
        "pib",
        "inflación",
        "desempleo",
        "exportación",
        "exportaciones",
        "importación",
        "importaciones",
        "comercio",
        "inversión",
        "crecimiento",
        "precio",
        "precios",
        "salario",
        "empleo",
    ),
    "logística/Canal": (
        "canal de panamá",
        "canal",
        "logística",
        "logístico",
        "puerto",
        "puertos",
        "buque",
        "buques",
        "contenedor",
        "contenedores",
        "carga",
        "tránsito marítimo",
        "marítimo",
        "peaje",
        "esclusa",
        "esclusas",
    ),
    "turismo": (
        "turismo",
        "turístico",
        "turística",
        "turista",
        "turistas",
        "hotel",
        "hoteles",
        "visitante",
        "visitantes",
        "aeropuerto",
        "vuelo",
        "vuelos",
        "crucero",
        "cruceros",
    ),
    "servicios públicos": (
        "servicios públicos",
        "agua potable",
        "agua",
        "electricidad",
        "energía",
        "apagón",
        "apagones",
        "transporte público",
        "metro",
        "acueducto",
        "alcantarillado",
        "recolección de basura",
        "idaan",
        "etesa",
        "ensa",
        "naturgy",
    ),
    "eventos naturales": (
        "sismo",
        "sismos",
        "terremoto",
        "inundación",
        "inundaciones",
        "lluvia",
        "lluvias",
        "tormenta",
        "huracán",
        "deslizamiento",
        "sequía",
        "incendio forestal",
        "evento natural",
        "fenómeno natural",
    ),
    "regulación": (
        "regulación",
        "regulatorio",
        "regulatoria",
        "ley",
        "leyes",
        "decreto",
        "resolución",
        "reglamento",
        "norma",
        "normativa",
        "gaceta oficial",
        "asamblea nacional",
        "superintendencia",
    ),
}


@dataclass(frozen=True)
class BaselinePrediction:
    topic: str | None
    status: str
    match_count: int
    matched_keywords: tuple[str, ...]
    tied_topics: tuple[str, ...] = ()


def _normalize(text: object) -> str:
    if pd.isna(text):
        return ""
    value = str(text).lower().strip()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9ñ\s/]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return f" {value} "


_NORMALIZED_KEYWORDS = {
    topic: tuple((_normalize(k).strip(), k) for k in keywords)
    for topic, keywords in BASELINE_KEYWORDS.items()
}


def classify_title_baseline(title: object) -> BaselinePrediction:
    """Clasifica únicamente el título disponible en el contrato actual.

    Si no hay señal suficiente o existe empate entre temas, se abstiene.
    `sin_clasificar` es un estado técnico, NO una séptima categoría editorial.
    """
    normalized = _normalize(title)
    if not normalized.strip():
        return BaselinePrediction(
            topic=None,
            status="sin_clasificar",
            match_count=0,
            matched_keywords=(),
        )

    matches_by_topic: dict[str, list[str]] = {}

    for topic, keyword_pairs in _NORMALIZED_KEYWORDS.items():
        found: list[str] = []
        for normalized_keyword, original_keyword in keyword_pairs:
            needle = f" {normalized_keyword} "
            if needle in normalized:
                found.append(original_keyword)
        matches_by_topic[topic] = found

    scores = {topic: len(found) for topic, found in matches_by_topic.items()}
    max_score = max(scores.values(), default=0)

    if max_score == 0:
        return BaselinePrediction(
            topic=None,
            status="sin_clasificar",
            match_count=0,
            matched_keywords=(),
        )

    winners = tuple(topic for topic, score in scores.items() if score == max_score)

    if len(winners) > 1:
        merged = tuple(
            sorted(
                {
                    keyword
                    for topic in winners
                    for keyword in matches_by_topic[topic]
                }
            )
        )
        return BaselinePrediction(
            topic=None,
            status="empate",
            match_count=max_score,
            matched_keywords=merged,
            tied_topics=winners,
        )

    winner = winners[0]
    return BaselinePrediction(
        topic=winner,
        status="clasificado",
        match_count=max_score,
        matched_keywords=tuple(matches_by_topic[winner]),
    )


def classify_dataframe_baseline(
    df: pd.DataFrame,
    title_column: str = "titulo",
) -> pd.DataFrame:
    if title_column not in df.columns:
        raise ValueError(f"Falta la columna requerida para el baseline: {title_column}")

    out = df.copy()
    predictions = [classify_title_baseline(value) for value in out[title_column]]

    out["tema_baseline"] = [
        p.topic if p.topic is not None else "sin_clasificar"
        for p in predictions
    ]
    out["baseline_estado"] = [p.status for p in predictions]
    out["baseline_coincidencias"] = [p.match_count for p in predictions]
    out["baseline_keywords"] = [
        " | ".join(p.matched_keywords) for p in predictions
    ]
    out["baseline_empates"] = [
        " | ".join(p.tied_topics) for p in predictions
    ]

    # Importante: NO sobrescribe `tema`.
    return out


def evaluate_against_reference(
    df: pd.DataFrame,
    reference_column: str = "tema",
    prediction_column: str = "tema_baseline",
) -> dict:
    """Evalúa solo filas cuyo `tema` de referencia pertenece a las seis categorías.

    Si no existen etiquetas humanas válidas, devuelve métricas como no disponibles.
    Una predicción `sin_clasificar` cuenta como fallo frente a una etiqueta disponible.
    """
    if reference_column not in df.columns or prediction_column not in df.columns:
        return {
            "available": False,
            "reason": "No existen columnas de referencia/predicción.",
            "n_labeled": 0,
        }

    ref = df[reference_column].astype("string")
    mask = ref.isin(OFFICIAL_TOPICS)
    evaluation = df.loc[mask].copy()

    if evaluation.empty:
        return {
            "available": False,
            "reason": (
                "No hay etiquetas de referencia válidas. "
                "Las métricas deben calcularse sobre etiquetas humanas."
            ),
            "n_labeled": 0,
        }

    y_true = evaluation[reference_column].astype(str)
    y_pred = evaluation[prediction_column].astype(str)

    classified_mask = y_pred.isin(OFFICIAL_TOPICS)
    coverage = float(classified_mask.mean())

    return {
        "available": True,
        "n_labeled": int(len(evaluation)),
        "classification_coverage": round(coverage, 4),
        "macro_f1": round(
            float(
                f1_score(
                    y_true,
                    y_pred,
                    labels=list(OFFICIAL_TOPICS),
                    average="macro",
                    zero_division=0,
                )
            ),
            4,
        ),
        "macro_precision": round(
            float(
                precision_score(
                    y_true,
                    y_pred,
                    labels=list(OFFICIAL_TOPICS),
                    average="macro",
                    zero_division=0,
                )
            ),
            4,
        ),
        "macro_recall": round(
            float(
                recall_score(
                    y_true,
                    y_pred,
                    labels=list(OFFICIAL_TOPICS),
                    average="macro",
                    zero_division=0,
                )
            ),
            4,
        ),
        "warning": (
            "Estas métricas solo son válidas como evaluación real si `tema` "
            "fue etiquetado mediante revisión humana. No usar etiquetas sintéticas "
            "como resultado final del reto."
        ),
    }
