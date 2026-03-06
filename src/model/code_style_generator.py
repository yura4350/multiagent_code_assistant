import logging

from src.models.issue import Issue
from src.models.suggestion import Suggestion

logger = logging.getLogger(__name__)


class Generator:
    def __init__(self):
        pass

    def get_suggestions(self, issues: list[Issue], _code: str) -> list[Suggestion]:
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
