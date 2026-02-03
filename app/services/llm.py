from textwrap import shorten
from typing import Iterable

from app.api.schemas import Constraints, DraftCandidate, DraftRequest, Tone


def _apply_constraints(text: str, constraints: Constraints | None) -> str:
    if constraints is None:
        return text

    result = text
    if constraints.must_include_question and "?" not in result:
        result = f"{result} What do you think?"

    if constraints.avoid_phrases:
        for phrase in constraints.avoid_phrases:
            if phrase.lower() in result.lower():
                result = result.replace(phrase, "").strip()

    if constraints.word_limit:
        # shorten keeps whole words and appends ellipsis if truncated
        result = shorten(result, width=constraints.word_limit * 6, placeholder="...")

    return result


def _confidence_for_tone(tone: Tone, channel: str) -> float:
    base = {
        "friendly": 0.74,
        "professional": 0.82,
        "concise": 0.78,
        "assertive": 0.76,
        "apologetic": 0.7,
    }.get(tone, 0.7)

    channel_modifier = 0.05 if channel in {"email", "slack"} else -0.02
    return round(min(1.0, max(0.5, base + channel_modifier)), 2)


def generate_drafts(request: DraftRequest) -> Iterable[DraftCandidate]:
    base_text = (
        f"Thanks for reaching out. {request.message.strip()} "
        f"{request.context or ''}".strip()
    )

    flavours: list[tuple[str, Tone]] = [
        ("Here is a polished reply that keeps things clear.", request.tone),
        ("A warmer, more personable take.", "friendly"),
        ("A crisp version that gets straight to the point.", "concise"),
    ]

    for preface, tone in flavours:
        text = f"{preface} {base_text}"
        text = _apply_constraints(text, request.constraints)
        yield DraftCandidate(
            text=text,
            tone_label=tone,  # type: ignore[arg-type]
            rationale=f"Aligned to {tone} tone for {request.channel}.",
            confidence=_confidence_for_tone(tone, request.channel),
        )

