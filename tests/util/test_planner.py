"""Tests for planner.plan"""
import pytest

from src.util.planner import plan
from src.util.input import ParsedInput


def _make_input(agent=None, file_path="f.py", file_content="x=1", apply=False):
    return ParsedInput(agent=agent, file_path=file_path, file_content=file_content, apply=apply)


def test_plan_uses_specified_agent():
    agent_name, _ = plan(_make_input(agent="IDIOMS"))
    assert agent_name == "IDIOMS"


def test_plan_defaults_to_code_style_when_no_agent():
    agent_name, _ = plan(_make_input(agent=None))
    assert agent_name == "CODE_STYLE"


def test_plan_returns_parsed_input_unchanged():
    parsed = _make_input(agent="IDIOMS", file_content="print('hi')")
    _, returned = plan(parsed)
    assert returned is parsed


def test_plan_raises_for_unknown_agent():
    with pytest.raises(ValueError, match="Unknown agent"):
        plan(_make_input(agent="UNKNOWN_AGENT"))
