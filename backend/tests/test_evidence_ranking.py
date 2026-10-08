import pandas as pd

from app.services.evidence_engine import build_evidence_package
from app.services.ranking import propose_components
from app.services.contextualization import contextualize_case
from app.services.topic_analysis import _workflow


def news():
    return pd.DataFrame(
        [
            {
                "id_noticia": "N1",
                "titulo": "Panamá registra cambios en actividad económica",
                "url": "https://example.org/1",
                "medio": "A",
                "origen": "Fuente A",
                "fecha_publicacion": "2026-09-10T10:00:00Z",
                "tema_baseline": "economía",
                "alcance_texto": "titular/metadatos",
            },
            {
                "id_noticia": "N2",
                "titulo": "Economía panameña registra nueva variación",
                "url": "https://example.org/2",
                "medio": "B",
                "origen": "Fuente B",
                "fecha_publicacion": "2026-09-10T11:00:00Z",
                "tema_baseline": "economía",
                "alcance_texto": "titular/metadatos",
            },
        ]
    )


def inds():
    return pd.DataFrame(
        [
            {
                "indicador_id": "NY.GDP.MKTP.KD.ZG",
                "anio": "2024",
                "valor": "2.7",
                "unidad": "porcentaje",
                "fuente_url": "https://example.org/wb/gdp",
                "licencia": "CC BY 4.0",
            },
            {
                "indicador_id": "FP.CPI.TOTL.ZG",
                "anio": "2024",
                "valor": "1.5",
                "unidad": "porcentaje",
                "fuente_url": "https://example.org/wb/cpi",
                "licencia": "CC BY 4.0",
            },
            {
                "indicador_id": "SL.UEM.TOTL.ZS",
                "anio": "2024",
                "valor": "8.4",
                "unidad": "porcentaje",
                "fuente_url": "https://example.org/wb/unemployment",
                "licencia": "CC BY 4.0",
            },
            {
                "indicador_id": "NE.EXP.GNFS.ZS",
                "anio": "2024",
                "valor": "44.3",
                "unidad": "porcentaje del PIB",
                "fuente_url": "https://example.org/wb/exports",
                "licencia": "CC BY 4.0",
            },
        ]
    )


def test_package_traceable():
    package = build_evidence_package("C1", news(), inds(), "v")
    assert package.independent_provenances == 2
    assert any(
        item.source_type == "official_indicator"
        for item in package.evidence
    )
    assert package.evidence_state == "suficiente para el borrador"


def test_formula():
    package = build_evidence_package("C1", news(), inds(), "v")
    components = propose_components(news(), package)
    assert components.total == round(
        30 * components.relevance
        + 25 * components.impact
        + 20 * components.urgency
        + 15 * components.novelty
        + 10 * components.evidence,
        2,
    )


def test_one_source_without_official_context_is_insufficient():
    n = news().iloc[:1].copy()
    n["tema_baseline"] = "eventos naturales"
    package = build_evidence_package("C2", n, pd.DataFrame(), "v")
    assert package.evidence_state == "insuficiente"


def test_unemployment_title_selects_only_unemployment_indicator():
    n = pd.DataFrame(
        [
            {
                "titulo": (
                    "Creación de más plazas en la empresa privada "
                    "hace bajar el desempleo"
                )
            }
        ]
    )
    contexts, _ = contextualize_case("economía", n, inds())
    assert [x["indicator_id"] for x in contexts] == ["SL.UEM.TOTL.ZS"]


def test_high_attention_does_not_enable_draft_when_evidence_is_partial():
    state = _workflow("parcial")
    assert state["state"] == "requiere evidencia"
    assert state["draft_enabled"] is False
    assert state["publication_enabled"] is False


def test_sufficient_evidence_still_requires_human_review():
    state = _workflow("suficiente para el borrador")
    assert state["state"] == "en revisión"
    assert state["draft_enabled"] is True
    assert state["publication_enabled"] is False


def test_potential_contradiction_is_exposed_not_resolved():
    n = pd.DataFrame(
        [
            {
                "id_noticia": "A",
                "titulo": "Comisión recomienda reactivar la mina de cobre en Panamá",
                "url": "https://example.org/a",
                "medio": "A",
                "origen": "Fuente A",
                "fecha_publicacion": "2026-09-10T10:00:00Z",
                "tema_baseline": "economía",
                "alcance_texto": "titular/metadatos",
            },
            {
                "id_noticia": "B",
                "titulo": "Comisión recomienda cierre de la mina de cobre en Panamá",
                "url": "https://example.org/b",
                "medio": "B",
                "origen": "Fuente B",
                "fecha_publicacion": "2026-09-10T11:00:00Z",
                "tema_baseline": "economía",
                "alcance_texto": "titular/metadatos",
            },
        ]
    )

    p = build_evidence_package("C3", n, inds(), "v")
    assert len(p.contradictions) >= 1
    assert "No se determina cuál versión es correcta" in p.contradictions[0]
