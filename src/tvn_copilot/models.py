from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Topic(str, Enum):
    ECONOMIA = "economía"
    LOGISTICA_CANAL = "logística/Canal"
    TURISMO = "turismo"
    SERVICIOS_PUBLICOS = "servicios públicos"
    EVENTOS_NATURALES = "eventos naturales"
    REGULACION = "regulación"


class EvidenceState(str, Enum):
    INSUFICIENTE = "insuficiente"
    PARCIAL = "parcial"
    SUFICIENTE_BORRADOR = "suficiente para el borrador"


class ReviewState(str, Enum):
    NUEVO = "nuevo"
    EN_REVISION = "en revisión"
    REQUIERE_EVIDENCIA = "requiere evidencia"
    APROBADO_BORRADOR = "aprobado como borrador"
    DESCARTADO = "descartado"


class AttentionComponents(BaseModel):
    relevancia: float = Field(ge=0, le=1)
    impacto_potencial: float = Field(ge=0, le=1)
    urgencia: float = Field(ge=0, le=1)
    novedad: float = Field(ge=0, le=1)
    evidencia_disponible: float = Field(ge=0, le=1)

    @property
    def score(self) -> float:
        return round(
            30 * self.relevancia
            + 25 * self.impacto_potencial
            + 20 * self.urgencia
            + 15 * self.novedad
            + 10 * self.evidencia_disponible,
            2,
        )


class CaseFile(BaseModel):
    # Modelo mínimo propuesto para representar fichas.jsonl.
    id_caso: str
    modalidad: str = "TVN"
    ids_fuente: list[str]
    afirmaciones: list[dict[str, Any]] = []
    citas: list[dict[str, Any]] = []
    puntaje: float | None = None
    componentes: dict[str, float] = {}
    estado_evidencia: EvidenceState = EvidenceState.INSUFICIENTE
    borrador: dict[str, Any] | None = None
    estado_revision: ReviewState = ReviewState.NUEVO
