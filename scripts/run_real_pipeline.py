from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> None:
    cmd = [sys.executable, *args]
    print("\n$", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    # No vuelve a ejecutar la ingesta.
    run(
        "scripts/validate_snapshot.py",
        "--news", "data/snapshot/noticias.csv",
        "--indicators", "data/snapshot/indicadores.csv",
    )
    run("scripts/audit_real_corpus.py")
    run("scripts/classify_baseline.py")
    run("scripts/group_baseline.py")

    print(
        "\nPipeline determinístico completado. "
        "Siguiente paso: instalar requirements-semantic.txt y ejecutar "
        "scripts/prepare_embeddings.py."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
