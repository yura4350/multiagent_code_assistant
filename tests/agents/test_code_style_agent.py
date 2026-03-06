"""
Tests for StyleAgent
Run with: python -m pytest tests/agents/test_code_style_agent.py
"""

from unittest.mock import MagicMock, patch

import pytest

from src.agents.code_style_agent import StyleAgent
from src.model.code_style_scanner import Scanner
from src.models.issue import Issue


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_issue(rule_id: str = "E501", line: int = 1, message: str = "msg") -> Issue:
    return Issue(line=line, message=message, severity="error", rule_id=rule_id)


def _make_ruff_entry(
    code: str = "E501",
    message: str = "line too long",
    row: int = 5,
    column: int = 80,
) -> dict:
    return {"code": code, "message": message, "location": {"row": row, "column": column}}


# ---------------------------------------------------------------------------
# scan (integration – requires ruff + real file)
# ---------------------------------------------------------------------------

def test_style_agent_scan():
    """Test that StyleAgent can scan a file and find issues"""
    agent = StyleAgent()
    issues = agent.scan("../data/bad_style.py")

    assert len(issues) > 0
    assert issues[0].line > 0
    assert issues[0].message != ""
    assert issues[0].severity in ["info", "warning", "error"]
    assert issues[0].rule_id != ""


def test_style_agent_scan_clean_file(tmp_path):
    """Scanning a clean file returns an empty list."""
    clean = tmp_path / "clean.py"
    clean.write_text('x = 1\n')

    agent = StyleAgent()
    issues = agent.scan(str(clean))

    assert issues == []


# ---------------------------------------------------------------------------
# _severity_from_rule
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rule_id,expected", [
    ("E501", "error"),
    ("E302", "error"),
    ("F401", "error"),
    ("F811", "error"),
    ("W291", "warning"),
    ("W503", "warning"),
    ("I001", "info"),
    ("C901", "info"),
    ("B006", "info"),
])
def test_severity_from_rule(rule_id, expected):
    scanner = Scanner()
    assert scanner._severity_from_rule(rule_id) == expected


# ---------------------------------------------------------------------------
# _parse_ruff_output
# ---------------------------------------------------------------------------

def test_parse_ruff_output_empty():
    scanner = Scanner()
    assert scanner._parse_ruff_output([]) == []


def test_parse_ruff_output_single():
    scanner = Scanner()
    raw = [_make_ruff_entry(code="E501", message="line too long", row=10, column=80)]
    issues = scanner._parse_ruff_output(raw)

    assert len(issues) == 1
    assert issues[0].line == 10
    assert issues[0].column == 80
    assert issues[0].message == "line too long"
    assert issues[0].rule_id == "E501"
    assert issues[0].severity == "error"


def test_parse_ruff_output_multiple():
    scanner = Scanner()
    raw = [
        _make_ruff_entry(code="W291", row=3),
        _make_ruff_entry(code="F401", row=7),
    ]
    issues = scanner._parse_ruff_output(raw)

    assert len(issues) == 2
    assert issues[0].severity == "warning"
    assert issues[1].severity == "error"


def test_parse_ruff_output_missing_fields():
    """Entries with missing optional fields should use sensible defaults."""
    scanner = Scanner()
    raw = [{"message": "something wrong"}]  # no code, no location
    issues = scanner._parse_ruff_output(raw)

    assert len(issues) == 1
    assert issues[0].rule_id == "RUFF"
    assert issues[0].line == 1
    assert issues[0].column == 1


# ---------------------------------------------------------------------------
# get_suggestions
# ---------------------------------------------------------------------------

def test_get_suggestions_empty():
    agent = StyleAgent()
    assert agent.get_suggestions([], "") == []


def test_get_suggestions_creates_one_suggestion_per_issue():
    agent = StyleAgent()
    issues = [_make_issue("E501"), _make_issue("W291")]
    suggestions = agent.get_suggestions(issues, "some code")

    assert len(suggestions) == 2


def test_get_suggestions_rationale_contains_rule_and_message():
    agent = StyleAgent()
    issue = _make_issue(rule_id="E501", message="line too long")
    suggestions = agent.get_suggestions([issue], "code")

    assert "E501" in suggestions[0].rationale
    assert "line too long" in suggestions[0].rationale


def test_get_suggestions_confidence_is_one():
    agent = StyleAgent()
    suggestions = agent.get_suggestions([_make_issue()], "code")
    assert suggestions[0].confidence == 1.0


def test_get_suggestions_issue_is_preserved():
    agent = StyleAgent()
    issue = _make_issue(rule_id="F401", line=42)
    suggestions = agent.get_suggestions([issue], "code")
    assert suggestions[0].issue == issue


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

def test_validate_no_issues_returns_true():
    agent = StyleAgent()
    assert agent.validate([]) is True


def test_validate_with_issues_returns_false():
    agent = StyleAgent()
    assert agent.validate([_make_issue()]) is False


def test_validate_with_multiple_issues_returns_false():
    agent = StyleAgent()
    assert agent.validate([_make_issue(), _make_issue("W291")]) is False


# ---------------------------------------------------------------------------
# apply (mocked subprocess)
# ---------------------------------------------------------------------------

@patch("src.model.code_style_applier.subprocess.run")
def test_apply_calls_ruff_fix_and_format(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stderr="")
    agent = StyleAgent()
    agent.apply(None, "some_file.py")

    assert mock_run.call_count == 2
    first_cmd = mock_run.call_args_list[0][0][0]
    second_cmd = mock_run.call_args_list[1][0][0]
    assert "check" in first_cmd and "--fix" in first_cmd
    assert "format" in second_cmd


# ---------------------------------------------------------------------------
# _run_ruff_check (mocked subprocess)
# ---------------------------------------------------------------------------

@patch("src.model.code_style_scanner.subprocess.run")
def test_run_ruff_check_returns_parsed_json(mock_run):
    import json
    payload = [_make_ruff_entry()]
    mock_run.return_value = MagicMock(returncode=1, stdout=json.dumps(payload), stderr="")
    scanner = Scanner()
    assert scanner._run_ruff_check("file.py") == payload


@patch("src.model.code_style_scanner.subprocess.run")
def test_run_ruff_check_empty_stdout_returns_empty(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    assert Scanner()._run_ruff_check("file.py") == []


@patch("src.model.code_style_scanner.subprocess.run")
def test_run_ruff_check_bad_json_returns_empty(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stdout="not json", stderr="")
    assert Scanner()._run_ruff_check("file.py") == []


@patch("src.model.code_style_scanner.subprocess.run")
def test_run_ruff_check_error_returncode_returns_empty(mock_run):
    mock_run.return_value = MagicMock(returncode=2, stdout="", stderr="fatal error")
    assert Scanner()._run_ruff_check("file.py") == []


def test_run_ruff_check_ruff_not_found_raises():
    with patch("src.model.code_style_scanner.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(RuntimeError, match="Ruff not found"):
            Scanner()._run_ruff_check("file.py")
