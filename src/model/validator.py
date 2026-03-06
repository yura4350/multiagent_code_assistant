import logging

from src.model.prompt_registry import PromptRegistry
from src.models.issue import Issue

logger = logging.getLogger(__name__)

class Validator:
    """Initialize the Validator"""
    def __init__(self, issues: list[Issue]):
        self.issues = issues

    def validate(self) -> bool:
        return len(self.issues) == 0