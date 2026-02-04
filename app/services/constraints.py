"""
Constraint evaluation and light enforcement helpers.
"""

from __future__ import annotations

from textwrap import shorten
from typing import List, Optional

from app.api.schemas import Constraints


def check_constraints(text: str, constraints: Optional[Constraints]) -> dict:
    """
    Evaluate a draft against constraints.

    Returns a dict:
        within_max_words: bool
        includes_question: bool
        avoids_phrases: bool
        violations: list[str]
    """
    if not constraints:
        return {
            "within_max_words": True,
            "includes_question": True,
            "avoids_phrases": True,
            "violations": [],
        }

    violations: List[str] = []
    words = text.split()
    within_max = True
    if constraints.max_words and len(words) > constraints.max_words:
        within_max = False
        violations.append("max_words")

    includes_question = True
    if constraints.must_include_question and "?" not in text:
        includes_question = False
        violations.append("must_include_question")

    avoids_phrases = True
    if constraints.avoid_phrases:
        for phrase in constraints.avoid_phrases:
            if phrase.lower() in text.lower():
                avoids_phrases = False
                if "avoid_phrases" not in violations:
                    violations.append("avoid_phrases")
                break

    return {
        "within_max_words": within_max,
        "includes_question": includes_question,
        "avoids_phrases": avoids_phrases,
        "violations": violations,
    }


def adjust_text_for_violations(text: str, constraints: Optional[Constraints]) -> str:
    """
    Apply a single pass of gentle adjustments to address violations.
    """
    if not constraints:
        return text

    current = text
    evaluation = check_constraints(current, constraints)

    if "max_words" in evaluation["violations"] and constraints.max_words:
        sentences = current.split(". ")
        if len(sentences) > 1:
            sentences = sentences[: max(1, len(sentences) - 1)]
            current = ". ".join(sentences).strip()
        words = current.split()
        if len(words) > constraints.max_words:
            current = " ".join(words[: constraints.max_words])
        current = shorten(current, width=constraints.max_words * 6, placeholder="…")
        # Final hard clamp to word count
        words = current.split()
        if len(words) > constraints.max_words:
            current = " ".join(words[: constraints.max_words])

    if "must_include_question" in evaluation["violations"]:
        if not current.strip().endswith("?"):
            current = f"{current.rstrip('. ')} What do you think?"

    if "avoid_phrases" in evaluation["violations"] and constraints.avoid_phrases:
        for phrase in constraints.avoid_phrases:
            current = current.replace(phrase, "").strip()

    # Final clamp to max_words after all adjustments
    if constraints.max_words:
        words = current.split()
        if len(words) > constraints.max_words:
            current = " ".join(words[: constraints.max_words])

    if constraints.must_include_question and "?" not in current:
        words = current.split()
        if constraints.max_words and len(words) >= constraints.max_words:
            words[-1] = "?"
            current = " ".join(words)
        else:
            current = f"{current} ?"

    return current
