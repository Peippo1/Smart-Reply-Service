"""
Prompt templates for the Smart Reply service.

The goal is to make model behavior explicit and reproducible:
- SYSTEM_PROMPT enforces JSON-only output, safety, and style rules.
- build_user_prompt turns a DraftRequest into a compact, structured instruction.
"""

from app.api.schemas import DraftRequest


SYSTEM_PROMPT = (
    "You are Smart Reply, an assistant that returns ONLY valid JSON.\n"
    "- Output JSON and nothing else; no markdown, prefaces, or commentary.\n"
    "- Always produce exactly 3 drafts with distinct styles.\n"
    "- Obey the requested tone and channel etiquette; keep replies safe and professional.\n"
    "- Default to UK English spelling unless an explicit language override is provided."
)


def build_user_prompt(request: DraftRequest, language: str | None = None) -> str:
    """
    Build the user prompt for the Responses API.

    Parameters
    ----------
    request : DraftRequest
        Validated request payload from the API layer.
    language : str | None
        Optional language override; defaults to UK English to keep spelling consistent.

    Returns
    -------
    str
        A concise instruction block that the model will parse into JSON.
    """
    constraint_lines: list[str] = []
    if request.constraints:
        if request.constraints.max_words:
            constraint_lines.append(f"- max_words: {request.constraints.max_words}")
        if request.constraints.must_include_question:
            constraint_lines.append("- must_include_question: true")
        if request.constraints.avoid_phrases:
            constraint_lines.append(f"- avoid_phrases: {request.constraints.avoid_phrases}")
    constraint_block = "\n".join(constraint_lines) if constraint_lines else "None"

    language_pref = language or (
        "UK English (default)"
        if not request.options or request.options.uk_english
        else "User-specified language"
    )

    return (
        "Generate reply drafts for the following input.\n"
        f"- channel: {request.channel}\n"
        f"- tone: {request.tone}\n"
        f"- language: {language_pref}\n"
        f"- message: {request.incoming_message}\n"
        f"- context: {request.context or 'None'}\n"
        f"- constraints:\n{constraint_block}\n\n"
        "Schema:\n"
        "{\n"
        '  \"request_id\": str,\n'
        '  \"detected_tone\": str,\n'
        '  \"channel_applied\": str,\n'
        '  \"drafts\": [\n'
        "    {\"label\": str, \"text\": str}\n"
        "  ],\n"
        '  \"notes\": str,\n'
        '  \"confidence_score\": float\n'
        "}\n"
        "Rules:\n"
        "- Exactly 3 drafts; each draft must have a distinct style.\n"
        "- Keep answers concise and appropriate for the channel.\n"
        "- Respect all constraints and the specified language.\n"
        "- Return JSON only."
    )
