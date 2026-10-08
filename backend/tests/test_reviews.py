from pathlib import Path

from app.repositories.duckdb_repo import DuckDBRepository

def test_review_roundtrip(tmp_path: Path):
    repo = DuckDBRepository(tmp_path / "test.db")
    saved = repo.save_review(
        "C1", "correct", "en revisión", "editor", "Verificar fuente", "2026-10-07T00:00:00+00:00"
    )
    assert saved["case_id"] == "C1"
    assert saved["state"] == "en revisión"
    loaded = repo.get_review("C1")
    assert loaded is not None
    assert loaded["note"] == "Verificar fuente"
