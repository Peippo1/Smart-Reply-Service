import json
import logging
import time
from textwrap import shorten
from typing import Iterable

from pydantic import ValidationError

from app.api.schemas import Draft, DraftRequest, DraftResponse, Tone
from app.core.config import get_settings
from app.services.prompts import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


def _stub_drafts(request: DraftRequest) -> DraftResponse:
    """
    Lightweight fallback when no OpenAI key is configured.
    Keeps the service usable in local/dev without external calls.
    """
    base_text = (
        f"Thanks for reaching out. {request.incoming_message.strip()} "
        f"{request.context or ''}".strip()
    )

    flavours: list[tuple[str, str]] = [
        ("Here is a polished reply that keeps things clear.", request.tone),
        ("A warmer, more personable take.", "friendly"),
        ("A crisp version that gets straight to the point.", "concise"),
    ]

    def apply_constraints(text: str) -> str:
        constraints = request.constraints
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
            result = shorten(result, width=constraints.word_limit * 6, placeholder="...")
        return result

    drafts: list[DraftCandidate] = []
    for idx, (preface, tone) in enumerate(flavours):
        text = apply_constraints(f"{preface} {base_text}")
        drafts.append(
            Draft(
                label=f"Option {idx + 1}",
                text=text,
            )
        )
    return DraftResponse(
        drafts=drafts,
        request_id="stub",
        detected_tone=request.tone,
        channel_applied=request.channel,
        notes="Stub generator used (no OpenAI key).",
        confidence_score=0.75,
    )


def generate_reply_drafts(request: DraftRequest) -> DraftResponse:
    """
    Call OpenAI Responses API and return validated DraftResponse.
    Retries on JSON parse/validation failures (max 2 retries).
    Falls back to a local stub when no API key is set.
    """
    settings = get_settings()
    start = time.perf_counter()

    if not settings.openai_api_key:
        logger.warning("openai.key.missing - returning stub drafts")
        result = _stub_drafts(request)
        latency_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "drafts.generated.stub",
            extra={"request_id": "stub", "latency_ms": round(latency_ms, 2)},
        )
        return result

    # Import here so tests can run without the openai package installed.
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - exercised only in dev without deps
        raise RuntimeError(
            "openai package is required when SMART_REPLY_OPENAI_API_KEY is set."
        ) from exc

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    user_prompt = build_user_prompt(request)

    max_retries = 2
    attempt = 0
    last_error: Exception | None = None

    while attempt <= max_retries:
        attempt += 1
        response = client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.6,
            max_output_tokens=600,
        )
        request_id = getattr(response, "id", None)

        try:
            content_text = getattr(response, "output_text", None) or response.output[0].content[0].text
            parsed = json.loads(content_text)
            result = DraftResponse.model_validate(parsed)
            latency_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "openai.responses.success",
                extra={
                    "request_id": request_id,
                    "latency_ms": round(latency_ms, 2),
                    "attempt": attempt,
                },
            )
            return result
        except (json.JSONDecodeError, ValidationError, AttributeError) as err:
            last_error = err
            logger.warning(
                "openai.responses.parse_failure",
                extra={"request_id": request_id, "attempt": attempt, "error": str(err)},
            )
            if attempt > max_retries:
                raise

    # Should never reach here
    raise RuntimeError(f"Failed to parse OpenAI response after {max_retries + 1} attempts: {last_error}")
