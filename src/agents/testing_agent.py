"""Agent for identifying missing or insufficient tests in Python source files."""

import json
import logging
import os

from openai import OpenAI

from src.agents.abstract_agent import BaseAgent
from src.util.llm_generator import LLMGenerator
from src.util.llm_scanner import LLMScanner
from src.util.prompt_registry import PromptRegistry
from src.util.testing_applier import Applier
from src.util.testing_validator import Validator
from src.util.issue import Issue
from src.util.suggestion import Suggestion

logger = logging.getLogger(__name__)

LLM_TOKEN = os.getenv("LITELLM_TOKEN")
LLM_API_URL = os.getenv("LLM_API_URL", "https://litellm.oit.duke.edu/v1")


class TestingAgent(BaseAgent):
    """Agent that identifies missing or weak tests and suggests improvements."""

    # Prevents pytest from trying to collect this class as a test suite
    __test__ = False

    def __init__(self) -> None:
        super().__init__("Testing")

    def _get_client(self) -> OpenAI:
        token = os.getenv("LITELLM_TOKEN")
        if not token:
            raise RuntimeError(
                "Missing LITELLM_TOKEN. Put it in .env at project root or export it."
            )

        base_url = os.getenv("LLM_API_URL", "https://litellm.oit.duke.edu/v1")
        return OpenAI(api_key=token, base_url=base_url)

    def _get_model(self) -> str:
        return os.getenv("MODEL_ID", "GPT 4.1")

    def scan(self, file_path: str) -> list[Issue]:
        """Scan source and test files for missing or insufficient tests."""
        content = self._read_file(file_path)
        test_file_path = self._get_test_file_path(file_path)
        test_content = self._read_file(test_file_path)
        client = self._get_client()
        model = self._get_model()

        if not test_content:
            logger.info("No existing test file found at %s", test_file_path)

        llm_scanner = LLMScanner(
            client=client, model=model, prompt_registry=PromptRegistry()
        )

        context = {
            "content": content,
            "test_content": test_content,
        }

        return llm_scanner.scan(prompt_name="testing.scan", context=context)

    def get_suggestions(self, issues: list[Issue], code: str) -> list[Suggestion]:
        """Provide suggestions based on the scanned file and identified issues"""
        client = self._get_client()
        model = self._get_model()

        llm_generator = LLMGenerator(
            client=client, model=model, prompt_registry=PromptRegistry()
        )

        context = {
            "code": code,
            "issues_json": json.dumps(
                [issue.model_dump() for issue in issues], indent=2
            ),
        }

        return llm_generator.generate_suggestions(
            prompt_name="testing.generate_suggestions", context=context, issues=issues
        )

    def validate(self, suggestion) -> bool:
        validator = Validator(suggestion)
        return validator.validate()

    def apply(self, suggestions: list[Suggestion], file_path: str) -> None:
        applier = Applier()
        test_file_path = self._get_test_file_path(file_path)
        applier.apply(suggestions, test_file_path=test_file_path)

    def _read_file(self, file_path: str) -> str:
        """Read and return file contents."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                logger.info("File successfully read: %s", file_path)
                return content
        except OSError as e:
            logger.warning("Could not read file %s: %s", file_path, e)
            return ""

    def _get_test_file_path(self, source_path: str) -> str:
        """Derive the test file path from a source file path.

        Example: src/agents/idioms_agent.py -> tests/agents/test_idioms_agent.py
        """
        if "src/" in source_path:
            source_path = source_path[source_path.index("src/") :]
        elif "data/" in source_path:
            source_path = source_path[source_path.index("data/") :]

        directory = source_path.rsplit("/", 1)[0]
        filename = source_path.rsplit("/", 1)[1]
        return f"tests/{directory}/test_{filename}"
