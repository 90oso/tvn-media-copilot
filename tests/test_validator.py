\
from pathlib import Path

import pandas as pd

from tvn_copilot.validator import validate_news, validate_indicators


def test_t01_news_invalid_date_and_null_do_not_block(tmp_path: Path):
    path = tmp_path / "noticias.csv"
    pd.DataFrame(
        [
            {
                "id_noticia": "N1",
                "titulo": "Registro válido",
                "url": "https://example.org/1",
                "medio": "Demo",
                "idioma": "es",
                "fecha_publicacion": "2026-10-01T10:00:00Z",
                "fecha_deteccion": "2026-10-01T10:01:00Z",
                "fecha_extraccion": "2026-10-01T12:00:00Z",
                "tema": "economía",
                "origen": "demo",
                "alcance_texto": "titular/metadatos",
            },
            {
                "id_noticia": "N2",
                "titulo": None,
                "url": "https://example.org/2",
                "medio": "Demo",
                "idioma": "es",
                "fecha_publicacion": "NO_ES_FECHA",
                "fecha_deteccion": "2026-10-01T11:01:00Z",
                "fecha_extraccion": "2026-10-01T12:00:00Z",
                "tema": "economía",
                "origen": "demo",
                "alcance_texto": "titular/metadatos",
            },
        ]
    ).to_csv(path, index=False)

    result = validate_news(path)

    assert result.summary["rows_loaded"] == 2
    assert len(result.dataframe) == 2
    assert result.summary["rows_with_errors"] == 1
    errors = result.dataframe.iloc[1]["_validation_errors"]
    assert "null:titulo" in errors
    assert "invalid_date:fecha_publicacion" in errors


def test_indicator_value_null_is_allowed_by_contract(tmp_path: Path):
    path = tmp_path / "indicadores.csv"
    pd.DataFrame(
        [
            {
                "pais_iso3": "PAN",
                "indicador_id": "TEST",
                "anio": "2024",
                "valor": None,
                "unidad": "porcentaje",
                "fuente_url": "https://example.org/data",
                "fecha_extraccion": "2026-10-01T12:00:00Z",
                "licencia": "demo",
            }
        ]
    ).to_csv(path, index=False)

    result = validate_indicators(path)

    assert result.summary["rows_loaded"] == 1
    assert result.summary["rows_with_issues"] == 0
    assert pd.isna(result.dataframe.iloc[0]["valor"])


def test_gdelt_missing_publication_is_warning_not_error(tmp_path: Path):
    path = tmp_path / "noticias.csv"
    pd.DataFrame(
        [
            {
                "id_noticia": "G1",
                "titulo": "Registro GDELT",
                "url": "https://example.org/g1",
                "medio": "example.org",
                "idioma": "Spanish",
                "fecha_publicacion": None,
                "fecha_deteccion": "2026-09-30T10:00:00Z",
                "fecha_extraccion": "2026-10-01T12:00:00Z",
                "tema": "sin_clasificar",
                "origen": "example.org",
                "alcance_texto": "titular/metadatos",
            }
        ]
    ).to_csv(path, index=False)

    result = validate_news(path)

    assert result.summary["rows_with_errors"] == 0
    assert result.summary["rows_with_warnings"] == 1
    assert result.summary["rows_usable"] == 1
    assert result.dataframe.iloc[0]["_validation_status"] == "warning"
    assert (
        "missing_publication_date:fecha_publicacion"
        in result.dataframe.iloc[0]["_validation_warnings"]
    )
