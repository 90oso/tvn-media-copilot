from __future__ import annotations
from pathlib import Path
import sqlite3
import pandas as pd

try:
    import duckdb  # type: ignore
except ImportError:  # fallback útil para entornos mínimos de desarrollo
    duckdb = None


class DuckDBRepository:
    """Repositorio analítico.

    Usa DuckDB cuando está instalado (entorno objetivo). Si no está disponible,
    usa SQLite como fallback de desarrollo para mantener healthchecks/tests ejecutables.
    El archivo de base no se versiona y se regenera desde el snapshot.
    """

    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def engine(self) -> str:
        return "duckdb" if duckdb is not None else "sqlite-fallback"

    def connect(self):
        if duckdb is not None:
            return duckdb.connect(str(self.database_path))
        return sqlite3.connect(str(self.database_path))

    def _tables(self, con) -> list[str]:
        if duckdb is not None:
            return [r[0] for r in con.execute("SHOW TABLES").fetchall()]
        return [
            r[0]
            for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]

    def _columns(self, con, table: str) -> set[str]:
        if duckdb is not None:
            return {r[0] for r in con.execute(f"DESCRIBE {table}").fetchall()}
        return {r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()}

    def bootstrap_from_csv(self, news_csv: Path | None, indicators_csv: Path | None) -> dict:
        loaded: dict[str, int] = {}
        if duckdb is not None:
            with self.connect() as con:
                if news_csv and news_csv.exists():
                    con.execute(
                        "CREATE OR REPLACE TABLE noticias AS SELECT * FROM read_csv_auto(?, header=true)",
                        [str(news_csv)],
                    )
                    loaded["noticias"] = con.execute("SELECT COUNT(*) FROM noticias").fetchone()[0]
                if indicators_csv and indicators_csv.exists():
                    con.execute(
                        "CREATE OR REPLACE TABLE indicadores AS SELECT * FROM read_csv_auto(?, header=true)",
                        [str(indicators_csv)],
                    )
                    loaded["indicadores"] = con.execute("SELECT COUNT(*) FROM indicadores").fetchone()[0]
            return loaded

        with self.connect() as con:
            if news_csv and news_csv.exists():
                df = pd.read_csv(news_csv)
                df.to_sql("noticias", con, if_exists="replace", index=False)
                loaded["noticias"] = len(df)
            if indicators_csv and indicators_csv.exists():
                df = pd.read_csv(indicators_csv)
                df.to_sql("indicadores", con, if_exists="replace", index=False)
                loaded["indicadores"] = len(df)
        return loaded

    def health(self) -> dict:
        with self.connect() as con:
            tables = self._tables(con)
            counts = {
                table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in tables
            }
        return {
            "database": str(self.database_path),
            "engine": self.engine,
            "tables": tables,
            "counts": counts,
        }

    def list_news(self, limit: int = 20) -> pd.DataFrame:
        with self.connect() as con:
            if "noticias" not in self._tables(con):
                return pd.DataFrame()
            if duckdb is not None:
                return con.execute("SELECT * FROM noticias LIMIT ?", [limit]).fetchdf()
            return pd.read_sql_query("SELECT * FROM noticias LIMIT ?", con, params=(limit,))


    def get_all_valid_news(self) -> pd.DataFrame:
        """Carga las noticias utilizables en una sola consulta.

        La agenda usa este método para evitar abrir la base una vez por cada
        cluster. Con ~1,300 clusters, el patrón anterior provocaba cientos o
        miles de conexiones/consultas por una sola petición HTTP.
        """
        with self.connect() as con:
            if "noticias" not in self._tables(con):
                return pd.DataFrame()

            cols = self._columns(con, "noticias")
            valid_clause = (
                " WHERE _validation_status IN ('ok','warning')"
                if "_validation_status" in cols
                else ""
            )
            query = f"SELECT * FROM noticias{valid_clause}"

            if duckdb is not None:
                return con.execute(query).fetchdf()

            return pd.read_sql_query(query, con)

    def _editorial_store(self):
        import os
        from app.repositories.editorial_store import EditorialStore
        url = os.environ.get("EDITORIAL_DATABASE_URL")
        return EditorialStore(url if url else "sqlite:///" + str(self.database_path.parent / "editorial.sqlite3"))

    def get_all_reviews(self) -> dict[str, dict]:
        from app.repositories.editorial_store import EditorialStore
        return self._editorial_store().all_reviews()
        """Devuelve revisiones humanas indexadas por case_id en una sola consulta."""
        with self.connect() as con:
            self._ensure_reviews_table(con)
            rows = con.execute(
                """
                SELECT case_id, action, state, reviewer, note, updated_at
                FROM reviews
                """
            ).fetchall()

        keys = [
            "case_id",
            "action",
            "state",
            "reviewer",
            "note",
            "updated_at",
        ]
        return {
            str(row[0]): dict(zip(keys, row))
            for row in rows
        }

    def get_cluster_news(self, cluster_id: str) -> pd.DataFrame:
        with self.connect() as con:
            if "noticias" not in self._tables(con):
                return pd.DataFrame()
            cols = self._columns(con, "noticias")
            cluster_col = (
                "cluster_semantic"
                if "cluster_semantic" in cols
                else "cluster_baseline"
                if "cluster_baseline" in cols
                else None
            )
            if not cluster_col:
                return pd.DataFrame()
            valid_clause = " AND _validation_status IN ('ok','warning')" if "_validation_status" in cols else ""
            query = f"SELECT * FROM noticias WHERE {cluster_col}=?{valid_clause}"
            if duckdb is not None:
                return con.execute(query, [cluster_id]).fetchdf()
            return pd.read_sql_query(query, con, params=(cluster_id,))

    def list_cluster_ids(self) -> list[str]:
        with self.connect() as con:
            if "noticias" not in self._tables(con):
                return []
            cols = self._columns(con, "noticias")
            cluster_col = (
                "cluster_semantic"
                if "cluster_semantic" in cols
                else "cluster_baseline"
                if "cluster_baseline" in cols
                else None
            )
            if not cluster_col:
                return []
            valid_clause = " AND _validation_status IN ('ok','warning')" if "_validation_status" in cols else ""
            rows = con.execute(
                f"SELECT DISTINCT {cluster_col} FROM noticias "
                f"WHERE {cluster_col} IS NOT NULL{valid_clause} ORDER BY {cluster_col}"
            ).fetchall()
            return [str(r[0]) for r in rows]

    def get_snapshot_reference(self):
        with self.connect() as con:
            if "noticias" not in self._tables(con):
                return None
            cols = self._columns(con, "noticias")
            if "fecha_publicacion" not in cols and "fecha_deteccion" not in cols:
                return None
            if duckdb is not None:
                pub_expr = (
                    "TRY_CAST(fecha_publicacion AS TIMESTAMPTZ)"
                    if "fecha_publicacion" in cols else "NULL"
                )
                det_expr = (
                    "TRY_CAST(fecha_deteccion AS TIMESTAMPTZ)"
                    if "fecha_deteccion" in cols else "NULL"
                )
                return con.execute(
                    f"SELECT MAX(COALESCE({pub_expr}, {det_expr})) FROM noticias"
                ).fetchone()[0]

            select_cols = [
                c for c in ("fecha_publicacion", "fecha_deteccion") if c in cols
            ]
            frame = pd.read_sql_query(
                f"SELECT {', '.join(select_cols)} FROM noticias", con
            )
            pub = (
                pd.to_datetime(frame["fecha_publicacion"], errors="coerce", utc=True)
                if "fecha_publicacion" in frame else pd.Series(pd.NaT, index=frame.index)
            )
            det = (
                pd.to_datetime(frame["fecha_deteccion"], errors="coerce", utc=True)
                if "fecha_deteccion" in frame else pd.Series(pd.NaT, index=frame.index)
            )
            effective = pub.fillna(det).dropna()
            return effective.max() if not effective.empty else None

    def get_panama_indicators(self) -> pd.DataFrame:
        with self.connect() as con:
            if "indicadores" not in self._tables(con):
                return pd.DataFrame()
            if "pais_iso3" not in self._columns(con, "indicadores"):
                return pd.DataFrame()
            if duckdb is not None:
                return con.execute(
                    "SELECT * FROM indicadores WHERE pais_iso3='PAN'"
                ).fetchdf()
            return pd.read_sql_query(
                "SELECT * FROM indicadores WHERE pais_iso3='PAN'", con
            )

    def _ensure_reviews_table(self, con) -> None:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                case_id VARCHAR PRIMARY KEY,
                action VARCHAR NOT NULL,
                state VARCHAR NOT NULL,
                reviewer VARCHAR NOT NULL,
                note VARCHAR,
                updated_at VARCHAR NOT NULL
            )
            """
        )

    def save_review(self, case_id: str, action: str, state: str, reviewer: str, note: str, updated_at: str) -> dict:
        from app.repositories.editorial_store import EditorialStore
        return self._editorial_store().save_review(case_id, action, state, reviewer, note, updated_at)
        with self.connect() as con:
            self._ensure_reviews_table(con)
            con.execute("DELETE FROM reviews WHERE case_id=?", [case_id] if duckdb is not None else (case_id,))
            params = [case_id, action, state, reviewer, note, updated_at] if duckdb is not None else (case_id, action, state, reviewer, note, updated_at)
            con.execute(
                "INSERT INTO reviews(case_id,action,state,reviewer,note,updated_at) VALUES (?,?,?,?,?,?)",
                params,
            )
        return self.get_review(case_id) or {}

    def get_review(self, case_id: str) -> dict | None:
        from app.repositories.editorial_store import EditorialStore
        return self._editorial_store().get_review(case_id)
        with self.connect() as con:
            self._ensure_reviews_table(con)
            row = con.execute(
                "SELECT case_id,action,state,reviewer,note,updated_at FROM reviews WHERE case_id=?",
                [case_id] if duckdb is not None else (case_id,),
            ).fetchone()
            if not row:
                return None
            keys = ["case_id","action","state","reviewer","note","updated_at"]
            return dict(zip(keys, row))
