"""
Tests for IdiomsAgent
Run with: python -m pytest tests/agents/test_idioms_agent.py
"""

import pytest
from src.agents.idioms_agent import IdiomsAgent


def test_idioms_scan():
    """Test that IdiomsAgent can scan a file and find issues"""
    agent = IdiomsAgent()
    issues = agent.scan("../sample_bad_idioms.py")

    assert len(issues) > 0

    assert issues[0].line > 0
    assert issues[0].message != ""
    assert issues[0].severity in ["info", "warning", "error"]
    assert issues[0].rule_id != ""
