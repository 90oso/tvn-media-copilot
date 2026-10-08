from __future__ import annotations

import argparse
import json

import requests


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Genera y congela las tres modalidades para casos elegibles "
            "de la agenda. Requiere FastAPI ejecutándose."
        )
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--agenda-timeout",
        type=int,
        default=120,
        help="Timeout de lectura para /agenda, en segundos.",
    )
    parser.add_argument(
        "--generation-timeout",
        type=int,
        default=420,
        help=(
            "Timeout por modalidad. Debe permitir los reintentos internos "
            "de Gemini."
        ),
    )
    args = parser.parse_args()

    base = args.base_url.rstrip("/")

    print("=== Prewarm de borradores editoriales ===")
    print(f"API: {base}")
    print(f"Top solicitado: {args.limit}")

    try:
        agenda = requests.get(
            f"{base}/agenda",
            params={"limit": args.limit},
            timeout=(5, args.agenda_timeout),
        )
        agenda.raise_for_status()
    except requests.Timeout:
        print(
            "ERROR: /agenda agotó el tiempo de espera. "
            "Verifica que FastAPI tenga aplicado el parche v0.9.1 "
            "de agenda batch."
        )
        return 2
    except requests.RequestException as exc:
        print(f"ERROR consultando /agenda: {exc}")
        return 3

    items = agenda.json()["items"]

    eligible = [
        item
        for item in items
        if item.get("workflow", {}).get("draft_enabled")
    ]

    print(f"Agenda consultada: {len(items)}")
    print(f"Casos elegibles: {len(eligible)}")

    if not eligible:
        print(
            "No hay casos del Top solicitado con evidencia suficiente "
            "para generar borradores."
        )
        return 0

    failures = 0
    generated = 0

    with requests.Session() as session:
        for item in eligible:
            case_id = item["case_id"]

            for mode in ("brief", "script", "digital"):
                print(f"\n{case_id} · {mode}")

                try:
                    response = session.post(
                        f"{base}/generate/{case_id}",
                        params={"mode": mode},
                        timeout=(5, args.generation_timeout),
                    )
                except requests.Timeout:
                    failures += 1
                    print(
                        "ERROR timeout: el backend no respondió dentro de "
                        f"{args.generation_timeout}s."
                    )
                    continue
                except requests.RequestException as exc:
                    failures += 1
                    print(f"ERROR de conexión: {exc}")
                    continue

                if response.ok:
                    body = response.json()
                    print(
                        "OK | modelo="
                        f"{body.get('model')} | "
                        f"cached={body.get('cached')} | "
                        f"attempts={body.get('attempts')}"
                    )
                    generated += 1
                    continue

                failures += 1
                try:
                    print(
                        "ERROR",
                        response.status_code,
                        json.dumps(
                            response.json(),
                            ensure_ascii=False,
                        ),
                    )
                except Exception:
                    print(
                        "ERROR",
                        response.status_code,
                        response.text[:500],
                    )

    print("")
    print(f"Borradores preparados: {generated}")
    print(f"Fallos: {failures}")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
