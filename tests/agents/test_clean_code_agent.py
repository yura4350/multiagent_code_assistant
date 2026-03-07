"""
Tests for CleanCodeAgent
Run with: python -m pytest tests/agents/test_clean_code_agent.py
"""
from unittest.mock import MagicMock, patch

from src.agents.clean_code_agent import CleanCodeAgent
from src.util.llm_generator import LLMGenerator
from src.util.llm_scanner import LLMScanner
from src.util.prompt_registry import PromptRegistry
from src.util.issue import Issue
from src.util.suggestion import Suggestion

MOCK_ISSUES_JSON = """[
    {"line": 1,
    "message": "Unused imports: 'os', 'sys', 'math' are imported but not used.",
    "severity": "warning",
    "rule_id": "unused-import",
    "column": 1}
]"""

MOCK_SUGGESTIONS_JSON = """[
    {
    "issue": {
      "line": 1,
      "message": "Unused imports: 'os', 'sys', 'math' are imported but not used.",
      "severity": "warning",
      "rule_id": "unused-import",
      "column": 1
    },
    "original_code": "import os, sys, json\\nimport os\\nimport math",
    "fixed_code": "import json",
    "rationale": "Removes unnecessary imports to reduce clutter and potential confusion. Only keep modules used in the code.",
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

@patch("src.agents.clean_code_agent.OpenAI")
def test_clean_code_scan(mock_openai, monkeypatch):
    _set_llm_env(monkeypatch)
    mock_openai.return_value.chat.completions.create.return_value = make_mock_response(
        MOCK_ISSUES_JSON
    )

    agent = CleanCodeAgent()
    issues = agent.scan("data/sample_bad_clean_code.py")

    assert len(issues) > 0
    assert issues[0].line == 1
    assert issues[0].rule_id == "unused-import"
    assert issues[0].severity == "warning"


@patch("src.agents.clean_code_agent.OpenAI")
@patch("src.util.prompt_registry.PromptRegistry.load")
def test_clean_code_get_suggestions(mock_load_prompt, mock_openai, monkeypatch):
    _set_llm_env(monkeypatch)

    mock_load_prompt.return_value = (
        "Code:\n{{ code }}\n\nIssues:\n{{ issues_json }}"
    )
    mock_openai.return_value.chat.completions.create.return_value = make_mock_response(
        MOCK_SUGGESTIONS_JSON
    )

    agent = CleanCodeAgent()
    issues = [
        Issue(
            line=1,
            message="Unused imports: 'os', 'sys', 'math' are imported but not used.",
            severity="warning",
            rule_id="unused-import",
            column=1,
        )
    ]

    suggestions = agent.get_suggestions(
        issues, "import os, sys, json\nimport os\nimport math"
    )

    assert len(suggestions) > 0
    assert suggestions[0].original_code == "import os, sys, json\nimport os\nimport math"
    assert suggestions[0].fixed_code == "import json"
    assert suggestions[0].confidence == 1.0


@patch("src.agents.clean_code_agent.OpenAI")
def test_clean_code_apply_suggestions(mock_openai, monkeypatch, tmp_path):
    _set_llm_env(monkeypatch)
    mock_openai.return_value.chat.completions.create.return_value = make_mock_response(
        "import json"
    )

    agent = CleanCodeAgent()
    test_file = tmp_path / "test_code.py"
    test_file.write_text("import os, sys, json\nimport os\nimport math\n")

    issue = Issue(
        line=1,
        message="Unused imports: 'os', 'sys', 'math' are imported but not used.",
        severity="warning",
        rule_id="unused-import",
        column=1,
    )
    suggestion = Suggestion(
        issue=issue,
        original_code="import os, sys, json\nimport os\nimport math",
        fixed_code="import json",
        rationale="Removes unnecessary imports to reduce clutter and potential confusion. Only keep modules used in the code.",
        confidence=1.0,
    )

    agent.apply([suggestion], str(test_file))
    result = test_file.read_text()
    assert "import json" in result


def test_read_file(tmp_path, monkeypatch):
    _set_llm_env(monkeypatch)
    test_file = tmp_path / "sample.py"
    test_file.write_text("print('hello')\n")

    agent = CleanCodeAgent()
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