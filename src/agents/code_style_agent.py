import subprocess
import json
import logging

from agents.abstract_agent import BaseAgent
from models.issue import Issue
from models.suggestion import Suggestion

import re

logger = logging.getLogger(__name__)

class StyleAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("CodeStyle")

    """
    Scan the code for the linting issues
    """
    def scan(self, file_path: str) -> list[Issue]:
        lint_results = self._run_ruff_check(file_path)
        return self._parse_ruff_output(lint_results)
    
    """
    Generate suggestions for the linting issues.
    FOR RUFF LINTER - LOGGING
    """
    def generate_suggestions(self, issues: list[Issue], code: str) -> list[Suggestion]:
        suggestions: list[Suggestion] = []

        for issue in issues:
            suggestions.append(
                Suggestion(
                    issue=issue,
                    rationale=f"Fix {issue.rule_id}: {issue.message}",
                    confidence=1.0,
                )
            )

        return suggestions
    
    """
    Validate the suggestions
    """
    def validate(self, issues: list[Issue]) -> bool:
        """Valid when there are no remaining lint issues."""
        return len(issues) == 0
    
    """
    Apply the suggestions to the code
    """
    def apply(self, file_path: str) -> None:
        self._run_ruff_fix(file_path)
        self._run_ruff_format(file_path)
    
    def _run_ruff_check(self, file_path: str) -> list[dict]:
        try:
            result = subprocess.run(
                ["ruff", "check", file_path, "--output-format", "json"],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "Ruff not found. Install it with: pip install ruff"
            ) from exc

        # 0 - no issues, 1 - issues found, >1 - command/problem error
        if result.returncode not in (0, 1):
            logger.warning("Ruff check failed: %s", result.stderr.strip())
            return []

        stdout = result.stdout.strip()
        if not stdout:
            return []

        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            logger.warning("Could not parse Ruff JSON output.")
            return []
    
    def _parse_ruff_output(self, linting_issues: list[dict]) -> list[Issue]:
        if not linting_issues:
            return []

        issues: list[Issue] = []

        for linting_issue in linting_issues:
            code = linting_issue.get("code", "RUFF")
            message = linting_issue.get("message", "")
            location = linting_issue.get("location", {})
            line = int(location.get("row", 1))
            column = int(location.get("column", 1))

            issues.append(
                Issue(
                    line=line,
                    message=message,
                    severity=self._severity_from_rule(code),
                    rule_id=code,
                    column=column,
                )
            )

        return issues
    
    def _run_ruff_fix(self, file_path: str) -> None:
        result = subprocess.run(
            ["ruff", "check", file_path, "--fix"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode not in (0, 1):
            logger.warning("Ruff fix failed: %s", result.stderr.strip())

    def _run_ruff_format(self, file_path: str) -> None:
        result = subprocess.run(
            ["ruff", "format", file_path],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode not in (0, 1):
            logger.warning("Ruff format failed: %s", result.stderr.strip())

    def _severity_from_rule(self, rule_id: str) -> str:
        # Lightweight heuristic for MVP reporting.
        if rule_id.startswith(("E", "F")):
            return "error"
        if rule_id.startswith("W"):
            return "warning"
        return "info"

    """
    Pylint functions not used
    """
    def _run_pylint(self, file_path: str) -> list[dict]:
        try:
            result = subprocess.run(
                ["pylint", file_path, "--output-format=json"],
                capture_output=True,
                text=True,
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Pylint failed with Exit Code: {e.returncode}")
            return []
        except FileNotFoundError:
            print("Error: Pylint not found")
            return []

    def _parse_pylint_output(self, linting_issues: list[dict]) -> list[Issue]:
        if not linting_issues:
            return []

        issues = []

        severity_map = {
            "convention": "info",
            "refactor": "info",
            "warning": "warning",
            "error": "error",
            "fatal": "error",
        }

        for linting_issue in linting_issues:
            issue = Issue(
                line=linting_issue["line"],
                message=linting_issue["message"],
                severity=severity_map[linting_issue["type"]],
                rule_id=linting_issue["message-id"],
                column=linting_issue["column"],
            )
            issues.append(issue)

        return issues
