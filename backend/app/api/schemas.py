from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    deadline: Optional[datetime] = None


class StatusUpdateRequest(BaseModel):
    status: str
    verification_evidence: Optional[str] = None


class OutcomeCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    category: str = "decision"
    details: Optional[str] = None


class OutcomeUpdateRequest(BaseModel):
    status: str


class VoiceSynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    voice_id: Optional[str] = None
