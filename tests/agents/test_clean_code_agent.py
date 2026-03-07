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
    "original_code": "import os, sys, json\nimport os\nimport math",
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
def test_idioms_scan(mock_openai, monkeypatch):
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