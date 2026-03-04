"""
Tests for Suggestion model
Run with: python -m pytest tests/models/test_suggestion.py
"""

from src.models.issue import Issue
from src.models.suggestion import Suggestion


def test_create_suggestion():
    """Test creating a Suggestion with all fields"""
    issue = Issue(
        line=5,
        message="Line too long",
        severity="warning",
        rule_id="C0301",
        column=10,
    )

    suggestion = Suggestion(
        issue=issue,
        original_code="def myFunction(): ",
        fixed_code="def my_function(): ",
        rationale="Use snake_case for function names per PEP 8",
        confidence=0.95,
    )

    # Test all fields
    assert suggestion.issue == issue
    assert suggestion.original_code == "def myFunction(): "
    assert suggestion.fixed_code == "def my_function(): "
    assert suggestion.rationale == "Use snake_case for function names per PEP 8"
    assert suggestion.confidence == 0.95
