from app.services.formatting import apply_channel_format
from app.services.formatting import normalize_terminal_punctuation


def test_email_formatting_adds_greeting_and_signoff():
    text = "Thanks for the update."
    formatted, score = apply_channel_format("email", text)
    assert "Hi" in formatted.splitlines()[0]
    assert "Best regards" in formatted
    assert score > 0
    assert ".." not in formatted
    assert "?." not in formatted


def test_slack_formatting_uses_bullets_and_truncates():
    text = "Sentence one. Sentence two provides more detail. Sentence three wraps up with extra info."
    formatted, score = apply_channel_format("slack", text)
    assert formatted.startswith("- ")
    assert score > 0


def test_linkedin_formatting_adds_cta():
    text = "I enjoyed your post on product strategy."
    formatted, score = apply_channel_format("linkedin", text)
    assert "happy to connect" in formatted.lower()
    assert score > 0


def test_normalize_terminal_punctuation():
    assert normalize_terminal_punctuation("Hello?") == "Hello?"
    assert normalize_terminal_punctuation("Hello!") == "Hello!"
    assert normalize_terminal_punctuation("Hello.") == "Hello."
    assert normalize_terminal_punctuation("Hello") == "Hello."
