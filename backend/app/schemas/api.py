from pydantic import BaseModel, Field
class AttentionScoreRequest(BaseModel):
    relevance: float = Field(ge=0, le=1)
    impact: float = Field(ge=0, le=1)
    urgency: float = Field(ge=0, le=1)
    novelty: float = Field(ge=0, le=1)
    evidence: float = Field(ge=0, le=1)
