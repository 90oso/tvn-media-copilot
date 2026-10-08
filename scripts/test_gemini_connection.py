from __future__ import annotations

from pathlib import Path
import os
import sys

import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

api_key = os.getenv("GEMINI_API_KEY", "").strip()
model = os.getenv("GEMINI_MODEL", "").strip()
base_url = os.getenv(
    "GEMINI_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta",
).rstrip("/")
timeout = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))

print("=== Diagnóstico Gemini ===")
print("Modelo:", model or "<vacío>")
print("Base URL:", base_url)
print("API key:", "configurada" if api_key else "NO configurada")

if not api_key:
    print("ERROR: falta GEMINI_API_KEY en .env")
    raise SystemExit(2)

if not model:
    print("ERROR: falta GEMINI_MODEL en .env")
    raise SystemExit(3)

url = f"{base_url}/models/{model}:generateContent"
payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": (
                        "Responde únicamente con la palabra OK. "
                        "Esta es una prueba de conectividad."
                    )
                }
            ]
        }
    ]
}

try:
    response = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        json=payload,
        timeout=timeout,
    )
except requests.Timeout:
    print(f"ERROR: timeout después de {timeout}s")
    raise SystemExit(4)
except requests.ConnectionError as exc:
    print("ERROR DE CONEXIÓN:", exc)
    raise SystemExit(5)
except requests.RequestException as exc:
    print("ERROR HTTP/TRANSPORTE:", type(exc).__name__, exc)
    raise SystemExit(6)

print("HTTP:", response.status_code)

try:
    body = response.json()
except ValueError:
    print("Respuesta no JSON:")
    print((response.text or "")[:1000])
    raise SystemExit(7)

if not response.ok:
    err = body.get("error", {}) if isinstance(body, dict) else {}
    print("Estado Gemini:", err.get("status"))
    print("Mensaje:", err.get("message"))
    if response.status_code == 503:
        print("Nota: 503 UNAVAILABLE es un error transitorio del proveedor; reintenta más tarde o usa backoff.")
    raise SystemExit(8)

try:
    text = body["candidates"][0]["content"]["parts"][0]["text"]
except Exception:
    print("Respuesta recibida, pero sin texto esperado:")
    print(body)
    raise SystemExit(9)

print("Respuesta:", text.strip())
print("Gemini: OK")
