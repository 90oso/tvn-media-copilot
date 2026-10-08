from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib

import numpy as np
import pandas as pd

from .embeddings import load_embeddings
from .temporal import effective_event_dates


@dataclass(frozen=True)
class SemanticGroupingConfig:
    """Parámetros propuestos; deben calibrarse contra etiquetas humanas."""
    similarity_threshold: float = 0.78
    max_days_apart: int = 3
    require_same_topic_when_available: bool = False


class _UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb
        elif self.rank[ra] > self.rank[rb]:
            self.parent[rb] = ra
        else:
            self.parent[rb] = ra
            self.rank[ra] += 1


def _date_compatible(
    a: pd.Timestamp | pd.NaT,
    b: pd.Timestamp | pd.NaT,
    max_days_apart: int,
) -> bool:
    if pd.isna(a) or pd.isna(b):
        return True
    return abs(a - b) <= pd.Timedelta(days=max_days_apart)


def _topic_compatible(row_a: pd.Series, row_b: pd.Series) -> bool:
    for col in ("tema_baseline", "tema"):
        if col in row_a.index and col in row_b.index:
            a = row_a[col]
            b = row_b[col]
            a_valid = pd.notna(a) and str(a) not in {"", "sin_clasificar", "<NA>"}
            b_valid = pd.notna(b) and str(b) not in {"", "sin_clasificar", "<NA>"}
            if a_valid and b_valid:
                return str(a) == str(b)
    return True


def _stable_cluster_id(member_ids: list[str]) -> str:
    digest = hashlib.sha1("|".join(sorted(member_ids)).encode("utf-8")).hexdigest()[:10]
    return f"EVT-S-{digest}"


def _cosine_pair(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def group_news_semantic(
    df: pd.DataFrame,
    ids: np.ndarray,
    vectors: np.ndarray,
    config: SemanticGroupingConfig | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Agrupa por embeddings con pruning temporal.

    Para 1,000+ noticias evita construir una matriz NxN completa y evita guardar
    pares que ya son incompatibles por fecha.
    """
    config = config or SemanticGroupingConfig()

    if "id_noticia" not in df.columns:
        raise ValueError("Falta la columna `id_noticia`.")

    out = df.copy().reset_index(drop=True)

    ids = np.asarray(ids).astype(str)
    vectors = np.asarray(vectors, dtype=np.float32)

    if vectors.ndim != 2:
        raise ValueError("`vectors` debe ser una matriz 2D.")
    if len(ids) != vectors.shape[0]:
        raise ValueError("Cantidad de IDs y embeddings no coincide.")

    vector_by_id = {str(id_): vectors[i] for i, id_ in enumerate(ids)}
    missing_embeddings = [
        str(id_) for id_ in out["id_noticia"].astype(str)
        if str(id_) not in vector_by_id
    ]
    if missing_embeddings:
        raise ValueError(
            "Faltan embeddings para: " + ", ".join(missing_embeddings[:10])
        )

    ordered_vectors = np.stack(
        [vector_by_id[str(id_)] for id_ in out["id_noticia"].astype(str)]
    )

    dates, date_sources = effective_event_dates(out)

    uf = _UnionFind(len(out))
    pair_rows: list[dict] = []
    skipped_temporal = 0

    for i in range(len(out)):
        for j in range(i + 1, len(out)):
            date_ok = _date_compatible(
                dates.iloc[i],
                dates.iloc[j],
                config.max_days_apart,
            )
            if not date_ok:
                skipped_temporal += 1
                continue

            sim = _cosine_pair(ordered_vectors[i], ordered_vectors[j])

            topic_ok = (
                _topic_compatible(out.iloc[i], out.iloc[j])
                if config.require_same_topic_when_available
                else True
            )

            accepted = (
                sim >= config.similarity_threshold
                and topic_ok
            )

            pair_rows.append(
                {
                    "id_noticia_a": str(out.iloc[i]["id_noticia"]),
                    "id_noticia_b": str(out.iloc[j]["id_noticia"]),
                    "similarity_semantic": round(sim, 6),
                    "date_compatible": True,
                    "effective_date_a": (
                        dates.iloc[i].isoformat()
                        if pd.notna(dates.iloc[i]) else None
                    ),
                    "effective_date_b": (
                        dates.iloc[j].isoformat()
                        if pd.notna(dates.iloc[j]) else None
                    ),
                    "date_source_a": str(date_sources.iloc[i]),
                    "date_source_b": str(date_sources.iloc[j]),
                    "topic_compatible": bool(topic_ok),
                    "accepted_same_event": bool(accepted),
                }
            )

            if accepted:
                uf.union(i, j)

    root_to_members: dict[int, list[int]] = {}
    for idx in range(len(out)):
        root_to_members.setdefault(uf.find(idx), []).append(idx)

    cluster_ids: dict[int, str] = {}
    for root_idx, members in root_to_members.items():
        member_ids = [str(out.iloc[m]["id_noticia"]) for m in members]
        cluster_ids[root_idx] = _stable_cluster_id(member_ids)

    out["cluster_semantic"] = [
        cluster_ids[uf.find(i)] for i in range(len(out))
    ]

    sizes = out["cluster_semantic"].value_counts().to_dict()
    out["cluster_size_semantic"] = (
        out["cluster_semantic"].map(sizes).astype(int)
    )

    provenance_col = (
        "origen"
        if "origen" in out.columns
        else ("medio" if "medio" in out.columns else None)
    )

    if provenance_col:
        provenance_map = (
            out.groupby("cluster_semantic")[provenance_col]
            .apply(
                lambda s: sorted(
                    {
                        str(x).strip()
                        for x in s.dropna()
                        if str(x).strip()
                    }
                )
            )
            .to_dict()
        )
        out["procedencias_semantic"] = out["cluster_semantic"].map(
            lambda cid: " | ".join(provenance_map.get(cid, []))
        )
        out["procedencias_independientes_semantic"] = out["cluster_semantic"].map(
            lambda cid: len(provenance_map.get(cid, []))
        ).astype(int)
    else:
        out["procedencias_semantic"] = ""
        out["procedencias_independientes_semantic"] = 0

    pairs = pd.DataFrame(pair_rows)
    pairs.attrs["skipped_temporal_pairs"] = skipped_temporal
    return out, pairs


def load_and_group_semantic(
    news_csv: Path,
    embeddings_npz: Path,
    config: SemanticGroupingConfig | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(news_csv, dtype="string")
    ids, vectors = load_embeddings(embeddings_npz)
    return group_news_semantic(df, ids, vectors, config=config)
