"""
Tests for IdiomsAgent
Run with: python -m pytest tests/agents/test_idioms_agent.py
"""
from unittest.mock import MagicMock, patch

from src.agents.idioms_agent import IdiomsAgent
from src.model.llm_generator import LLMGenerator
from src.model.llm_scanner import LLMScanner
from src.model.prompt_registry import PromptRegistry
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
    mock_response = MagicMock()
    mock_response.choices[0].message.content = content
    return mock_response


def _set_llm_env(monkeypatch):
    monkeypatch.setenv("LITELLM_TOKEN", "test-token")
    monkeypatch.setenv("LLM_API_URL", "https://example.test/v1")
    monkeypatch.setenv("MODEL_ID", "GPT 4.1")


@patch("src.agents.idioms_agent.OpenAI")
def test_idioms_scan(mock_openai, monkeypatch):
    _set_llm_env(monkeypatch)
    mock_openai.return_value.chat.completions.create.return_value = make_mock_response(
        MOCK_ISSUES_JSON
    )

    agent = IdiomsAgent()
    issues = agent.scan("data/sample_bad_idioms.py")

    assert len(issues) > 0
    assert issues[0].line == 3
    assert issues[0].rule_id == "range_len_enumerate"
    assert issues[0].severity == "warning"


@patch("src.agents.idioms_agent.OpenAI")
@patch("src.model.prompt_registry.PromptRegistry.load")
def test_idioms_get_suggestions(mock_load_prompt, mock_openai, monkeypatch):
    _set_llm_env(monkeypatch)

    # Keep prompt rendering deterministic in test.
    mock_load_prompt.return_value = (
        "Code:\n{{ code }}\n\nIssues:\n{{ issues_json }}"
    )
    mock_openai.return_value.chat.completions.create.return_value = make_mock_response(
        MOCK_SUGGESTIONS_JSON
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

    suggestions = agent.get_suggestions(
        issues, "for i in range(len(names)):\n    print(names[i])"
    )

    assert len(suggestions) > 0
    assert suggestions[0].original_code == "for i in range(len(names)):"
    assert suggestions[0].fixed_code == "for i, name in enumerate(names):"
    assert suggestions[0].confidence == 1.0


@patch("src.agents.idioms_agent.OpenAI")
def test_idioms_apply_suggestions(mock_openai, monkeypatch, tmp_path):
    _set_llm_env(monkeypatch)
    mock_openai.return_value.chat.completions.create.return_value = make_mock_response(
        "for i, name in enumerate(names):\n    print(i, name)"
    )

    agent = IdiomsAgent()
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


def test_read_file(tmp_path, monkeypatch):
    _set_llm_env(monkeypatch)
    test_file = tmp_path / "sample.py"
    test_file.write_text("print('hello')\n")

    agent = IdiomsAgent()
    content = agent._read_file(str(test_file))
    assert content == "print('hello')\n"


def test_llm_scanner_parse_issues_invalid_json(monkeypatch):
    dummy_client = MagicMock()
    scanner = LLMScanner(
        client=dummy_client,
        model="GPT 4.1",
        prompt_registry=PromptRegistry(),
    )
    result = scanner._parse_issues("not valid json")
    assert result == []


def test_llm_generator_parse_suggestions_invalid_json():
    dummy_client = MagicMock()
    generator = LLMGenerator(
        client=dummy_client,
        model="GPT 4.1",
        prompt_registry=PromptRegistry(),
    )
    result = generator._parse_suggestions("not valid json", [])
    assert result == []
