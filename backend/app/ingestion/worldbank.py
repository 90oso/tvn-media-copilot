from __future__ import annotations

from itertools import product
from pathlib import Path

import pandas as pd

from .common import build_http_session, utc_now_iso


COUNTRIES = ("PAN", "CRI", "COL", "DOM", "MEX", "GTM")

INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "porcentaje",
    "FP.CPI.TOTL.ZG": "porcentaje",
    "SL.UEM.TOTL.ZS": "porcentaje",
    "SP.POP.TOTL": "personas",
    "IT.NET.USER.ZS": "porcentaje",
    "NE.EXP.GNFS.ZS": "porcentaje del PIB",
}


def collect_worldbank(
    base_url: str,
    user_agent: str,
    start_year: int = 2010,
    end_year: int = 2024,
    timeout: int = 45,
) -> tuple[list[dict], list[dict], list[str]]:
    session = build_http_session(user_agent)
    extraction = utc_now_iso()

    observed: dict[tuple[str, str, int], dict] = {}
    query_log: list[dict] = []
    warnings: list[str] = []

    for country in COUNTRIES:
        for indicator, unit in INDICATORS.items():
            url = f"{base_url.rstrip('/')}/country/{country}/indicator/{indicator}"
            params = {
                "date": f"{start_year}:{end_year}",
                "format": "json",
                "per_page": 1000,
            }
            response = session.get(url, params=params, timeout=timeout)
            query_log.append(
                {
                    "country": country,
                    "indicator": indicator,
                    "status_code": response.status_code,
                    "url": response.url,
                }
            )

            if response.status_code != 200:
                warnings.append(
                    f"Banco Mundial {country}/{indicator}: HTTP {response.status_code}"
                )
                continue

            payload = response.json()
            records = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
            for item in records or []:
                try:
                    year = int(item.get("date"))
                except (TypeError, ValueError):
                    continue
                if not start_year <= year <= end_year:
                    continue
                observed[(country, indicator, year)] = {
                    "pais_iso3": country,
                    "indicador_id": indicator,
                    "anio": year,
                    "valor": item.get("value"),
                    "unidad": unit,
                    "fuente_url": response.url,
                    "fecha_extraccion": extraction,
                    "licencia": "CC BY 4.0; revisar excepciones de terceros",
                }

    # Completa explícitamente la cuadrícula y conserva nulos.
    rows: list[dict] = []
    years = range(start_year, end_year + 1)
    for country, indicator, year in product(COUNTRIES, INDICATORS.keys(), years):
        row = observed.get((country, indicator, year))
        if row is None:
            row = {
                "pais_iso3": country,
                "indicador_id": indicator,
                "anio": year,
                "valor": None,
                "unidad": INDICATORS[indicator],
                "fuente_url": (
                    f"{base_url.rstrip('/')}/country/{country}/indicator/{indicator}"
                    f"?date={start_year}:{end_year}&format=json"
                ),
                "fecha_extraccion": extraction,
                "licencia": "CC BY 4.0; revisar excepciones de terceros",
            }
        rows.append(row)

    # El documento enumera 6×6×15 = 540 combinaciones pero también declara 1,350.
    enumerated_grid = len(COUNTRIES) * len(INDICATORS) * len(list(years))
    if enumerated_grid != 1350:
        warnings.append(
            "Discrepancia documental: 6 países × 6 indicadores × 15 años = "
            f"{enumerated_grid}, mientras el documento declara 1,350 combinaciones. "
            "El collector sigue las dimensiones enumeradas y conserva esta advertencia."
        )

    return rows, query_log, warnings
