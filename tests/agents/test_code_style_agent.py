"""
Tests for StyleAgent
Run with: python -m pytest tests/agents/test_code_style_agent.py
"""

from src.agents.code_style_agent import StyleAgent


def test_style_agent_scan():
    """Test that StyleAgent can scan a file and find issues"""
    agent = StyleAgent()
    issues = agent.scan("../data/bad_style.py")

    assert len(issues) > 0

    assert issues[0].line > 0
    assert issues[0].message != ""
    assert issues[0].severity in ["info", "warning", "error"]
    assert issues[0].rule_id != ""
