from pathlib import Path
from app.core.settings import get_settings
from app.repositories.duckdb_repo import DuckDBRepository

if __name__ == "__main__":
    s = get_settings()
    repo = DuckDBRepository(s.database_path)

    candidates = [
        s.processed_news_csv,
        Path("data/processed/noticias_grouped_semantic.csv"),
        Path("data/processed/noticias_grouped_baseline.csv"),
    ]
    news_path = next((p for p in candidates if p.exists()), s.processed_news_csv)

    print("News source:", news_path)
    print(
        "Loaded:",
        repo.bootstrap_from_csv(news_path, s.indicators_csv),
    )
    print("Health:", repo.health())
