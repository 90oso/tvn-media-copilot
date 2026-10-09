"""Protección opcional de escrituras editoriales y de la cuota de Gemini."""
import hmac
import os
from fastapi import HTTPException


def require_editor_access(token: str | None) -> None:
    expected = os.environ.get("EDITOR_ACCESS_TOKEN", "").strip()
    if expected and not hmac.compare_digest(expected, token or ""):
        raise HTTPException(401, detail="Clave de edición requerida o incorrecta.")
