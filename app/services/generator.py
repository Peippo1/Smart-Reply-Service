"""
Base draft generator interface (stub). Intended to be swapped with an LLM-backed implementation.
"""

from app.api.schemas import Draft, DraftRequest


def _context_keyword(context: str | None) -> str | None:
    """
    Extract a simple keyword from context to subtly ground drafts without copying verbatim.
    """
    if not context:
        return None
    tokens = context.split()
    for tok in tokens:
        cleaned = tok.strip(",.!?").lower()
        if cleaned:
            return cleaned
    return None


def _extract_phrase(context: str | None) -> str | None:
    """
    Extract a meaningful noun phrase from context, stripping common lead-ins.
    Returns lowercase phrase or None if unusable.
    """
    if not context:
        return None
    lowered = context.strip().lower()
    for prefix in ("this is for", "this relates to", "for", "regarding", "about"):
        if lowered.startswith(prefix):
            lowered = lowered[len(prefix):].strip()
            break
    lowered = lowered.strip(" .,!?:;")
    if not lowered or lowered == "this":
        return None
    return lowered


def generate_base_drafts(request: DraftRequest) -> list[Draft]:
    """
    Produce three simple drafts based on the incoming request.
    Currently stubbed; replace with LLM outputs later.
    Drafts differ by voice (Direct/Friendly/Action-oriented) and lightly weave in context.
    """
    base = request.incoming_message.strip()
    phrase = _extract_phrase(request.context)

    if request.channel == "slack":
        direct = f"{base}" if not phrase else f"Given this is for {phrase}, {base}"
        friendly = f"Hey team, when you have a moment, {base}" if not phrase else f"Hey team, when you have a moment, and since this is for {phrase}, {base}"
        action = f"{base} Can we align on next steps today?" if not phrase else f"{base} It’s for {phrase}. Can we align on next steps today?"
    elif request.channel == "linkedin":
        direct = f"{base}" if not phrase else f"As this is for {phrase}, {base}"
        friendly = f"Appreciate the perspective. {base}" if not phrase else f"Appreciate the perspective—since this is for {phrase}, {base}"
        action = f"{base} If you’re open to it, happy to connect and compare notes." if not phrase else f"{base} If you’re open to it, happy to connect and compare notes for {phrase}."
    else:  # email or other
        direct = f"{base}" if not phrase else f"Given this is for {phrase}, {base}"
        friendly = (
            f"When you have a moment, could you {base.lower()}"
            if not phrase
            else f"When you have a moment—since this is for {phrase}—could you {base.lower()}"
        )
        if "metrics" in base.lower() or "reports" in base.lower() or "figures" in base.lower():
            deadline_q = "When do you need them by?"
        else:
            deadline_q = "What deadline are you working to?"
        action = f"{base} {deadline_q}" if not phrase else f"Given this is for {phrase}, {base} {deadline_q}"

    drafts = [
        Draft(label="Direct", text=direct),
        Draft(label="Friendly", text=friendly),
        Draft(label="Action-oriented", text=action),
    ]
    return drafts
