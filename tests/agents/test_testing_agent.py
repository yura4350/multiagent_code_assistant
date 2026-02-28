"""
Tests for IdiomsAgent
Run with: python -m pytest tests/agents/test_testing_agent.py
"""
from unittest.mock import MagicMock, patch

from src.agents.testing_agent import TestingAgent
from src.models.issue import Issue
from src.models.suggestion import Suggestion

MOCK_ISSUES_JSON = """[
    {"line": 3, "message": "Use enumerate()", "severity": "warning",
     "rule_id": "range_len_enumerate", "column": 0}
]"""

MOCK_SUGGESTIONS_JSON = """[
    {
        "issue": {"line": 3, "message": "Use enumerate()", "severity": "warning",
                  "rule_id": "range_len_enumerate", "column": 0},
        "original_code": "for i in range(len(names)):",
        "fixed_code": "for i, name in enumerate(names):",
        "rationale": "enumerate() is more Pythonic.",
        "confidence": 1.0
    }
]"""


def make_mock_response(content: str) -> MagicMock:
    """Helper to create a mock OpenAI response."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = content
    return mock_response


@patch("src.agents.testing_agent.OpenAI")
def test_tests_scan(mock_openai):
    """Test that scan() parses LLM response into Issue objects."""
    mock_openai.return_value.chat.completions.create.return_value = (
        make_mock_response(MOCK_ISSUES_JSON)
    )
    agent = TestingAgent()
    issues = agent.scan("data/processor.py")

    assert len(issues) > 0
    assert issues[0].line == 3
    assert issues[0].rule_id == "range_len_enumerate"
    assert issues[0].severity == "warning"