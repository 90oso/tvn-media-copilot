from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

ReviewAction = Literal["approve", "correct", "discard"]

class ReviewRequest(BaseModel):
    action: ReviewAction
    reviewer: str = Field(default="editor", min_length=1, max_length=120)
    note: str = Field(default="", max_length=2000)

class ReviewRecord(BaseModel):
    case_id: str
    action: ReviewAction
    state: str
    reviewer: str
    note: str = ""
    updated_at: str
