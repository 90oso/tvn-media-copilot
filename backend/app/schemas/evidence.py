from pydantic import BaseModel, Field

class EvidenceItem(BaseModel):
    evidence_id: str
    source_type: str
    source_name: str
    field: str
    value: str
    url: str | None = None
    period: str | None = None
    unit: str | None = None
    scope_note: str | None = None

class EvidencePackage(BaseModel):
    case_id: str
    topic: str | None = None
    news_ids: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    evidence_state: str
    independent_provenances: int = 0
    rules_version: str
