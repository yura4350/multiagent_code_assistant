import logging

from src.agents.abstract_agent import BaseAgent
from src.models.issue import Issue
from src.models.suggestion import Suggestion

logger = logging.getLogger(__name__)


class IdiomsAgent(BaseAgent):
    def __init__(self, agent_name: str) -> None:
        super().__init__("Idiom")

    """
    Scan the code for adherence to programming language idioms
    """

    def scan(self, file_path: str) -> list[Issue]:
        # read the given file - use self._read_file(file_path)
        # read the pythonic idiom file - use self._read_file(file_path)
        # create the prompt
        # Initiate generator
        # Parse generator output
        return super().scan(file_path)

    def generate_suggestions(self, issues: list[Issue], code: str) -> list[Suggestion]:
        return super().generate_suggestions(issues, code)
        # read given file + use issues from above
        # create the prompt
        # Initiate generator

    def validate(self, suggestion: Suggestion) -> bool:
        return super().validate(suggestion)

    def apply(self, suggestion: Suggestion, file_path: str) -> None:
        return super().apply(suggestion, file_path)

    def _read_file(self, file_path: str) -> str:
        return ""
