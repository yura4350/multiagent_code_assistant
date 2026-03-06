"""
Tests for TestingAgent
Run with: python -m pytest tests/agents/test_testing_agent.py
"""
import json
from unittest.mock import MagicMock, mock_open, patch

from src.agents.testing_agent import TestingAgent
from src.models.issue import Issue
from src.models.suggestion import Suggestion

MOCK_ISSUES_JSON = """[
    {"line": 3, "message": "Use enumerate()", "severity": "warning",
     "rule_id": "range_len_enumerate", "column": 0}
]"""

def _set_llm_env(monkeypatch):
    monkeypatch.setenv("LITELLM_TOKEN", "test-token")
    monkeypatch.setenv("LLM_API_URL", "https://example.test/v1")
    monkeypatch.setenv("MODEL_ID", "GPT 4.1")


def make_mock_response(content: str) -> MagicMock:
    """Helper to create a mock OpenAI response."""
    mock_response = MagicMock()
    # Create a mock for choices[0].message.content
    mock_message = MagicMock()
    mock_message.content = content
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    return mock_response

@patch("src.agents.testing_agent.OpenAI")
def test_tests_scan(mock_openai, monkeypatch):
    """Test that scan() parses LLM response into Issue objects."""
    _set_llm_env(monkeypatch)
    mock_openai.return_value.chat.completions.create.return_value = (
        make_mock_response(MOCK_ISSUES_JSON)
    )
    agent = TestingAgent()

    # Mock _read_file to avoid actual disk access
    with patch.object(TestingAgent, '_read_file', return_value="for i in range(len(x)): pass"):
        issues = agent.scan("data/processor.py")

    assert len(issues) > 0
    assert issues[0].line == 3
    assert issues[0].rule_id == "range_len_enumerate"

@patch("src.agents.testing_agent.OpenAI")
def test_get_suggestions_success(mock_openai_class, monkeypatch):
    """Test the full flow of generating suggestions from issues."""
    _set_llm_env(monkeypatch)
    mock_client = mock_openai_class.return_value

    # The JSON the LLM returns
    mock_llm_content = json.dumps([{
        "issue": {"line": 10, "message": "Missing test", "severity": "warning", "rule_id": "test-gap", "column": 0},
        "original_code": "def my_func(): pass",
        "fixed_code": "def test_my_func(): assert my_func() is None",
        "rationale": "Testing return value",
        "confidence": 1.0
    }])

    mock_client.chat.completions.create.return_value = make_mock_response(mock_llm_content)

    agent = TestingAgent()

    # We create an issue that matches the rule_id in the mock JSON above
    sample_issue = Issue(
        line=10,
        message="Missing test",
        severity="warning",
        rule_id="test-gap",
        column=0
    )
    sample_code = "def my_func():\n    pass"

    suggestions = agent.get_suggestions([sample_issue], sample_code)

    # Assertions
    assert len(suggestions) == 1
    assert suggestions[0].issue.rule_id == "test-gap"
    assert "def test_my_func()" in suggestions[0].fixed_code

    # Verify OpenAI was called correctly
    args, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs["model"] == "GPT 4.1"
    assert "test-gap" in kwargs["messages"][0]["content"]

@patch("builtins.open", new_callable=mock_open)
def test_apply_suggestions_success(mock_file):
    """Test that apply() appends valid test code to the correct file."""
    agent = TestingAgent()

    # 1. Create a valid suggestion (contains 'def test_')
    issue = Issue(line=5, message="msg", severity="info", rule_id="r1", column=0)
    valid_suggestion = Suggestion(
        issue=issue,
        original_code="",
        fixed_code="def test_new_feature():\n    assert True",
        rationale="Adding missing test",
        confidence=1.0
    )

    # 2. Create an invalid suggestion (fails validate() check)
    invalid_suggestion = Suggestion(
        issue=issue,
        original_code="",
        fixed_code="print('this is not a test')",
        rationale="Bad suggestion",
        confidence=0.5
    )

    # 3. Mock the path resolution to return a dummy path
    with patch.object(TestingAgent, '_get_test_file_path', return_value="tests/test_dummy.py"):
        agent.apply([valid_suggestion, invalid_suggestion], "src/dummy.py")

    # 4. Assertions
    # Ensure it tried to open the correct file in append mode ('a')
    mock_file.assert_called_once_with("tests/test_dummy.py", "a", encoding="utf-8")

    # Check that ONLY the valid code was written
    handle = mock_file()
    written_data = "".join(call.args[0] for call in handle.write.call_args_list)

    assert "def test_new_feature()" in written_data
    assert "print('this is not a test')" not in written_data
