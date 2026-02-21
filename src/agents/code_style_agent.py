import subprocess
import json
from agents.abstract_agent import BaseAgent
from models.issue import Issue
from models.suggestion import Suggestion


class StyleAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("CodeStyle")

    def scan(self, file_path: str) -> list[Issue]:
        lint_results = self._run_pylint(file_path)
        issues = self._parse_pylint_output(lint_results)
        return issues

    def generate_suggestions(self, issues: list[Issue], code: str) -> list[Suggestion]:
        suggestions: list[Suggestion] = []

        for issue in issues:
            suggestions.append(
            Suggestion(
                issue=issue,
                original_code="",  # optional for now
                fixed_code="",     # optional for now (no auto-fix yet)
                rationale=f"{issue.rule_id}: {issue.message}",
                confidence=1.0, # default value
            )
        )

        return suggestions
    
    def validate(self, suggestion: Suggestion) -> bool:
        return True # For now, we assume the linter suggestions are always valid

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
