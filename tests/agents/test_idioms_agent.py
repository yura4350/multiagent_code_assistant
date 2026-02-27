"""
Tests for IdiomsAgent
Run with: python -m pytest tests/agents/test_idioms_agent.py
"""
from unittest.mock import MagicMock, patch

from src.agents.idioms_agent import IdiomsAgent
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


@patch("src.agents.idioms_agent.OpenAI")
def test_idioms_scan(mock_openai):
    """Test that scan() parses LLM response into Issue objects."""
    mock_openai.return_value.chat.completions.create.return_value = (
        make_mock_response(MOCK_ISSUES_JSON)
    )
    agent = IdiomsAgent()
    issues = agent.scan("data/sample_bad_idioms.py")

    assert len(issues) > 0
    assert issues[0].line == 3
    assert issues[0].rule_id == "range_len_enumerate"
    assert issues[0].severity == "warning"


@patch("src.agents.idioms_agent.OpenAI")
def test_idioms_generate_suggestions(mock_openai):
    """Test that generate_suggestions() parses LLM response into Suggestion objects."""
    mock_openai.return_value.chat.completions.create.return_value = (
        make_mock_response(MOCK_SUGGESTIONS_JSON)
    )
    agent = IdiomsAgent()
    issues = [
        Issue(
            line=3,
            message="Use enumerate()",
            severity="warning",
            rule_id="range_len_enumerate",
            column=0,
        )
    ]
    suggestions = agent.generate_suggestions(
        issues, "for i in range(len(names)):\n    print(names[i])"
    )

    assert len(suggestions) > 0
    assert suggestions[0].original_code == "for i in range(len(names)):"
    assert suggestions[0].fixed_code == "for i, name in enumerate(names):"
    assert suggestions[0].confidence == 1.0


@patch("src.agents.idioms_agent.OpenAI")
def test_idioms_apply_suggestions(mock_openai, tmp_path):
    """Test that apply() writes fixed code back to the file."""
    mock_openai.return_value.chat.completions.create.return_value = (
        make_mock_response("for i, name in enumerate(names):\n    print(i, name)")
    )
    agent = IdiomsAgent()

    # Create a temporary file to apply suggestions to
    test_file = tmp_path / "test_code.py"
    test_file.write_text("for i in range(len(names)):\n    print(names[i])\n")

    issue = Issue(
        line=3,
        message="Use enumerate()",
        severity="warning",
        rule_id="range_len_enumerate",
        column=0,
    )
    suggestion = Suggestion(
        issue=issue,
        original_code="for i in range(len(names)):",
        fixed_code="for i, name in enumerate(names):",
        rationale="More Pythonic.",
        confidence=1.0,
    )

    agent.apply([suggestion], str(test_file))
    result = test_file.read_text()
    assert "enumerate" in result


def test_read_file(tmp_path):
    """Test that _read_file() reads file content correctly."""
    test_file = tmp_path / "sample.py"
    test_file.write_text("print('hello')\n")

    agent = IdiomsAgent()
    content = agent._read_file(str(test_file))
    assert content == "print('hello')\n"


def test_parse_issues_invalid_json():
    """Test that _parse_issues() handles invalid JSON gracefully."""
    agent = IdiomsAgent()
    result = agent._parse_issues("not valid json")
    assert result == []


def test_parse_suggestions_invalid_json():
    """Test that _parse_suggestions() handles invalid JSON gracefully."""
    agent = IdiomsAgent()
    result = agent._parse_suggestions("not valid json", [])
    assert result == []