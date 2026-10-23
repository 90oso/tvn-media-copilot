from fastapi.testclient import TestClient
from app.main import app


def test_research_rejects_invalid_date_range():
    response = TestClient(app).post("/research/investigate", json={
        "objective": "Analizar señales del mercado laboral",
        "date_from": "2026-10-10",
        "date_to": "2026-10-01",
    })
    assert response.status_code == 422


def test_research_rejects_unbounded_objective():
    response = TestClient(app).post("/research/investigate", json={
        "objective": "a" * 241,
    })
    assert response.status_code == 422
