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


def generate_base_drafts(request: DraftRequest) -> list[Draft]:
    """
    Produce three simple drafts based on the incoming request.
    Currently stubbed; replace with LLM outputs later.
    Drafts differ by voice (Direct/Friendly/Action-oriented) and lightly weave in context.
    """
    base = request.incoming_message.strip()
    keyword = _context_keyword(request.context)
    def with_context(prefix: str) -> str:
        if not keyword:
            return ""
        return f"{prefix} {keyword} context, "

    if request.channel == "slack":
        direct = f"{with_context('With the')}{base}"
        friendly = f"Hey team, {with_context('since it\'s about the').strip()} {base} Appreciate it!"
        action = f"{with_context('Given the')} {base} Can we align on next steps today?"
    elif request.channel == "linkedin":
        direct = f"Since you're working on {keyword}," if keyword else base
        direct = f"{direct} {base}" if keyword else direct
        friendly = f"Appreciate the perspective on {keyword}, {base}" if keyword else f"Appreciate the perspective. {base}"
        action = f"{base} If you’re open to it, happy to connect and compare notes on {keyword or 'this'}."
    else:  # email or other
        direct = f"{with_context('Given the')}{base}"
        friendly = f"Thanks for flagging this{f' in {keyword}' if keyword else ''}. {base}"
        action = f"{with_context('Considering the')}{base} Please confirm the next steps or timeline."

    drafts = [
        Draft(label="Direct", text=direct),
        Draft(label="Friendly", text=friendly),
        Draft(label="Action-oriented", text=action),
    ]
    return drafts
