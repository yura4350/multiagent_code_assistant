"""
Tests for Issue model
Run with: python -m pytest tests/models/test_issue.py
"""

from src.util.issue import Issue


def test_create_issue():
    """Test creating a basic Issue object with all fields"""
    issue = Issue(
        line=5,
        message="Line too long",
        severity="warning",
        rule_id="C0301",
        column=10,
    )

    assert issue.line == 5
    assert issue.column == 10
    assert issue.message == "Line too long"
    assert issue.severity == "warning"
    assert issue.rule_id == "C0301"
