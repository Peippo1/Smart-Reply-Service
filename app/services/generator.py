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


def _context_clause(keyword: str | None) -> str:
    """
    Produce a short, natural clause to ground the draft in context.
    Avoids awkward phrases like 'this context' or 'the this context'.
    """
    if keyword:
        return f"given this is for {keyword}"
    return "given the context here"


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

    clause = _context_clause(keyword)

    if request.channel == "slack":
        direct = f"{base} ({clause})" if keyword else base
        friendly = f"Hey team, {base} ({clause}). Appreciate it!" if keyword else f"Hey team, {base} Appreciate it!"
        action = f"{base} ({clause}). can we align on next steps today?"
    elif request.channel == "linkedin":
        direct = f"{base} ({clause})" if keyword else base
        friendly = f"Appreciate the perspective—{base} ({clause})" if keyword else f"Appreciate the perspective. {base}"
        action = f"{base} If you’re open to it, happy to connect and compare notes on {keyword or 'this'}."
    else:  # email or other
        direct = f"{base} ({clause})" if keyword else base
        friendly = f"Thanks for sharing. {base} ({clause})" if keyword else f"Thanks for sharing. {base}"
        action = f"{base} ({clause}). when do you need this by?"

    drafts = [
        Draft(label="Direct", text=direct),
        Draft(label="Friendly", text=friendly),
        Draft(label="Action-oriented", text=action),
    ]
    return drafts
