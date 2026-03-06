"""Tests for LLMApplier"""
from unittest.mock import MagicMock, mock_open, patch

from src.util.llm_applier import LLMApplier


def _make_applier():
    return LLMApplier(
        client=MagicMock(),
        model="GPT 4.1",
        prompt_registry=MagicMock(),
    )


def _make_llm_response(content):
    resp = MagicMock()
    resp.choices[0].message.content = content
    return resp


def test_render_prompt_replaces_all_placeholders():
    applier = _make_applier()
    rendered = applier._render_prompt("{{ code }} | {{ suggestions_json }}", {
        "code": "x=1",
        "suggestions_json": "[]",
    })
    assert rendered == "x=1 | []"


def test_parse_applied_suggestion_writes_clean_code(tmp_path):
    applier = _make_applier()
    out_file = tmp_path / "out.py"
    applier._parse_applied_suggestion("x = 1\n", str(out_file))
    assert out_file.read_text() == "x = 1"


def test_parse_applied_suggestion_strips_markdown_fences(tmp_path):
    applier = _make_applier()
    out_file = tmp_path / "out.py"
    applier._parse_applied_suggestion("```python\nx = 1\n```", str(out_file))
    assert out_file.read_text() == "x = 1"


def test_apply_calls_registry_and_client_and_writes_file(tmp_path):
    applier = _make_applier()
    applier.prompt_registry.load.return_value = "Code: {{ code }}"
    applier.client.chat.completions.create.return_value = _make_llm_response("x = 1")
    out_file = tmp_path / "result.py"

    applier.apply("cleancode.apply", {"code": "x=1", "suggestions_json": "[]"}, str(out_file))

    applier.prompt_registry.load.assert_called_once_with("cleancode.apply")
    applier.client.chat.completions.create.assert_called_once()
    assert out_file.read_text() == "x = 1"


def test_apply_returns_empty_when_llm_returns_none(tmp_path):
    applier = _make_applier()
    applier.prompt_registry.load.return_value = "prompt"
    applier.client.chat.completions.create.return_value = _make_llm_response(None)
    out_file = tmp_path / "result.py"

    result = applier.apply("cleancode.apply", {"code": "x", "suggestions_json": "[]"}, str(out_file))

    assert result == []
