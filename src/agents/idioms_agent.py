import json
import logging
import os
from src.agents.abstract_agent import BaseAgent
from src.models.issue import Issue
from src.models.suggestion import Suggestion
from openai import OpenAI

logger = logging.getLogger(__name__)

LLM_TOKEN = os.getenv("LITELLM_TOKEN")
LLM_API_URL = os.getenv("LLM_API_URL", "https://litellm.oit.duke.edu/v1")

class IdiomsAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Idiom")

    def scan(self, file_path: str) -> list[Issue]:
        """Scan the code for adherence to programming language idioms"""
        content = self._read_file(file_path)

        # TODO: Replace with LLM Generator when ready
        client = OpenAI(
            api_key=LLM_TOKEN,
            base_url=LLM_API_URL,
        )
        idiom_scanner_prompt = f"""
        Role: You are a distinguished Python engineer
        Task: Analyze the given Python code ONLY for Pythonic idiom violations. 
            Do NOT report spacing, formatting, or linting issues.

        Focus ONLY on these kinds of issues:
        - Using range(len(x)) instead of enumerate(x)
        - Using a loop to build a list instead of a list comprehension
        - Not using context managers (with) for file/resource handling
        - Comparing to True/False/None with == instead of 'is' or truthiness
        - Using mutable default arguments (def f(x=[]))
        - Not using zip() to iterate over multiple lists
        - Using map/filter when a comprehension is cleaner
        - Not using any(), all(), sum() where appropriate
        - Using bare except instead of specific exception types

        Return ONLY a valid JSON array with no extra text, no markdown, no backticks.
        Each element must have: line (int), message (str), severity (str), rule_id (str), column (int).

        Code to analyze:
        {content}
        """

        response = client.chat.completions.create(
            model="GPT 4.1",
            messages=[{"role": "user", "content": idiom_scanner_prompt}],
        )

        raw = response.choices[0].message.content
        if raw:
            logger.info("raw: %s", raw)
            return self._parse_issues(raw)

        return []

    def generate_suggestions(self, issues: list[Issue], code: str) -> list[Suggestion]:
        return []

    def validate(self, suggestion: Suggestion) -> bool:
        return super().validate(suggestion)

    def apply(self, suggestion: Suggestion, file_path: str) -> None:
        return super().apply(suggestion, file_path)

    def _read_file(self, file_path: str) -> str:
        with open(file_path, "r") as file:
            content = file.read()
            logger.info("File Successfully Read")
        return content

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
