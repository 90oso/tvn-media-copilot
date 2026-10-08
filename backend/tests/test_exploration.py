"""Pruebas de búsqueda verificable sin utilizar la red ni un LLM."""
import pandas as pd
from app.services.exploration import search_terms, explore_events


class StubRepo:
    def __init__(self):
        self.calls = {"news": 0, "indicators": 0, "reference": 0, "reviews": 0}

    def get_all_valid_news(self):
        self.calls["news"] += 1
        return pd.DataFrame([
            {"cluster_semantic": "C-1", "titulo": "Panamá registra más puestos de empleo", "medio": "Uno", "origen": "Uno", "id_noticia": "N1", "url": "https://example.org/1", "fecha_publicacion": "2026-09-10T10:00:00Z", "tema_baseline": "economía"},
            {"cluster_semantic": "C-2", "titulo": "Llegan nuevos visitantes de turismo", "medio": "Dos", "origen": "Dos", "id_noticia": "N2", "url": "https://example.org/2", "fecha_publicacion": "2026-09-11T10:00:00Z", "tema_baseline": "turismo"},
        ])

    def get_panama_indicators(self):
        self.calls["indicators"] += 1
        return pd.DataFrame()

    def get_snapshot_reference(self):
        self.calls["reference"] += 1
        return pd.Timestamp("2026-09-12T00:00:00Z")

    def get_all_reviews(self):
        self.calls["reviews"] += 1
        return {}


class StubSettings:
    evidence_rules_version = "test"
    ranking_rules_version = "test"


def test_spanish_question_retrieves_matching_event_and_batch_reads():
    repo = StubRepo()
    result = explore_events(repo, StubSettings(), question="¿Qué temas laborales requieren investigación en Panamá?")
    assert result["count"] == 1
    assert result["items"][0]["case_id"] == "C-1"
    assert "empleo" in result["items"][0]["headline"]
    assert all(n == 1 for n in repo.calls.values())
    assert result["search_mode"] == "lexical_metadata"


def test_no_results_abstains_without_generating_fake_answer():
    r = explore_events(StubRepo(), StubSettings(), question="fusión nuclear cuántica")
    assert r["abstained"] is True
    assert r["items"] == []
    assert "Sin coincidencias" in r["note"]


def test_topic_filter_and_limit():
    r = explore_events(StubRepo(), StubSettings(), topic="turismo", limit=1)
    assert r["count"] == 1
    assert r["items"][0]["case_id"] == "C-2"


def test_accent_normalization():
    assert "econom" in search_terms("¿Qué temas económicos sobre Panamá?")
    assert "inflacion" in search_terms("inflación")


def test_editorial_top_five_question_returns_ranked_agenda():
    r = explore_events(StubRepo(), StubSettings(), question="¿Qué cinco temas merecen revisión para la agenda de Panamá y por qué?")
    assert r["abstained"] is False
    assert r["search_mode"] == "editorial_agenda"
    assert r["count"] == 2
    assert r["items"][0]["attention"]["score"] >= r["items"][1]["attention"]["score"]


def test_detection_date_is_not_reported_as_publication():
    from app.services.agenda import _preview
    frame = pd.DataFrame([{
        "titulo": "Una noticia detectada", "medio": "Fuente",
        "fecha_publicacion": None, "fecha_deteccion": "2026-09-10T10:00:00Z",
    }])
    metadata = _preview(frame)
    assert metadata["date_origin"] == "detección"
    assert metadata["headline"] == "Una noticia detectada"


def test_http_explore_route_exposes_traceable_search(monkeypatch):
    from pathlib import Path
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.routes import explore as explore_route

    monkeypatch.setattr(explore_route, "get_settings", lambda: type(
        "Settings", (), {
            "database_path": Path("no-database-needed.duckdb"),
            "evidence_rules_version": "test",
            "ranking_rules_version": "test",
        },
    )())
    monkeypatch.setattr(explore_route, "DuckDBRepository", lambda _: StubRepo())
    client = TestClient(app)
    response = client.get("/explore", params={"q": "empleo", "limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["items"][0]["headline"].startswith("Panamá")
    assert data["items"][0]["date_origin"] == "publicación"


def test_filter_language_does_not_erase_foreign_snapshot():
    """La vista es lingüística; no altera el conjunto histórico original."""
    from app.services.exploration_language import spanish_only, case_languages
    class MultilingualRepo(StubRepo):
        def get_all_valid_news(self):
            frame = super().get_all_valid_news()
            frame["idioma"] = "es"
            return pd.concat([frame, pd.DataFrame([{
                "cluster_semantic": "C-RU", "titulo": "Новости о Панаме",
                "idioma": "ru", "medio": "Noticias RU", "origen": "GDELT",
                "id_noticia": "NRU", "url": "https://example.org/ru",
                "fecha_publicacion": "2026-09-09T10:00:00Z",
                "tema_baseline": "economía",
            }])], ignore_index=True)
    repo = MultilingualRepo()
    before = repo.get_all_valid_news()
    assert len(spanish_only(before)) == 2
    assert len(before) == 3
    assert case_languages(before) == ["es", "ru"]
    result_es = explore_events(repo, StubSettings(), topic="economía", language="es")
    assert result_es["count"] == 1
    result_all = explore_events(repo, StubSettings(), topic="economía", language="all")
    assert result_all["count"] == 2


def test_cyrillic_title_not_visible_in_spanish_view_even_when_mislabeled():
    from app.services.exploration_language import spanish_only
    frame = pd.DataFrame([{"titulo": "Новости сегодня", "idioma": "es"}])
    assert spanish_only(frame).empty


def test_agenda_language_filter_is_opt_in_and_backward_compatible():
    from app.services.agenda import build_agenda

    class MixedRepo(StubRepo):
        def get_all_valid_news(self):
            frame = super().get_all_valid_news()
            frame["idioma"] = "es"
            foreign = pd.DataFrame([{
                "cluster_semantic": "C-RU", "titulo": "Новости о Панаме",
                "idioma": "ru", "medio": "Ejemplo", "origen": "Ejemplo",
                "id_noticia": "N-RU", "url": "https://example.org/foreign",
                "fecha_publicacion": "2026-09-10T10:00:00Z", "tema_baseline": "economía",
            }])
            return pd.concat([frame, foreign], ignore_index=True)

    all_cases = build_agenda(MixedRepo(), StubSettings(), limit=10)
    spanish_cases = build_agenda(MixedRepo(), StubSettings(), limit=10, language="es")
    assert len(all_cases) == 3
    assert len(spanish_cases) == 2
    assert all(item["headline"] and "Новости" not in item["headline"] for item in spanish_cases)
