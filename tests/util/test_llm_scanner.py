"""Tests for LLMScanner"""
from unittest.mock import MagicMock

from src.util.llm_scanner import LLMScanner
from src.util.issue import Issue


def _make_scanner():
    return LLMScanner(
        client=MagicMock(),
        model="GPT 4.1",
        prompt_registry=MagicMock(),
    )


def _make_llm_response(content):
    resp = MagicMock()
    resp.choices[0].message.content = content
    return resp


def test_render_prompt_replaces_placeholders():
    scanner = _make_scanner()
    rendered = scanner._render_prompt("Hello {{ name }}!", {"name": "world"})
    assert rendered == "Hello world!"


def test_render_prompt_leaves_unknown_keys_intact():
    scanner = _make_scanner()
    rendered = scanner._render_prompt("{{ a }} {{ b }}", {"a": "X"})
    assert "X" in rendered
    assert "{{ b }}" in rendered


def test_parse_issues_valid_json():
    scanner = _make_scanner()
    raw = '[{"line": 5, "message": "bad", "severity": "warning", "rule_id": "R1", "column": 0}]'
    issues = scanner._parse_issues(raw)
    assert len(issues) == 1
    assert issues[0].line == 5
    assert issues[0].rule_id == "R1"


def test_parse_issues_strips_markdown_fences():
    scanner = _make_scanner()
    raw = '```json\n[{"line": 1, "message": "x", "severity": "error", "rule_id": "E1", "column": 0}]\n```'
    issues = scanner._parse_issues(raw)
    assert len(issues) == 1


def test_parse_issues_invalid_json_returns_empty():
    scanner = _make_scanner()
    assert scanner._parse_issues("not json") == []


def test_parse_issues_empty_array_returns_empty():
    scanner = _make_scanner()
    assert scanner._parse_issues("[]") == []


def test_scan_calls_registry_and_client():
    scanner = _make_scanner()
    scanner.prompt_registry.load.return_value = "Scan: {{ content }}"
    raw_json = '[{"line": 3, "message": "m", "severity": "info", "rule_id": "I1", "column": 0}]'
    scanner.client.chat.completions.create.return_value = _make_llm_response(raw_json)

    issues = scanner.scan("idioms.scan", {"content": "some code"})

    scanner.prompt_registry.load.assert_called_once_with("idioms.scan")
    scanner.client.chat.completions.create.assert_called_once()
    assert len(issues) == 1
    assert issues[0].rule_id == "I1"


def test_scan_returns_empty_when_llm_returns_none():
    scanner = _make_scanner()
    scanner.prompt_registry.load.return_value = "prompt"
    scanner.client.chat.completions.create.return_value = _make_llm_response(None)

    assert scanner.scan("idioms.scan", {"content": "code"}) == []
