import json

import pytest
import requests

from app.core.settings import Settings
from app.schemas.evidence import EvidencePackage, EvidenceItem
from app.services.llm_provider import (
    GeminiProvider,
    build_llm_provider,
)


def _package():
    return EvidencePackage(
        case_id="C1",
        topic="economía",
        news_ids=["N1"],
        evidence=[
            EvidenceItem(
                evidence_id="NEWS-1",
                source_type="news",
                source_name="Fuente",
                field="titulo",
                value="Panamá registra un cambio económico",
                url="https://example.org/1",
            )
        ],
        evidence_state="suficiente para el borrador",
        independent_provenances=2,
        rules_version="test",
    )


def _settings():
    return Settings(
        llm_provider="gemini",
        gemini_api_key="secret-test-key",
        gemini_model="gemini-3.8-flash",
        request_timeout_seconds=5,
    )


def test_ollama_disabled():
    with pytest.raises(RuntimeError):
        build_llm_provider(Settings(llm_provider="ollama"))


def test_gemini_http_error_becomes_runtime_error(monkeypatch):
    response = requests.Response()
    response.status_code = 429
    response._content = json.dumps(
        {
            "error": {
                "code": 429,
                "message": "Quota exceeded",
                "status": "RESOURCE_EXHAUSTED",
            }
        }
    ).encode("utf-8")

    monkeypatch.setattr(
        "app.services.llm_provider.requests.post",
        lambda *args, **kwargs: response,
    )

    with pytest.raises(RuntimeError) as exc:
        GeminiProvider(_settings()).generate_from_evidence(
            "Genera un brief.",
            _package(),
        )

    message = str(exc.value)
    assert "429" in message
    assert "Quota exceeded" in message
    assert "secret-test-key" not in message


def test_gemini_success_joins_text_parts(monkeypatch):
    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Parte uno. "},
                            {"text": "Parte dos."},
                        ]
                    }
                }
            ]
        }
    ).encode("utf-8")

    monkeypatch.setattr(
        "app.services.llm_provider.requests.post",
        lambda *args, **kwargs: response,
    )

    result = GeminiProvider(_settings()).generate_from_evidence(
        "Genera un brief.",
        _package(),
    )

    assert result.text == "Parte uno. Parte dos."
    assert result.provider == "gemini"


def test_gemini_retries_503_then_succeeds(monkeypatch):
    responses = []

    for status, body in [
        (
            503,
            {
                "error": {
                    "code": 503,
                    "message": "High demand",
                    "status": "UNAVAILABLE",
                }
            },
        ),
        (
            200,
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "OK después del reintento"}]
                        }
                    }
                ]
            },
        ),
    ]:
        response = requests.Response()
        response.status_code = status
        response._content = json.dumps(body).encode("utf-8")
        responses.append(response)

    calls = {"n": 0}

    def fake_post(*args, **kwargs):
        idx = calls["n"]
        calls["n"] += 1
        return responses[idx]

    monkeypatch.setattr(
        "app.services.llm_provider.requests.post",
        fake_post,
    )
    monkeypatch.setattr(
        "app.services.llm_provider.time.sleep",
        lambda *_: None,
    )
    monkeypatch.setattr(
        "app.services.llm_provider.random.uniform",
        lambda *_: 0.0,
    )

    settings = _settings().model_copy(
        update={
            "gemini_max_retries": 3,
            "gemini_retry_base_seconds": 0.1,
        }
    )

    result = GeminiProvider(settings).generate_from_evidence(
        "Genera un brief.",
        _package(),
    )

    assert result.text == "OK después del reintento"
    assert result.attempts == 2
    assert calls["n"] == 2


def test_gemini_does_not_retry_403(monkeypatch):
    response = requests.Response()
    response.status_code = 403
    response._content = json.dumps(
        {
            "error": {
                "code": 403,
                "message": "Permission denied",
                "status": "PERMISSION_DENIED",
            }
        }
    ).encode("utf-8")

    calls = {"n": 0}

    def fake_post(*args, **kwargs):
        calls["n"] += 1
        return response

    monkeypatch.setattr(
        "app.services.llm_provider.requests.post",
        fake_post,
    )

    settings = _settings().model_copy(update={"gemini_max_retries": 4})

    with pytest.raises(RuntimeError):
        GeminiProvider(settings).generate_from_evidence(
            "Genera un brief.",
            _package(),
        )

    assert calls["n"] == 1


def test_gemini_json_generation_parses_object(monkeypatch):
    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "proposed_title": "Título",
                                        "public_interest": "Interés",
                                    }
                                )
                            }
                        ]
                    }
                }
            ]
        }
    ).encode("utf-8")

    monkeypatch.setattr(
        "app.services.llm_provider.requests.post",
        lambda *args, **kwargs: response,
    )

    result = GeminiProvider(_settings()).generate_json_from_evidence(
        "Devuelve JSON.",
        _package(),
    )
    assert result.data["proposed_title"] == "Título"
