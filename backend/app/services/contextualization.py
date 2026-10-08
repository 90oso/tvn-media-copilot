import re
import unicodedata

import pandas as pd

# PROPUESTA DEL EQUIPO, deliberadamente conservadora.
INDICATOR_LABELS = {
    "NY.GDP.MKTP.KD.ZG": "Crecimiento del PIB",
    "FP.CPI.TOTL.ZG": "Inflación",
    "SL.UEM.TOTL.ZS": "Desempleo",
    "SP.POP.TOTL": "Población",
    "IT.NET.USER.ZS": "Uso de internet",
    "NE.EXP.GNFS.ZS": "Exportaciones/PIB",
}


LEGACY_TOPIC_TO_INDICATORS = {
    "economía": (
        "NY.GDP.MKTP.KD.ZG",
        "FP.CPI.TOTL.ZG",
        "SL.UEM.TOTL.ZS",
        "NE.EXP.GNFS.ZS",
    ),
    "logística/Canal": (
        "NY.GDP.MKTP.KD.ZG",
        "NE.EXP.GNFS.ZS",
    ),
}

# Fallback temático cuando el titular no contiene una señal suficientemente específica.
TOPIC_FALLBACK = {
    "economía": ("NY.GDP.MKTP.KD.ZG",),
    "logística/Canal": ("NE.EXP.GNFS.ZS",),
}

# Señales textuales transparentes. No son una verdad causal; solo determinan qué
# indicador oficial es pertinente como contexto.
INDICATOR_SIGNALS = {
    "SL.UEM.TOTL.ZS": (
        "desempleo", "empleo", "empleados", "trabajo", "laboral",
        "plazas", "contratacion", "contrataciones",
    ),
    "FP.CPI.TOTL.ZG": (
        "inflacion", "precios", "ipc", "costo de vida", "canasta basica",
    ),
    "NY.GDP.MKTP.KD.ZG": (
        "pib", "producto interno bruto", "crecimiento economico",
        "actividad economica", "economia crece", "economia cae",
    ),
    "NE.EXP.GNFS.ZS": (
        "exportacion", "exportaciones", "comercio exterior",
        "ventas al exterior", "balanza comercial",
    ),
}


def _norm(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip()


def _latest_per_indicator(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    x = df.copy()
    x["_anio"] = pd.to_numeric(x["anio"], errors="coerce")
    return (
        x.sort_values(["indicador_id", "_anio"])
        .groupby("indicador_id", as_index=False)
        .tail(1)
        .drop(columns=["_anio"])
    )


def _indicator_ids_for_case(topic: str | None, news: pd.DataFrame) -> tuple[str, ...]:
    corpus = " ".join(
        _norm(x)
        for col in ("titulo",)
        if col in news.columns
        for x in news[col].dropna()
    )

    matched: list[str] = []
    for indicator_id, signals in INDICATOR_SIGNALS.items():
        if any(signal in corpus for signal in signals):
            matched.append(indicator_id)

    # Máximo dos indicadores específicos para evitar "rellenar" evidencia con
    # macrodatos poco relacionados.
    if matched:
        return tuple(matched[:2])

    return TOPIC_FALLBACK.get(topic or "", ())


def contextualize_case(
    topic: str | None,
    news: pd.DataFrame,
    indicators: pd.DataFrame,
) -> tuple[list[dict], list[str]]:
    if not topic:
        return [], ["No hay tema disponible para contextualizar."]

    allowed = _indicator_ids_for_case(topic, news)
    if not allowed:
        return [], [
            f"No se fuerza una relación con Banco Mundial para `{topic}`: "
            "el set obligatorio no ofrece un indicador suficientemente específico."
        ]

    if indicators.empty:
        return [], ["No hay indicadores de Panamá disponibles en el snapshot."]

    x = _latest_per_indicator(
        indicators[indicators["indicador_id"].isin(allowed)].copy()
    )

    out = []
    for _, row in x.iterrows():
        if pd.isna(row.get("valor")):
            continue
        indicator_id = str(row.get("indicador_id", ""))
        out.append(
            {
                "indicator_id": indicator_id,
                "indicator_label": INDICATOR_LABELS.get(
                    indicator_id, indicator_id
                ),
                "year": str(row.get("anio", "")),
                "value": str(row.get("valor", "")),
                "unit": str(row.get("unidad", "")),
                "source_url": str(row.get("fuente_url", "")),
                "license": str(row.get("licencia", "")),
                "scope_note": (
                    "Indicador macroeconómico anual usado únicamente como contexto. "
                    "No prueba causalidad ni describe necesariamente la situación actual."
                ),
            }
        )

    notes = [] if out else [
        "No hay valores utilizables para los indicadores pertinentes."
    ]
    return out, notes


# Compatibilidad temporal con código anterior y pruebas existentes.
# El Evidence Engine nuevo NO usa este wrapper; usa contextualize_case().
def contextualize_topic(
    topic: str | None,
    indicators: pd.DataFrame,
) -> tuple[list[dict], list[str]]:
    if not topic:
        return [], ["No hay tema disponible para contextualizar."]

    allowed = LEGACY_TOPIC_TO_INDICATORS.get(topic, ())
    if not allowed:
        return [], [
            f"No se fuerza una relación con Banco Mundial para `{topic}`: "
            "el set obligatorio no ofrece un indicador suficientemente específico."
        ]
    if indicators.empty:
        return [], ["No hay indicadores de Panamá disponibles en el snapshot."]

    x = _latest_per_indicator(
        indicators[indicators["indicador_id"].isin(allowed)].copy()
    )
    out = []
    for _, row in x.iterrows():
        if pd.isna(row.get("valor")):
            continue
        indicator_id = str(row.get("indicador_id", ""))
        out.append(
            {
                "indicator_id": indicator_id,
                "indicator_label": INDICATOR_LABELS.get(indicator_id, indicator_id),
                "year": str(row.get("anio", "")),
                "value": str(row.get("valor", "")),
                "unit": str(row.get("unidad", "")),
                "source_url": str(row.get("fuente_url", "")),
                "license": str(row.get("licencia", "")),
                "scope_note": (
                    "Indicador macroeconómico anual usado únicamente como contexto. "
                    "No prueba causalidad ni describe necesariamente la situación actual."
                ),
            }
        )
    notes = [] if out else [
        "No hay valores utilizables para los indicadores pertinentes."
    ]
    return out, notes
