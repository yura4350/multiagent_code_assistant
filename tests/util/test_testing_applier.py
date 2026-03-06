"""Tests for testing_applier.Applier"""
from unittest.mock import mock_open, patch

from src.util.testing_applier import Applier
from src.util.issue import Issue
from src.util.suggestion import Suggestion


def _make_suggestion(fixed_code):
    issue = Issue(line=1, message="msg", severity="warning", rule_id="R1", column=0)
    return Suggestion(issue=issue, fixed_code=fixed_code, rationale="reason")


def test_apply_writes_valid_suggestions(tmp_path):
    applier = Applier()
    test_file = tmp_path / "tests" / "test_dummy.py"
    test_file.parent.mkdir()
    test_file.write_text("")

    s = _make_suggestion("def test_foo():\n    assert True")
    applier.apply([s], str(test_file))

    content = test_file.read_text()
    assert "def test_foo()" in content


def test_apply_skips_invalid_suggestions(tmp_path):
    applier = Applier()
    test_file = tmp_path / "tests" / "test_dummy.py"
    test_file.parent.mkdir()
    test_file.write_text("")

    invalid = _make_suggestion("print('no test here')")
    applier.apply([invalid], str(test_file))

    assert test_file.read_text() == ""


def test_apply_writes_only_valid_among_mixed(tmp_path):
    applier = Applier()
    test_file = tmp_path / "tests" / "test_dummy.py"
    test_file.parent.mkdir()
    test_file.write_text("")

    valid = _make_suggestion("def test_bar():\n    assert 1 == 1")
    invalid = _make_suggestion("not_a_test()")
    applier.apply([valid, invalid], str(test_file))

    content = test_file.read_text()
    assert "def test_bar()" in content
    assert "not_a_test" not in content


def test_get_test_file_path_from_src():
    applier = Applier()
    result = applier._get_test_file_path("src/agents/idioms_agent.py")
    assert result == "tests/src/agents/test_idioms_agent.py"


def test_get_test_file_path_from_data():
    applier = Applier()
    result = applier._get_test_file_path("data/processor.py")
    assert result == "tests/data/test_processor.py"
