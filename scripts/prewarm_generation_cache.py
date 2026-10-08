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
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    agenda = requests.get(
        f"{base}/agenda",
        params={"limit": args.limit},
        timeout=30,
    )
    agenda.raise_for_status()
    items = agenda.json()["items"]

    eligible = [
        item
        for item in items
        if item.get("workflow", {}).get("draft_enabled")
    ]

    print("=== Prewarm de borradores editoriales ===")
    print(f"Agenda consultada: {len(items)}")
    print(f"Casos elegibles: {len(eligible)}")

    failures = 0
    generated = 0

    for item in eligible:
        case_id = item["case_id"]
        for mode in ("brief", "script", "digital"):
            print(f"\n{case_id} · {mode}")
            response = requests.post(
                f"{base}/generate/{case_id}",
                params={"mode": mode},
                timeout=180,
            )
            if response.ok:
                body = response.json()
                print(
                    "OK | modelo="
                    f"{body.get('model')} | "
                    f"cached={body.get('cached')} | "
                    f"attempts={body.get('attempts')}"
                )
                generated += 1
            else:
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
