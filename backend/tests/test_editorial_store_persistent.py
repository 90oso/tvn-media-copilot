"""Pruebas autocontenidas del almacén editorial (sin red ni credenciales)."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.repositories.editorial_store import EditorialStore
from app.core.editor_auth import require_editor_access
from fastapi import HTTPException
import pytest


def test_reviews_survive_restart_and_update(tmp_path):
    url = 'sqlite:///' + str(tmp_path / 'editorial.sqlite3')
    store = EditorialStore(url)
    assert store.get_review('C-1') is None
    assert store.save_review('C-1', 'approve', 'aprobado como borrador', 'Editor', 'Verificado', '2026-10-08')['action'] == 'approve'
    store2 = EditorialStore(url)
    assert store2.get_review('C-1')['state'] == 'aprobado como borrador'
    store2.save_review('C-1', 'correct', 'en revisión', 'Editor', 'Corregir cifra', '2026-10-09')
    assert len(store.all_reviews()) == 1
    assert store.get_review('C-1')['note'] == 'Corregir cifra'


def test_draft_requires_case_mode_and_fingerprint(tmp_path):
    url = 'sqlite:///' + str(tmp_path / 'editorial.sqlite3')
    store = EditorialStore(url)
    store.save_draft('C-1', 'brief', 'huella-A', {'text': 'Texto sin publicar', 'mode': 'brief'})
    other = EditorialStore(url)
    assert other.get_draft('C-1', 'brief', 'huella-A')['text'] == 'Texto sin publicar'
    assert other.get_draft('C-1', 'brief', 'huella-B') is None
    assert other.get_draft('C-2', 'brief', 'huella-A') is None
    assert other.get_draft('C-1', 'digital', 'huella-A') is None


def test_editor_key_optional_and_guarded(monkeypatch):
    monkeypatch.delenv('EDITOR_ACCESS_TOKEN', raising=False)
    require_editor_access(None)
    monkeypatch.setenv('EDITOR_ACCESS_TOKEN', 'demo-secret')
    with pytest.raises(HTTPException) as e:
        require_editor_access(None)
    assert e.value.status_code == 401
    with pytest.raises(HTTPException):
        require_editor_access('wrong')
    require_editor_access('demo-secret')
