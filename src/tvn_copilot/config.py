from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    app_env: str
    app_rules_version: str
    tz_display: str
    news_csv: Path
    indicators_csv: Path
    processed_dir: Path
    report_dir: Path


def get_settings(env_file: str | None = ".env") -> Settings:
    if env_file and Path(env_file).exists():
        load_dotenv(env_file)
    else:
        load_dotenv()

    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        app_rules_version=os.getenv("APP_RULES_VERSION", "media-mvp-v0.1"),
        tz_display=os.getenv("TZ_DISPLAY", "America/Panama"),
        news_csv=Path(os.getenv("NEWS_CSV", "data/sample/noticias.csv")),
        indicators_csv=Path(os.getenv("INDICATORS_CSV", "data/sample/indicadores.csv")),
        processed_dir=Path(os.getenv("PROCESSED_DIR", "data/processed")),
        report_dir=Path(os.getenv("REPORT_DIR", "reports/data_quality")),
    )
