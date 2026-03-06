"""
Tests for CleanCodeAgent
Run with: python -m pytest tests/agents/test_clean_code_agent.py
"""
from unittest.mock import MagicMock, patch

from src.agents.idioms_agent import CleanCodeAgent
from src.model.llm_generator import LLMGenerator
from src.model.llm_scanner import LLMScanner
from src.model.prompt_registry import PromptRegistry
from src.models.issue import Issue
from src.models.suggestion import Suggestion

