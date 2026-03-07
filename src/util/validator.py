import logging

from src.util.issue import Issue

logger = logging.getLogger(__name__)


class Validator:
    """Initialize the Validator"""

    def __init__(self, issues: list[Issue]):
        self.issues = issues

    def validate(self) -> bool:
        return len(self.issues) == 0
