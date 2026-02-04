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
    drafts = [
        Draft(label="Direct", text=f"{base}"),
        Draft(label="Friendly", text=f"Thanks for raising this—{base}"),
        Draft(label="Action-oriented", text=f"{base} Could you confirm the next step or timing?"),
    ]
    return drafts
