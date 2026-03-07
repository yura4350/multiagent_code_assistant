"""Tests for input.parse_input"""
import pytest

from src.util.input import parse_input, ParsedInput


def test_parse_input_file_not_found_raises():
    with pytest.raises((FileNotFoundError, SystemExit)):
        parse_input(["nonexistent_file_xyz.py"])


def test_parse_input_reads_file_content(tmp_path):
    f = tmp_path / "sample.py"
    f.write_text("x = 1\n")

    result = parse_input([str(f)])

    assert result.file_content == "x = 1\n"
    assert result.file_path == str(f)
    assert result.apply is False
    assert result.agent is None


def test_parse_input_with_agent_flag(tmp_path):
    f = tmp_path / "sample.py"
    f.write_text("x = 1\n")

    result = parse_input([str(f), "--agent", "IDIOMS"])

    assert result.agent == "IDIOMS"


def test_parse_input_with_apply_flag(tmp_path):
    f = tmp_path / "sample.py"
    f.write_text("x = 1\n")

    result = parse_input([str(f), "--apply"])

    assert result.apply is True
