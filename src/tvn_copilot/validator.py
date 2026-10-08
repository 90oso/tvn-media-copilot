from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import pandas as pd

from .data_contracts import (
    NEWS_COLUMNS,
    INDICATOR_COLUMNS,
    INDICATOR_NULLABLE_COLUMNS,
    NEWS_DATE_COLUMNS,
    INDICATOR_DATE_COLUMNS,
)


@dataclass
class ValidationResult:
    dataset_name: str
    source_path: str
    dataframe: pd.DataFrame
    summary: dict


def load_csv_preserving_nulls(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")
    return pd.read_csv(path, dtype="string", keep_default_na=True)


def _is_valid_http_url(value: object) -> bool:
    if pd.isna(value):
        return False
    parsed = urlparse(str(value).strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _valid_datetime_mask(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    return parsed.notna()


def _add_issue(bucket: list[list[str]], idx: int, issue: str) -> None:
    bucket[idx].append(issue)


def _schema_summary(df: pd.DataFrame, required_columns: Iterable[str]) -> dict:
    required = list(required_columns)
    missing = [c for c in required if c not in df.columns]
    extra = [c for c in df.columns if c not in required]
    return {"missing_columns": missing, "extra_columns": extra}


def _is_blank(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype("string").str.strip() == "")


def _count_codes(items: list[list[str]]) -> dict[str, int]:
    return dict(sorted(Counter(code for row in items for code in row).items()))


def validate_news(path: Path) -> ValidationResult:
    """Valida noticias sin confundir ausencia documentada con dato corrupto.

    Regla v0.6.1:
    - `fecha_publicacion` faltante en TVN RSS = ERROR.
    - `fecha_publicacion` faltante en otra procedencia, con fecha_deteccion válida = WARNING.
    - No se copia fecha_deteccion a fecha_publicacion.
    """
    df = load_csv_preserving_nulls(path)
    schema = _schema_summary(df, NEWS_COLUMNS)

    errors: list[list[str]] = [[] for _ in range(len(df))]
    warnings: list[list[str]] = [[] for _ in range(len(df))]

    # Campos requeridos de forma general. fecha_publicacion se maneja con regla condicional.
    generally_required = [c for c in NEWS_COLUMNS if c != "fecha_publicacion"]

    for col in generally_required:
        if col not in df.columns:
            continue
        null_mask = _is_blank(df[col])
        for idx in df.index[null_mask]:
            _add_issue(errors, int(idx), f"null:{col}")

    # fecha_publicacion: condición por procedencia.
    if "fecha_publicacion" in df.columns:
        pub_blank = _is_blank(df["fecha_publicacion"])
        origin = (
            df["origen"].astype("string").fillna("").str.strip()
            if "origen" in df.columns
            else pd.Series("", index=df.index, dtype="string")
        )

        # TVN RSS debe traer fecha de publicación.
        tvn_missing = pub_blank & origin.eq("TVN RSS")
        for idx in df.index[tvn_missing]:
            _add_issue(errors, int(idx), "null:fecha_publicacion")

        # Para otras fuentes, la ausencia se conserva como warning si existe detección válida.
        other_missing = pub_blank & ~origin.eq("TVN RSS")
        if "fecha_deteccion" in df.columns:
            detection_valid = _valid_datetime_mask(df["fecha_deteccion"])
        else:
            detection_valid = pd.Series(False, index=df.index)

        warning_missing = other_missing & detection_valid
        for idx in df.index[warning_missing]:
            _add_issue(warnings, int(idx), "missing_publication_date:fecha_publicacion")

        no_date_basis = other_missing & ~detection_valid
        for idx in df.index[no_date_basis]:
            _add_issue(errors, int(idx), "missing_date_basis:fecha_publicacion+fecha_deteccion")

    if "url" in df.columns:
        invalid = ~df["url"].map(_is_valid_http_url)
        for idx in df.index[invalid]:
            _add_issue(errors, int(idx), "invalid_url:url")

    for col in NEWS_DATE_COLUMNS:
        if col not in df.columns:
            continue
        non_null = ~_is_blank(df[col])
        invalid = non_null & (~_valid_datetime_mask(df[col]))
        for idx in df.index[invalid]:
            _add_issue(errors, int(idx), f"invalid_date:{col}")

    duplicate_id_count = 0
    if "id_noticia" in df.columns:
        duplicated = df["id_noticia"].notna() & df["id_noticia"].duplicated(keep=False)
        duplicate_id_count = int(duplicated.sum())
        for idx in df.index[duplicated]:
            _add_issue(errors, int(idx), "duplicate_id:id_noticia")

    out = df.copy()
    out["_validation_errors"] = [";".join(x) for x in errors]
    out["_validation_warnings"] = [";".join(x) for x in warnings]

    statuses = []
    for row_errors, row_warnings in zip(errors, warnings):
        if row_errors:
            statuses.append("error")
        elif row_warnings:
            statuses.append("warning")
        else:
            statuses.append("ok")
    out["_validation_status"] = statuses

    nulls_by_column = {col: int(df[col].isna().sum()) for col in df.columns}
    rows_ok = int((out["_validation_status"] == "ok").sum())
    rows_warning = int((out["_validation_status"] == "warning").sum())
    rows_error = int((out["_validation_status"] == "error").sum())

    by_origin = {}
    if "origen" in out.columns:
        for origin_value, group in out.groupby(out["origen"].fillna("<NA>")):
            by_origin[str(origin_value)] = {
                "rows": int(len(group)),
                "ok": int((group["_validation_status"] == "ok").sum()),
                "warning": int((group["_validation_status"] == "warning").sum()),
                "error": int((group["_validation_status"] == "error").sum()),
            }

    summary = {
        "rows_loaded": int(len(df)),
        "rows_ok": rows_ok,
        "rows_with_warnings": rows_warning,
        "rows_with_errors": rows_error,
        "rows_usable": rows_ok + rows_warning,
        # Compatibilidad con reportes anteriores: "issues" significa errores reales.
        "rows_with_issues": rows_error,
        "schema": schema,
        "duplicate_id_rows": duplicate_id_count,
        "nulls_by_column": nulls_by_column,
        "errors_by_code": _count_codes(errors),
        "warnings_by_code": _count_codes(warnings),
        "by_origin": by_origin,
        "note": (
            "Las filas con warning siguen siendo utilizables. "
            "La ausencia de fecha_publicacion en fuentes como GDELT se conserva y "
            "no se reemplaza por fecha_deteccion. Las filas con error requieren revisión."
        ),
    }

    return ValidationResult("noticias", str(path), out, summary)


def validate_indicators(path: Path) -> ValidationResult:
    df = load_csv_preserving_nulls(path)
    schema = _schema_summary(df, INDICATOR_COLUMNS)
    errors: list[list[str]] = [[] for _ in range(len(df))]

    for col in INDICATOR_COLUMNS:
        if col not in df.columns or col in INDICATOR_NULLABLE_COLUMNS:
            continue
        null_mask = _is_blank(df[col])
        for idx in df.index[null_mask]:
            _add_issue(errors, int(idx), f"null:{col}")

    if "fuente_url" in df.columns:
        invalid = ~df["fuente_url"].map(_is_valid_http_url)
        for idx in df.index[invalid]:
            _add_issue(errors, int(idx), "invalid_url:fuente_url")

    for col in INDICATOR_DATE_COLUMNS:
        if col in df.columns:
            non_null = ~_is_blank(df[col])
            invalid = non_null & (~_valid_datetime_mask(df[col]))
            for idx in df.index[invalid]:
                _add_issue(errors, int(idx), f"invalid_date:{col}")

    if "anio" in df.columns:
        year_num = pd.to_numeric(df["anio"], errors="coerce")
        invalid = df["anio"].notna() & year_num.isna()
        for idx in df.index[invalid]:
            _add_issue(errors, int(idx), "invalid_number:anio")

    if "valor" in df.columns:
        value_num = pd.to_numeric(df["valor"], errors="coerce")
        non_null = ~_is_blank(df["valor"])
        invalid = non_null & value_num.isna()
        for idx in df.index[invalid]:
            _add_issue(errors, int(idx), "invalid_number:valor")

    if "pais_iso3" in df.columns:
        invalid_iso3 = (
            df["pais_iso3"].notna()
            & (df["pais_iso3"].astype("string").str.strip().str.len() != 3)
        )
        for idx in df.index[invalid_iso3]:
            _add_issue(errors, int(idx), "invalid_iso3:pais_iso3")

    duplicate_key_rows = 0
    key_cols = ["pais_iso3", "indicador_id", "anio"]
    if all(c in df.columns for c in key_cols):
        duplicated = df.duplicated(subset=key_cols, keep=False)
        duplicate_key_rows = int(duplicated.sum())
        for idx in df.index[duplicated]:
            _add_issue(errors, int(idx), "duplicate_key:pais_iso3+indicador_id+anio")

    out = df.copy()
    out["_validation_errors"] = [";".join(x) for x in errors]
    out["_validation_warnings"] = ""
    out["_validation_status"] = ["ok" if not x else "error" for x in errors]

    nulls_by_column = {col: int(df[col].isna().sum()) for col in df.columns}
    rows_ok = int((out["_validation_status"] == "ok").sum())
    rows_error = int((out["_validation_status"] == "error").sum())

    summary = {
        "rows_loaded": int(len(df)),
        "rows_ok": rows_ok,
        "rows_with_warnings": 0,
        "rows_with_errors": rows_error,
        "rows_usable": rows_ok,
        "rows_with_issues": rows_error,
        "schema": schema,
        "duplicate_key_rows": duplicate_key_rows,
        "nulls_by_column": nulls_by_column,
        "errors_by_code": _count_codes(errors),
        "warnings_by_code": {},
        "nullable_by_contract": sorted(INDICATOR_NULLABLE_COLUMNS),
        "note": (
            "`valor` puede ser nulo por contrato. "
            "Las filas se conservan y no se rellenan con cero."
        ),
    }

    return ValidationResult("indicadores", str(path), out, summary)
