"""Agent for identifying missing or insufficient tests in Python source files."""
import json
import logging
import os

from openai import OpenAI

from src.agents.abstract_agent import BaseAgent
from src.models.issue import Issue
from src.models.suggestion import Suggestion

logger = logging.getLogger(__name__)

LLM_TOKEN = os.getenv("LITELLM_TOKEN")
LLM_API_URL = os.getenv("LLM_API_URL", "https://litellm.oit.duke.edu/v1")


class TestsAgent(BaseAgent):
    """Agent that identifies missing or weak tests and suggests improvements."""

    def __init__(self) -> None:
        super().__init__("TESTS")

    def scan(self, file_path: str) -> list[Issue]:
        """Scan source and test files for missing or insufficient tests."""
        content = self._read_file(file_path)
        test_file_path = self._get_test_file_path(file_path)
        test_content = self._read_file(test_file_path)
        if not test_content:
            logger.info("No existing test file found at %s", test_file_path)

        client = OpenAI(
            api_key=LLM_TOKEN,
            base_url=LLM_API_URL,
        )
        test_scanner_prompt = f"""
        Role: You are a distinguished Python engineer specializing in test quality.
        Task: Analyze the given Python source file and its corresponding test file.
            Identify functions or methods that are missing tests or have insufficient tests.
            Do NOT generate test code — only identify the gaps.

        Focus on:
        - Functions in the source file with no corresponding test
        - Tests with no assertions
        - Tests that only cover the happy path but not edge cases or errors
        - Functions with complex logic that need more thorough testing

        Return ONLY a valid JSON array with no extra text, no markdown, no backticks.
        Each element must have:
            - line (int): line number in the SOURCE file where the function is defined
            - message (str): description of what test is missing or insufficient
            - severity (str): "error", "warning", or "info"
            - rule_id (str): short identifier like "missing-test" or "weak-test"
            - column (int): use 0

        Source file:
        {content}

        Existing test file (empty if none exists):
        {test_content}
        """
        response = client.chat.completions.create(
            model="GPT 4.1",
            messages=[{"role": "user", "content": test_scanner_prompt}],
        )

        raw = response.choices[0].message.content
        if raw:
            logger.info("raw: %s", raw)
            return self._parse_issues(raw)

        return []

    def generate_suggestions(
        self, issues: list[Issue], code: str
    ) -> list[Suggestion]:
        """Generate suggested test code for identified gaps."""
        # create prompt with source code and issues
        # call LLM
        # parse and return suggestions

        return []



    def validate(self, suggestion: Suggestion) -> bool:
        """Validate that suggestion contains at least one test function."""
        pass

    def apply(self, suggestions: list[Suggestion], file_path: str) -> None:
        """Write suggested tests to the corresponding test file."""
        pass

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
        
    def _parse_issues(self, response: str) -> list[Issue]:
        """Parse LLM JSON response into a list of Issue objects."""
        try:
            clean = response.strip().removeprefix("```json").removesuffix("```").strip()
            data = json.loads(clean)
            issues = [Issue(**item) for item in data]
            logger.info("Parsed %d issues from LLM response", len(issues))
            return issues
        except (json.JSONDecodeError, TypeError) as e:
            logger.error("Failed to parse issues from LLM response: %s", e)
            return []
        
    def _parse_suggestions(
        self, response: str, issues: list[Issue]
    ) -> list[Suggestion]:
        """Parse LLM JSON response into a list of Suggestion objects."""
        try:
            clean = response.strip().removeprefix("```json").removesuffix("```").strip()
            data = json.loads(clean)
            issue_map = {issue.rule_id: issue for issue in issues}
            suggestions = []
            for item in data:
                rule_id = item.get("issue", {}).get("rule_id")
                issue = issue_map.get(rule_id)
                if not issue:
                    logger.warning(
                        "No matching issue for rule_id %s, skipping.", rule_id
                    )
                    continue
                suggestions.append(
                    Suggestion(
                        issue=issue,
                        original_code=item.get("original_code")
                        or item.get("original code"),
                        fixed_code=item.get("fixed_code") or item.get("fixed code"),
                        rationale=item.get("rationale", ""),
                        confidence=item.get("confidence"),
                    )
                )
            logger.info("Parsed %d suggestions from LLM response", len(suggestions))
            return suggestions
        except (json.JSONDecodeError, TypeError) as e:
            logger.error("Failed to parse suggestions from LLM response: %s", e)
            return []

    def _get_test_file_path(self, source_path: str) -> str:
        """Derive the test file path from a source file path.

        Example: src/agents/idioms_agent.py -> tests/agents/test_idioms_agent.py
        """
        directory = source_path.rsplit("/", 1)[0].split("/", 1)[1]
        filename = source_path.rsplit("/", 1)[1]
        return f"tests/{directory}/test_{filename}"