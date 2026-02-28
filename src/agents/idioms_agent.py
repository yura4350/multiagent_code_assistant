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
        Each element must have:
            - line (int), message (str), severity (str), rule_id (str), column (int).

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
        """Provide suggestions based on the scanned file and identified issues"""
        # create the prompt
        # Initiate generator

        # TODO: Replace with LLM Generator when ready
        client = OpenAI(
            api_key=LLM_TOKEN,
            base_url=LLM_API_URL,
        )

        issues_json = json.dumps([issue.model_dump() for issue in issues], indent=2)

        idiom_scanner_prompt = f"""
        Role: You are a distinguished Python engineer at Big Tech.
        Task: Based on the list of issues identifed in terms of the given Python
                code ONLY for Pythonic idiom violations.
        Generate suggestions for improvement

        Return a suggestion.
        Return ONLY a valid JSON array with no extra text, no markdown, no backticks.

        Each element must have:
        - "issue": {{object with line, message, severity, rule_id, column}}
        - "original_code": string
        - "fixed_code": string
        - "rationale": string
        - "confidence": float 0.0-1.0


        Code to fix:
        {code}
        Issues to go through:
        {issues_json}

        """

        response = client.chat.completions.create(
            model="GPT 4.1",
            messages=[{"role": "user", "content": idiom_scanner_prompt}],
        )

        raw = response.choices[0].message.content
        if raw:
            logger.info("raw: %s", raw)
            return self._parse_suggestions(raw, issues)

        return []

    def validate(self, suggestion: Suggestion) -> bool:
        return super().validate(suggestion)

    def apply(self, suggestions: list[Suggestion], file_path: str) -> None:
        """
        Suggestion contains an issue with original code and fixed code.
        This functions aggregates these suggestions and provides updated code.
        """

        # TODO: Replace with LLM Generator when ready
        client = OpenAI(
            api_key=LLM_TOKEN,
            base_url=LLM_API_URL,
        )

        suggestions_json = json.dumps([s.model_dump() for s in suggestions], indent=2)
        code = self._read_file(file_path)

        idiom_apply_suggestion_prompt = f"""
        Role: You are a senior software engineer at Big Tech.
        Task: Apply the following suggestions to the given Python code.
            Replace each original_code snippet with the corresponding fixed_code.
        Code to fix:
        {code}

        Suggestions:
        {suggestions_json}

        Return ONLY the complete fixed Python script
        with no extra text, no markdown, no backticks.
        """
        response = client.chat.completions.create(
            model="GPT 4.1",
            messages=[{"role": "user", "content": idiom_apply_suggestion_prompt}],
        )

        raw = response.choices[0].message.content

        if raw:
            logger.info("raw: %s", raw)
            self._parse_applied_suggestion(raw, file_path)

        return

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

    def _parse_applied_suggestion(self, response: str, file_path: str) -> None:
        """Write the LLM-returned fixed code back to the file."""
        clean = response.strip().removeprefix("```python").removesuffix("```").strip()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(clean)
        logger.info("Applied suggestions to %s", file_path)
