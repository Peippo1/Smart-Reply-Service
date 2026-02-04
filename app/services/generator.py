"""
Base draft generator interface (stub). Intended to be swapped with an LLM-backed implementation.
"""

from app.api.schemas import Draft, DraftRequest


def generate_base_drafts(request: DraftRequest) -> list[Draft]:
    """
    Produce three simple drafts based on the incoming request.
    Currently stubbed; replace with LLM outputs later.
    """
    base = request.incoming_message.strip()
    context_snippet = f" ({request.context})" if request.context else ""

    if request.channel == "slack":
        direct = f"{base}"
        friendly = f"Hey team, {base}{context_snippet} Appreciate it!"
        action = f"{base}{context_snippet} Can we align on next steps today?"
    elif request.channel == "linkedin":
        direct = f"{base}"
        friendly = f"Appreciate you raising this{context_snippet}. {base}"
        action = f"{base}{context_snippet} Would you be open to a quick chat to align next steps?"
    else:  # email or other
        direct = f"{base}"
        friendly = f"Thanks for flagging this{context_snippet}. {base}"
        action = f"{base}{context_snippet} Please confirm the next steps or timeline."

    drafts = [
        Draft(label="Direct", text=direct),
        Draft(label="Friendly", text=friendly),
        Draft(label="Action-oriented", text=action),
    ]
    return drafts
