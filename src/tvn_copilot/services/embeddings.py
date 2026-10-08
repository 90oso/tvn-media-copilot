from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import hashlib
import json

import numpy as np
import pandas as pd


class EmbeddingProvider(Protocol):
    """Contrato mínimo para cualquier proveedor de embeddings semánticos."""

    @property
    def model_name(self) -> str:
        ...

    def encode(self, texts: list[str]) -> np.ndarray:
        ...


@dataclass(frozen=True)
class EmbeddingArtifact:
    vectors_path: Path
    metadata_path: Path
    count: int
    dimensions: int
    model_name: str


def build_semantic_text(df: pd.DataFrame) -> pd.Series:
    """Construye el texto a vectorizar sin inventar contenido.

    Con el contrato actual se usa únicamente `titulo`.
    Si en una versión futura existe una descripción permitida, debe incorporarse
    explícitamente y documentarse como cambio.
    """
    if "titulo" not in df.columns:
        raise ValueError("Falta la columna `titulo` para preparar embeddings.")
    return df["titulo"].fillna("").astype(str).str.strip()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save_embeddings(
    df: pd.DataFrame,
    provider: EmbeddingProvider,
    output_dir: Path,
    source_path: Path | None = None,
) -> EmbeddingArtifact:
    """Genera y congela embeddings para una demo reproducible/offline.

    El proveedor se inyecta: puede ser local o remoto. La app de demo debe leer
    los artefactos guardados en lugar de depender de una llamada en vivo.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if "id_noticia" not in df.columns:
        raise ValueError("Falta `id_noticia` para mapear embeddings.")

    texts = build_semantic_text(df).tolist()
    vectors = np.asarray(provider.encode(texts), dtype=np.float32)

    if vectors.ndim != 2:
        raise ValueError("El proveedor debe devolver una matriz 2D [filas, dimensiones].")
    if vectors.shape[0] != len(df):
        raise ValueError(
            "Cantidad de embeddings distinta a la cantidad de noticias."
        )

    ids = df["id_noticia"].fillna("").astype(str).to_numpy(dtype=str)
    vectors_path = output_dir / "news_embeddings.npz"
    np.savez_compressed(vectors_path, ids=ids, vectors=vectors)

    metadata = {
        "model_name": provider.model_name,
        "count": int(vectors.shape[0]),
        "dimensions": int(vectors.shape[1]),
        "source_path": str(source_path) if source_path else None,
        "source_sha256": (
            _sha256_file(source_path)
            if source_path and source_path.exists()
            else None
        ),
        "text_fields": ["titulo"],
        "note": (
            "Artefacto congelado para reproducibilidad. "
            "No contiene cuerpos completos de artículos."
        ),
    }
    metadata_path = output_dir / "news_embeddings.meta.json"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return EmbeddingArtifact(
        vectors_path=vectors_path,
        metadata_path=metadata_path,
        count=int(vectors.shape[0]),
        dimensions=int(vectors.shape[1]),
        model_name=provider.model_name,
    )


def load_embeddings(
    vectors_path: Path,
) -> tuple[np.ndarray, np.ndarray]:
    data = np.load(vectors_path, allow_pickle=False)
    return data["ids"], data["vectors"]


class SentenceTransformerProvider:
    """Proveedor local OPCIONAL.

    Requiere instalar `requirements-semantic.txt`.
    El modelo se carga de forma perezosa para que el MVP base no dependa de esta
    librería ni de internet en tiempo de ejecución.
    """

    def __init__(self, model_name: str):
        self._model_name = model_name
        self._model = None

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "sentence-transformers no está instalado. "
                    "Ejecuta: pip install -r requirements-semantic.txt"
                ) from exc
            except OSError as exc:
                # Caso frecuente en Windows: PyTorch no puede cargar c10.dll
                # o alguna dependencia nativa. Para este proyecto no necesitamos
                # CUDA para generar 1–2 mil embeddings, así que recomendamos la
                # build CPU oficial, más simple y portable.
                if "dll" in str(exc).lower() or "winerror 1114" in str(exc).lower():
                    raise RuntimeError(
                        "PyTorch no pudo cargar sus DLL nativas en Windows durante "
                        "la importación de Sentence Transformers. La build CPU ya "
                        "puede estar correcta; ejecuta "
                        "python scripts\\diagnose_torch_import_order.py para verificar "
                        "un conflicto por orden de carga de DLL."
                    ) from exc
                raise
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        model = self._get_model()
        vectors = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        return np.asarray(vectors, dtype=np.float32)
