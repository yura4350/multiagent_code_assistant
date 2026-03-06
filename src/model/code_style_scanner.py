import logging
import json
import subprocess
from src.models.issue import Issue

logger = logging.getLogger(__name__)

class Scanner:
    def __init__(self):
        pass

    def scan(self, file_path: str) -> list[Issue]:
        lint_results = self._run_ruff_check(file_path)
        return self._parse_ruff_output(lint_results)

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


    def _severity_from_rule(self, rule_id: str) -> str:
        # Lightweight heuristic for MVP reporting.
        if rule_id.startswith(("E", "F")):
            return "error"
        if rule_id.startswith("W"):
            return "warning"
        return "info"
