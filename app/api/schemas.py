from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Enums
Channel = Literal["email", "slack", "linkedin"]
Tone = Literal["friendly", "professional", "concise", "assertive", "apologetic", "polite", "neutral"]


class Constraints(BaseModel):
    max_words: int | None = Field(
        default=None,
        ge=1,
        le=500,
        description="Maximum words allowed in a draft.",
    )
    must_include_question: bool = Field(
        default=False, description="Whether the draft must contain a question."
    )
    avoid_phrases: list[str] | None = Field(
        default=None, description="Phrases to exclude; up to 20 items."
    )

    @field_validator("avoid_phrases")
    @classmethod
    def validate_avoid_phrases(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        if len(value) > 20:
            raise ValueError("avoid_phrases can have at most 20 items.")
        for phrase in value:
            if not (1 <= len(phrase) <= 60):
                raise ValueError("Each avoid phrase must be between 1 and 60 characters.")
        return value


class Options(BaseModel):
    emoji: bool = Field(default=False, description="Allow emojis in drafts.")
    uk_english: bool = Field(default=True, description="Use UK English spelling by default.")


class DraftRequest(BaseModel):
    incoming_message: str = Field(
        ...,
        min_length=1,
        max_length=8000,
        description="Incoming user message or email body.",
    )
    context: str | None = Field(
        default=None,
        max_length=4000,
        description="Optional extra context about thread or user.",
    )
    channel: Channel = Field(default="email", description="Delivery channel.")
    tone: Tone = Field(default="professional", description="Requested tone.")
    constraints: Constraints | None = None
    options: Options | None = None


class Draft(BaseModel):
    label: str
    text: str


class DraftResponse(BaseModel):
    request_id: str
    detected_tone: str
    channel_applied: Channel
    drafts: list[Draft] = Field(..., min_length=3, max_length=3)
    notes: str
    confidence_score: float = Field(ge=0.0, le=1.0)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str = "smart-reply-service"
