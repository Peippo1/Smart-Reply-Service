from typing import Literal

from pydantic import BaseModel, Field


Channel = Literal["email", "slack", "whatsapp", "linkedin"]
Tone = Literal["friendly", "professional", "concise", "assertive", "apologetic"]


class Constraints(BaseModel):
    word_limit: int | None = Field(default=None, ge=10, le=2000)
    must_include_question: bool = False
    avoid_phrases: list[str] | None = None


class DraftRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Incoming user message or email body.")
    context: str | None = Field(default=None, description="Optional extra context about thread or user.")
    channel: Channel = "email"
    tone: Tone = "professional"
    constraints: Constraints | None = None


class DraftCandidate(BaseModel):
    text: str
    tone_label: Tone
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)


class DraftResponse(BaseModel):
    drafts: list[DraftCandidate]
    channel: Channel
    requested_tone: Tone
    evidence: str | None = Field(
        default=None,
        description="Short note describing heuristic used to compute confidence.",
    )


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str = "smart-reply-service"
