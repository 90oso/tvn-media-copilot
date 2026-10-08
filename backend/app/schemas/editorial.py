from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ClaimType = Literal["hecho", "declaracion", "inferencia", "hipotesis"]


class EditorialClaim(BaseModel):
    type: ClaimType
    text: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)


class BriefDraft(BaseModel):
    proposed_title: str = Field(min_length=1)
    public_interest: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    claims: list[EditorialClaim] = Field(min_length=1)
    investigation_questions: list[str] = Field(min_length=3, max_length=3)
    sources_used: list[str] = Field(min_length=1)
    pending_checks: list[str] = Field(default_factory=list)


class ScriptDraft(BaseModel):
    script: str = Field(min_length=1)
    claims: list[EditorialClaim] = Field(min_length=1)
    sources_used: list[str] = Field(min_length=1)
    pending_checks: list[str] = Field(default_factory=list)


class DigitalDraft(BaseModel):
    copy: str = Field(min_length=1)
    claims: list[EditorialClaim] = Field(min_length=1)
    sources_used: list[str] = Field(min_length=1)
    pending_checks: list[str] = Field(default_factory=list)
