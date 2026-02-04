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
        Draft(label="Option 1", text=f"Quick summary: {base}"),
        Draft(label="Option 2", text=f"Friendly take: {base}"),
        Draft(label="Option 3", text=f"Action-oriented: {base}"),
    ]
    return drafts
