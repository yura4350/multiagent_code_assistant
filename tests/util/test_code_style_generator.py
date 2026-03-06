"""Tests for code_style_generator.Generator"""
from src.util.code_style_generator import Generator
from src.util.issue import Issue


def _make_issue(rule_id="E501", message="line too long"):
    return Issue(line=1, message=message, severity="error", rule_id=rule_id, column=0)


def test_get_suggestions_empty_issues_returns_empty():
    assert Generator().get_suggestions([], "some code") == []


def test_get_suggestions_one_per_issue():
    issues = [_make_issue("E501"), _make_issue("W291", "trailing whitespace")]
    suggestions = Generator().get_suggestions(issues, "code")
    assert len(suggestions) == 2


def test_get_suggestions_rationale_contains_rule_id_and_message():
    issue = _make_issue("E501", "line too long")
    suggestion = Generator().get_suggestions([issue], "code")[0]
    assert "E501" in suggestion.rationale
    assert "line too long" in suggestion.rationale


def test_get_suggestions_confidence_is_one():
    suggestion = Generator().get_suggestions([_make_issue()], "code")[0]
    assert suggestion.confidence == 1.0


def test_get_suggestions_issue_is_preserved():
    issue = _make_issue("F401")
    suggestion = Generator().get_suggestions([issue], "code")[0]
    assert suggestion.issue is issue
