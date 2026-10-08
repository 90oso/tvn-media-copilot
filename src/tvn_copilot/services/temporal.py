from __future__ import annotations

import pandas as pd


def effective_event_dates(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Fecha operativa para comparación temporal, sin reescribir el dato original.

    Prioridad:
    1) fecha_publicacion;
    2) fecha_deteccion como fallback operativo.

    Devuelve (fecha, fuente_de_fecha).
    """
    index = df.index

    publication = (
        pd.to_datetime(df["fecha_publicacion"], errors="coerce", utc=True)
        if "fecha_publicacion" in df.columns
        else pd.Series(pd.NaT, index=index, dtype="datetime64[ns, UTC]")
    )

    detection = (
        pd.to_datetime(df["fecha_deteccion"], errors="coerce", utc=True)
        if "fecha_deteccion" in df.columns
        else pd.Series(pd.NaT, index=index, dtype="datetime64[ns, UTC]")
    )

    effective = publication.fillna(detection)

    source = pd.Series("missing", index=index, dtype="string")
    source.loc[publication.notna()] = "fecha_publicacion"
    source.loc[publication.isna() & detection.notna()] = "fecha_deteccion"

    return effective, source
