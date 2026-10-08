from __future__ import annotations

import platform
import sys
import traceback


print("=== Diagnóstico entorno semántico ===")
print("Python:", sys.version.replace("\n", " "))
print("Executable:", sys.executable)
print("Platform:", platform.platform())
print("Architecture:", platform.architecture())

try:
    import torch
    print("torch:", torch.__version__)
    print("torch file:", torch.__file__)
    print("CUDA available:", torch.cuda.is_available())
    print("Tensor test:", torch.tensor([1.0, 2.0]).sum().item())
except Exception as exc:
    print("\nTORCH ERROR:")
    print(type(exc).__name__ + ":", exc)
    raise SystemExit(2)

try:
    import sentence_transformers
    from sentence_transformers import SentenceTransformer
    print("\nsentence-transformers:", sentence_transformers.__version__)
    print("SentenceTransformer import: OK")
except Exception as exc:
    print("\nSENTENCE-TRANSFORMERS ERROR:")
    print(type(exc).__name__ + ":", exc)
    raise SystemExit(3)

print("\nEntorno semántico: OK")
