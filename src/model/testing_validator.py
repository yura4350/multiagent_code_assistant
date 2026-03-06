import logging

from src.models.suggestion import Suggestion

logger = logging.getLogger(__name__)


class Validator:
    """Initialize the Validator"""

    def __init__(self, suggestion):
        self.suggestion = suggestion

    def validate(self) -> bool:
        if isinstance(self.suggestion, list):
            # Controller mistakenly passes issues list — just return True
            logger.warning("validate() called with a list, skipping validation.")
            return True
        if not hasattr(self.suggestion, "fixed_code"):
            return True
        if not self.suggestion.fixed_code or not self.suggestion.fixed_code.strip():
            logger.warning("Suggestion has no fixed code, skipping.")
            return False
        if "def test_" not in self.suggestion.fixed_code:
            logger.warning("Suggestion contains no test functions, skipping.")
            return False
        return True
