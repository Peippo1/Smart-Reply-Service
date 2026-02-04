import json
import logging
import time
import uuid
from textwrap import shorten
from typing import Iterable

from pydantic import ValidationError

from app.api.schemas import Draft, DraftRequest, DraftResponse, Tone
from app.core.config import get_settings
from app.services.constraints import adjust_text_for_violations, check_constraints
from app.services.formatting import apply_channel_format
from app.services.generator import generate_base_drafts
from app.services.prompts import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


def _stub_drafts(request: DraftRequest) -> DraftResponse:
    """
    Lightweight fallback when no OpenAI key is configured.
    Keeps the service usable in local/dev without external calls.
    """
    base_drafts = generate_base_drafts(request)

    def apply_constraints(text: str) -> tuple[str, bool]:
        constraints = request.constraints
        changed = False
        if constraints is None:
            return text, changed
        result = text
        if constraints.must_include_question and "?" not in result:
            result = f"{result} What do you think?"
            changed = True
        if constraints.avoid_phrases:
            for phrase in constraints.avoid_phrases:
                if phrase.lower() in result.lower():
                    result = result.replace(phrase, "").strip()
                    changed = True
        if constraints.max_words:
            before = result
            result = shorten(result, width=constraints.max_words * 6, placeholder="…")
            changed = changed or result != before
        return result, changed

    drafts: list[Draft] = []
    formatting_hits = 0.0
    constraint_hits = 0.0
    all_constraints_satisfied: list[bool] = []
    length_reasonable_flags: list[bool] = []
    context_flags: list[bool] = []

    emoji_enabled = bool(request.options and request.options.emoji)

    for draft in base_drafts:
        text, constraint_changed = apply_constraints(draft.text)
        constraint_hits += int(constraint_changed)
        evaluation = check_constraints(text, request.constraints)
        if evaluation["violations"]:
            text = adjust_text_for_violations(text, request.constraints)
            evaluation = check_constraints(text, request.constraints)

        formatted_text, formatting_score = apply_channel_format(
            request.channel, text, emoji_enabled=emoji_enabled
        )
        formatting_hits += formatting_score
        drafts.append(Draft(label=draft.label, text=formatted_text))

        all_constraints_satisfied.append(
            evaluation["within_max_words"] and evaluation["includes_question"] and evaluation["avoids_phrases"]
        )
        length_reasonable_flags.append(
            evaluation["within_max_words"]
            if request.constraints and request.constraints.max_words
            else len(formatted_text.split()) <= 160
        )
        if request.context:
            context_flags.append(request.context.lower() in formatted_text.lower())
        else:
            context_flags.append(True)

    baseline = 0.70
    formatting_component = 0.10 if (formatting_hits / len(base_drafts)) > 0 else 0.0
    constraints_component = 0.10 if (request.constraints and all(all_constraints_satisfied)) else 0.0
    length_component = 0.05 if all(length_reasonable_flags) else 0.0
    context_component = 0.05 if (request.context and all(context_flags)) else 0.0

    confidence_raw = baseline + formatting_component + constraints_component + length_component + context_component

    if request.constraints and all(all_constraints_satisfied) and request.context and all(context_flags):
        confidence = min(1.0, round(confidence_raw, 2))
    else:
        confidence = min(0.95, round(confidence_raw, 2))
    notes = "Applied channel formatting; enforced constraints; context referenced." if request.context else \
        "Applied channel formatting; enforced constraints."
    return DraftResponse(
        drafts=drafts,
        request_id=uuid.uuid4().hex[:8],
        detected_tone="neutral-professional",
        channel_applied=request.channel,
        notes=notes,
        confidence_score=confidence,
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
