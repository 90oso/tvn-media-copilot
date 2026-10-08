from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
import unicodedata

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .temporal import effective_event_dates


@dataclass(frozen=True)
class GroupingConfig:
    """Parámetros propuestos, no impuestos por el documento."""
    similarity_threshold: float = 0.42
    max_days_apart: int = 3
    require_same_topic_when_available: bool = True
    min_title_chars: int = 8


def _normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^a-z0-9ñ\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _same_topic_or_unknown(row_a: pd.Series, row_b: pd.Series) -> bool:
    for col in ("tema_baseline", "tema"):
        if col in row_a.index and col in row_b.index:
            a = row_a[col]
            b = row_b[col]
            a_valid = pd.notna(a) and str(a) not in {"", "sin_clasificar", "<NA>"}
            b_valid = pd.notna(b) and str(b) not in {"", "sin_clasificar", "<NA>"}
            if a_valid and b_valid:
                return str(a) == str(b)
    return True


def _date_compatible(
    date_a: pd.Timestamp | pd.NaT,
    date_b: pd.Timestamp | pd.NaT,
    max_days_apart: int,
) -> bool:
    if pd.isna(date_a) or pd.isna(date_b):
        # Conservador: no inventamos una distancia inexistente.
        return True
    return abs(date_a - date_b) <= pd.Timedelta(days=max_days_apart)


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


def group_news_baseline(
    df: pd.DataFrame,
    config: GroupingConfig | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """TF-IDF + coseno + ventana temporal + tema.

    v0.6.2:
    - usa publicación y, si falta, detección SOLO como fecha operativa;
    - no modifica ninguna columna original;
    - evita materializar pares que están claramente fuera de la ventana temporal,
      reduciendo memoria en corpus reales.
    """
    config = config or GroupingConfig()

    required = {"id_noticia", "titulo"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            "Faltan columnas requeridas para agrupación: "
            + ", ".join(sorted(missing))
        )

    out = df.copy().reset_index(drop=True)
    normalized_titles = out["titulo"].map(_normalize_text)
    eligible = normalized_titles.str.len() >= config.min_title_chars

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
        lowercase=False,
        norm="l2",
    )

    matrix = None
    if eligible.any():
        matrix = vectorizer.fit_transform(normalized_titles.where(eligible, ""))

    dates, date_sources = effective_event_dates(out)

    uf = _UnionFind(len(out))
    comparisons: list[dict] = []
    skipped_temporal = 0

    if matrix is not None and len(out) > 1:
        sim = cosine_similarity(matrix)

        for i in range(len(out)):
            if not eligible.iloc[i]:
                continue

            for j in range(i + 1, len(out)):
                if not eligible.iloc[j]:
                    continue

                date_ok = _date_compatible(
                    dates.iloc[i],
                    dates.iloc[j],
                    config.max_days_apart,
                )

                # En corpus real no guardamos millones de pares obviamente incompatibles.
                if not date_ok:
                    skipped_temporal += 1
                    continue

                similarity = float(sim[i, j])
                topic_ok = (
                    _same_topic_or_unknown(out.iloc[i], out.iloc[j])
                    if config.require_same_topic_when_available
                    else True
                )
                accepted = (
                    similarity >= config.similarity_threshold
                    and topic_ok
                )

                comparisons.append(
                    {
                        "id_noticia_a": str(out.iloc[i]["id_noticia"]),
                        "id_noticia_b": str(out.iloc[j]["id_noticia"]),
                        "similarity_tfidf": round(similarity, 6),
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
        member_ids = sorted(str(out.iloc[m]["id_noticia"]) for m in members)
        digest = hashlib.sha1("|".join(member_ids).encode("utf-8")).hexdigest()[:10]
        cluster_ids[root_idx] = f"EVT-B-{digest}"

    out["cluster_baseline"] = [
        cluster_ids[uf.find(i)] for i in range(len(out))
    ]

    cluster_sizes = out["cluster_baseline"].value_counts().to_dict()
    out["cluster_size_baseline"] = (
        out["cluster_baseline"].map(cluster_sizes).astype(int)
    )

    provenance_col = (
        "origen"
        if "origen" in out.columns
        else ("medio" if "medio" in out.columns else None)
    )

    if provenance_col:
        provenance_map = (
            out.groupby("cluster_baseline")[provenance_col]
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
        out["procedencias_baseline"] = out["cluster_baseline"].map(
            lambda cid: " | ".join(provenance_map.get(cid, []))
        )
        out["procedencias_independientes_baseline"] = out["cluster_baseline"].map(
            lambda cid: len(provenance_map.get(cid, []))
        ).astype(int)
    else:
        out["procedencias_baseline"] = ""
        out["procedencias_independientes_baseline"] = 0

    pairs = pd.DataFrame(comparisons)
    pairs.attrs["skipped_temporal_pairs"] = skipped_temporal
    return out, pairs


def cluster_summary(df: pd.DataFrame) -> pd.DataFrame:
    required = {
        "cluster_baseline",
        "cluster_size_baseline",
        "procedencias_independientes_baseline",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            "El dataframe no contiene resultados de agrupación baseline: "
            + ", ".join(sorted(missing))
        )

    agg = {
        "cluster_size_baseline": "first",
        "procedencias_independientes_baseline": "first",
    }
    if "tema_baseline" in df.columns:
        agg["tema_baseline"] = lambda s: " | ".join(
            sorted({str(x) for x in s.dropna() if str(x) != "sin_clasificar"})
        )
    if "titulo" in df.columns:
        agg["titulo"] = lambda s: " || ".join(str(x) for x in s.dropna())
    if "medio" in df.columns:
        agg["medio"] = lambda s: " | ".join(sorted({str(x) for x in s.dropna()}))

    return (
        df.groupby("cluster_baseline", as_index=False)
        .agg(agg)
        .sort_values(
            ["cluster_size_baseline", "cluster_baseline"],
            ascending=[False, True],
        )
        .reset_index(drop=True)
    )
