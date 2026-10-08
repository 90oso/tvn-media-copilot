from __future__ import annotations

import subprocess
import sys


CASES = [
    (
        "A · torch primero",
        "import torch; import pandas; import numpy; "
        "from sentence_transformers import SentenceTransformer; "
        "print('OK torch-first', torch.__version__)",
    ),
    (
        "B · pandas/numpy primero",
        "import pandas; import numpy; import torch; "
        "from sentence_transformers import SentenceTransformer; "
        "print('OK pandas-first', torch.__version__)",
    ),
]


def main() -> int:
    print("=== Diagnóstico de orden de importación PyTorch / Windows ===")
    print("Python:", sys.executable)

    failures = 0
    for label, code in CASES:
        print(f"\n--- {label} ---")
        proc = subprocess.run(
            [sys.executable, "-c", code],
            text=True,
            capture_output=True,
        )
        print("exit:", proc.returncode)
        if proc.stdout:
            print(proc.stdout.strip())
        if proc.stderr:
            print(proc.stderr.strip())
        if proc.returncode != 0:
            failures += 1

    if failures == 0:
        print("\nAmbos órdenes funcionan.")
    elif failures == 1:
        print(
            "\nHay un conflicto dependiente del orden de carga de DLL. "
            "La v0.6.4 precarga torch antes de pandas/numpy."
        )
    else:
        print(
            "\nPyTorch falla en ambos órdenes. En ese caso revisa Visual C++ "
            "Redistributable x64 o crea una venv limpia."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
