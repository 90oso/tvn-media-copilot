from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Literal, Type

from pydantic import BaseModel, ValidationError

from app.schemas.editorial import (
    BriefDraft,
    DigitalDraft,
    ScriptDraft,
)
from app.schemas.evidence import EvidencePackage
from app.services.llm_provider import LLMProvider


DraftMode = Literal["brief", "script", "digital"]


@dataclass(frozen=True)
class GeneratedEditorial:
    mode: DraftMode
    draft: dict[str, Any]
    rendered_text: str
    quality: dict[str, Any]
    provider: str
    model: str
    attempts: int
    generation_rounds: int


def _word_count(text: str) -> int:
    return len(
        re.findall(r"\b[\wÁÉÍÓÚÜÑáéíóúüñ'-]+\b", text or "")
    )


def _fingerprint(
    evidence: EvidencePackage,
    mode: DraftMode,
) -> str:
    payload = {
        "mode": mode,
        "evidence": evidence.model_dump(),
    }
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(raw.encode("utf-8")).hexdigest()[:16]


def _known_evidence_ids(evidence: EvidencePackage) -> set[str]:
    return {item.evidence_id for item in evidence.evidence}


def _validate_citations(
    draft: BaseModel,
    evidence: EvidencePackage,
) -> dict[str, Any]:
    known = _known_evidence_ids(evidence)
    claims = list(getattr(draft, "claims", []))

    invalid: set[str] = set()
    cited_claims = 0

    for claim in claims:
        ids = [str(value) for value in claim.evidence_ids]
        if ids:
            cited_claims += 1
        for evidence_id in ids:
            if evidence_id not in known:
                invalid.add(evidence_id)

    sources_used = [
        str(value)
        for value in getattr(draft, "sources_used", [])
    ]
    for evidence_id in sources_used:
        if evidence_id not in known:
            invalid.add(evidence_id)

    coverage = (
        cited_claims / len(claims)
        if claims
        else 0.0
    )

    return {
        "claim_count": len(claims),
        "claims_with_citations": cited_claims,
        "citation_coverage": round(coverage, 4),
        "invalid_evidence_ids": sorted(invalid),
    }


def _schema_for_mode(
    mode: DraftMode,
) -> Type[BaseModel]:
    if mode == "brief":
        return BriefDraft
    if mode == "script":
        return ScriptDraft
    if mode == "digital":
        return DigitalDraft
    raise ValueError(f"Modalidad no soportada: {mode}")


def _task_for_mode(
    mode: DraftMode,
    correction: str | None = None,
) -> str:
    common = """
Usa exclusivamente evidence_id presentes en el paquete.
Cada elemento de `claims` debe tener `type`, `text` y uno o más `evidence_ids`.
`sources_used` debe contener únicamente evidence_id realmente usados.
Incluye en `pending_checks` cualquier faltante o contradicción pendiente.
No inventes entrevistas, declaraciones, imágenes ni hechos no contenidos en la evidencia.
"""

    if mode == "brief":
        task = """
Genera un BRIEF EDITORIAL estructurado en JSON con exactamente estas claves:
{
  "proposed_title": "string",
  "public_interest": "string",
  "summary": "string de máximo 250 palabras",
  "claims": [
    {
      "type": "hecho|declaracion|inferencia|hipotesis",
      "text": "string",
      "evidence_ids": ["ID"]
    }
  ],
  "investigation_questions": ["pregunta 1", "pregunta 2", "pregunta 3"],
  "sources_used": ["ID"],
  "pending_checks": ["string"]
}
"""
    elif mode == "script":
        task = """
Genera un GUION DE 45 A 60 SEGUNDOS estructurado en JSON con exactamente estas claves:
{
  "script": "texto para locución",
  "claims": [
    {
      "type": "hecho|declaracion|inferencia|hipotesis",
      "text": "string",
      "evidence_ids": ["ID"]
    }
  ],
  "sources_used": ["ID"],
  "pending_checks": ["string"]
}
El texto hablado no necesita leer los IDs en voz alta; la trazabilidad queda en `claims`.
"""
    else:
        task = """
Genera un COPY DIGITAL estructurado en JSON con exactamente estas claves:
{
  "copy": "texto de máximo 80 palabras",
  "claims": [
    {
      "type": "hecho|declaracion|inferencia|hipotesis",
      "text": "string",
      "evidence_ids": ["ID"]
    }
  ],
  "sources_used": ["ID"],
  "pending_checks": ["string"]
}
"""

    if correction:
        task += (
            "\nLa salida anterior no pasó la validación del sistema. "
            "Corrige estos problemas:\n"
            f"{correction}\n"
        )

    return common + task


def _quality_for_mode(
    mode: DraftMode,
    draft: BaseModel,
    evidence: EvidencePackage,
) -> dict[str, Any]:
    citation = _validate_citations(draft, evidence)

    if citation["invalid_evidence_ids"]:
        raise ValueError(
            "La salida cita evidence_id inexistentes: "
            + ", ".join(citation["invalid_evidence_ids"])
        )

    if citation["citation_coverage"] < 1.0:
        raise ValueError(
            "No todos los claims contienen evidence_ids."
        )

    quality: dict[str, Any] = {
        **citation,
        "contradictions_in_evidence": len(
            evidence.contradictions
        ),
    }

    if mode == "brief":
        count = _word_count(draft.summary)
        quality.update(
            {
                "main_text_word_count": count,
                "word_limit": 250,
                "within_word_limit": count <= 250,
            }
        )
        if count > 250:
            raise ValueError(
                f"El brief tiene {count} palabras; máximo 250."
            )

        if len(draft.investigation_questions) != 3:
            raise ValueError(
                "El brief debe contener exactamente 3 preguntas."
            )

    elif mode == "digital":
        count = _word_count(draft.copy)
        quality.update(
            {
                "main_text_word_count": count,
                "word_limit": 80,
                "within_word_limit": count <= 80,
            }
        )
        if count > 80:
            raise ValueError(
                f"El copy tiene {count} palabras; máximo 80."
            )

    elif mode == "script":
        count = _word_count(draft.script)
        # Estimación conservadora de 140 palabras/minuto.
        estimated_seconds = (
            round(count / (140 / 60), 1)
            if count
            else 0.0
        )
        quality.update(
            {
                "main_text_word_count": count,
                "estimated_duration_seconds": estimated_seconds,
                "target_duration_seconds": "45-60",
                "within_duration_target": (
                    45 <= estimated_seconds <= 60
                ),
            }
        )
        # No bloqueamos por esta estimación porque velocidad de locución varía.

    return quality


def _render_claims(claims) -> str:
    lines = []
    for claim in claims:
        ids = " ".join(
            f"[{evidence_id}]"
            for evidence_id in claim.evidence_ids
        )
        lines.append(
            f"- {claim.type.upper()}: {claim.text} {ids}".rstrip()
        )
    return "\n".join(lines)


def render_draft(
    mode: DraftMode,
    draft: BaseModel,
) -> str:
    if mode == "brief":
        return (
            f"TÍTULO PROPUESTO\n{draft.proposed_title}\n\n"
            f"INTERÉS PÚBLICO\n{draft.public_interest}\n\n"
            f"BRIEF\n{draft.summary}\n\n"
            f"AFIRMACIONES TRAZABLES\n{_render_claims(draft.claims)}\n\n"
            "PREGUNTAS DE INVESTIGACIÓN\n"
            + "\n".join(
                f"{idx}. {question}"
                for idx, question in enumerate(
                    draft.investigation_questions,
                    start=1,
                )
            )
            + "\n\nVERIFICACIONES PENDIENTES\n"
            + (
                "\n".join(
                    f"- {item}"
                    for item in draft.pending_checks
                )
                if draft.pending_checks
                else "- Ninguna adicional declarada."
            )
        )

    if mode == "script":
        return (
            f"GUION 45–60 s\n{draft.script}\n\n"
            f"AFIRMACIONES TRAZABLES\n{_render_claims(draft.claims)}\n\n"
            "VERIFICACIONES PENDIENTES\n"
            + (
                "\n".join(
                    f"- {item}"
                    for item in draft.pending_checks
                )
                if draft.pending_checks
                else "- Ninguna adicional declarada."
            )
        )

    return (
        f"COPY DIGITAL\n{draft.copy}\n\n"
        f"AFIRMACIONES TRAZABLES\n{_render_claims(draft.claims)}\n\n"
        "VERIFICACIONES PENDIENTES\n"
        + (
            "\n".join(
                f"- {item}"
                for item in draft.pending_checks
            )
            if draft.pending_checks
            else "- Ninguna adicional declarada."
        )
    )


def generate_editorial(
    provider: LLMProvider,
    mode: DraftMode,
    evidence: EvidencePackage,
) -> GeneratedEditorial:
    schema = _schema_for_mode(mode)

    correction: str | None = None
    last_error: Exception | None = None
    total_attempts = 0

    # Máximo dos rondas lógicas: generación y una reparación de formato/calidad.
    for round_number in (1, 2):
        response = provider.generate_json_from_evidence(
            _task_for_mode(mode, correction),
            evidence,
        )
        total_attempts += response.attempts

        try:
            draft = schema.model_validate(response.data)
            quality = _quality_for_mode(
                mode,
                draft,
                evidence,
            )
            return GeneratedEditorial(
                mode=mode,
                draft=draft.model_dump(),
                rendered_text=render_draft(mode, draft),
                quality=quality,
                provider=response.provider,
                model=response.model,
                attempts=total_attempts,
                generation_rounds=round_number,
            )
        except (ValidationError, ValueError) as exc:
            last_error = exc
            correction = str(exc)

    raise RuntimeError(
        "Gemini respondió, pero el borrador estructurado no pasó "
        f"la validación: {last_error}"
    )


def cache_path(
    cache_dir: Path,
    evidence: EvidencePackage,
    mode: DraftMode,
) -> Path:
    fingerprint = _fingerprint(evidence, mode)
    return (
        cache_dir
        / f"{evidence.case_id}_{mode}_{fingerprint}.json"
    )


def save_cache(
    cache_dir: Path,
    evidence: EvidencePackage,
    result: GeneratedEditorial,
) -> Path:
    path = cache_path(cache_dir, evidence, result.mode)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": result.mode,
        "draft": result.draft,
        "text": result.rendered_text,
        "quality": result.quality,
        "provider": result.provider,
        "model": result.model,
        "attempts": result.attempts,
        "generation_rounds": result.generation_rounds,
        "evidence_fingerprint": _fingerprint(
            evidence,
            result.mode,
        ),
    }
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def load_cache(
    cache_dir: Path,
    evidence: EvidencePackage,
    mode: DraftMode,
) -> dict[str, Any] | None:
    path = cache_path(cache_dir, evidence, mode)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
