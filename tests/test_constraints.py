from app.api.schemas import Constraints
from app.services.constraints import check_constraints, adjust_text_for_violations


def test_check_constraints_detects_violations():
    constraints = Constraints(max_words=5, must_include_question=True, avoid_phrases=["ASAP"])
    text = "Please send ASAP. No question here."
    result = check_constraints(text, constraints)
    assert result["within_max_words"] is False
    assert result["includes_question"] is False
    assert result["avoids_phrases"] is False
    assert set(result["violations"]) == {"max_words", "must_include_question", "avoid_phrases"}


def test_adjust_text_for_violations():
    constraints = Constraints(max_words=5, must_include_question=True, avoid_phrases=["ASAP"])
    text = "Please send ASAP. No question here."
    adjusted = adjust_text_for_violations(text, constraints)
    result = check_constraints(adjusted, constraints)
    assert result["within_max_words"]
    assert result["includes_question"]
    assert result["avoids_phrases"]
