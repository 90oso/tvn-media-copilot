"""Arranque del backend alojado: no permite demos vacías por falta de CSVs."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from app.core.settings import get_settings
from app.repositories.duckdb_repo import DuckDBRepository


def main() -> None:
    settings = get_settings()
    candidates = (
        settings.processed_news_csv,
        Path("data/processed/noticias_grouped_semantic.csv"),
        Path("data/processed/noticias_grouped_baseline.csv"),
    )
    news_path = next((p for p in candidates if p.is_file()), None)
    if news_path is None:
        raise SystemExit(
            "DEPLOY ERROR: no hay noticias procesadas. Adjunta únicamente los CSV "
            "públicos permitidos (noticias_grouped_semantic.csv y "
            "indicadores_validated.csv) al repositorio."
        )
    if not settings.indicators_csv.is_file():
        raise SystemExit(
            f"DEPLOY ERROR: no existe archivo Banco Mundial: {settings.indicators_csv}"
        )

    repo = DuckDBRepository(settings.database_path)
    result = repo.bootstrap_from_csv(news_path, settings.indicators_csv)
    print("Hosted data bootstrap:", result, "source:", str(news_path), flush=True)
    if int(result.get("noticias", 0)) < 100 or int(result.get("indicadores", 0)) < 100:
        raise SystemExit(
            "DEPLOY ERROR: dataset insuficiente para demo real. "
            "No publicamos el fixture sintético por accidente."
        )

    # Render inyecta PORT; usar un único worker mantiene el archivo DuckDB local.
    port = os.environ.get("PORT", "10000")
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port],
        check=True,
    )


if __name__ == "__main__":
    main()
