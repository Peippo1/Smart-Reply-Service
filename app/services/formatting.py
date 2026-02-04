"""
Channel-aware formatting utilities for draft replies.
"""

import re
from textwrap import shorten

from app.api.schemas import Channel


def normalize_terminal_punctuation(text: str) -> str:
    """
    Prevent trailing double punctuation like '?.', '!.' or '..'.
    If text already ends with . ? ! leave it; otherwise append '.'.
    """
    stripped = text.rstrip()
    if stripped.endswith((".", "?", "!")):
        return stripped
    return f"{stripped}."


def _ensure_email_greeting(text: str) -> tuple[str, bool]:
    if re.match(r"^(hi|hello|dear)\b", text.strip(), re.IGNORECASE):
        return text, False
    greeting = "Hi there,"
    return f"{greeting}\n\n{text.strip()}", True


def _ensure_email_signoff(text: str) -> tuple[str, bool]:
    if re.search(r"(regards|cheers|sincerely|thanks)[,.]?\s*$", text.strip(), re.IGNORECASE):
        return text, False
    signoff = "Best regards,\nTim"
    base = normalize_terminal_punctuation(text.rstrip())
    return f"{base}\n\n{signoff}", True


def _ensure_blank_lines(text: str) -> tuple[str, bool]:
    if "\n\n" in text:
        return text, False
    if "\n" in text:
        return text.replace("\n", "\n\n"), True
    return text, False


def _word_count(text: str) -> int:
    return len(text.split())


def _truncate_slack(text: str) -> tuple[str, bool]:
    if _word_count(text) <= 60:
        return text, False
    truncated = shorten(text, width=360, placeholder="…")
    return truncated, True


def _bullets_from_sentences(text: str) -> tuple[str, bool]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if len(sentences) < 2:
        return text, False
    bullets = "\n".join(f"- {s}" for s in sentences)
    return bullets, True


def _add_emojis(text: str) -> tuple[str, bool]:
    if any(ch in text for ch in "😀🙂👍🙏🤝✨🎯✅"):
        return text, False
    additions = ["🙂", "👍"]
    return f"{text} {' '.join(additions)}", True


def _split_linkedin_paras(text: str) -> tuple[str, bool]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if not sentences:
        return text, False
    chunks = []
    current = []
    for sent in sentences:
        current.append(sent)
        if len(" ".join(current).split()) >= 50 and len(chunks) < 2:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    if len(chunks) <= 1:
        return text, False
    return "\n\n".join(chunks[:3]), True


def _ensure_linkedin_cta(text: str) -> tuple[str, bool]:
    if re.search(r"(chat|talk|connect|let me know)", text, re.IGNORECASE):
        return text, False
    cta = "If you’re open to it, happy to connect and compare notes."
    return f"{text.rstrip()} {cta}", True


def apply_channel_format(channel: Channel, text: str, emoji_enabled: bool = False) -> tuple[str, float]:
    """
    Apply channel-specific formatting rules. Returns (formatted_text, formatting_score 0-1).
    """
    applied = 0
    if channel == "email":
        text, changed = _ensure_email_greeting(text)
        applied += changed
        text, changed = _ensure_blank_lines(text)
        applied += changed
        text, changed = _ensure_email_signoff(text)
        applied += changed
        text = normalize_terminal_punctuation(text)
        return text, applied / 3

    if channel == "slack":
        text, changed = _bullets_from_sentences(text)
        applied += changed
        text, trunc = _truncate_slack(text)
        applied += trunc
        if emoji_enabled:
            text, emoji_added = _add_emojis(text)
            applied += emoji_added
        return text, applied / 3

    if channel == "linkedin":
        text, split = _split_linkedin_paras(text)
        applied += split
        text, cta_added = _ensure_linkedin_cta(text)
        applied += cta_added
        return text, applied / 2

    return text, 0.0
