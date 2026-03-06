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

