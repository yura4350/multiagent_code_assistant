import logging

from src.agents.abstract_agent import BaseAgent
from src.util.code_style_applier import Applier
from src.util.code_style_generator import Generator
from src.util.code_style_scanner import Scanner
from src.util.validator import Validator
from src.util.issue import Issue
from src.util.suggestion import Suggestion

logger = logging.getLogger(__name__)


class StyleAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("CodeStyle")

    """
    Scan the code for the linting issues
    """

    def scan(self, file_path: str) -> list[Issue]:
        return Scanner().scan(file_path)

    """
    Generate suggestions for the linting issues.
    FOR RUFF LINTER - LOGGING
    """

    def get_suggestions(self, issues: list[Issue], code: str) -> list[Suggestion]:
        return Generator().get_suggestions(issues, code)

    """
    Validate the suggestions
    """

    def validate(self, issues: list[Issue]) -> bool:
        """Valid when there are no remaining lint issues. Uses shared validator."""
        validator = Validator(issues)
        return validator.validate()

    """
    Apply the suggestions to the code
    """

    def apply(self, suggestions: list[Suggestion] | None, file_path: str) -> None:
        Applier().apply(suggestions, file_path)
