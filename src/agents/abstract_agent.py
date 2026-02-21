from abc import ABC, abstractmethod
from models.issue import Issue
from models.suggestion import Suggestion


class BaseAgent(ABC):
    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name

    @abstractmethod
    def scan(self, file_path: str) -> list[Issue]:
        """Scan code file and return list of issues found"""
        pass

    @abstractmethod
    def generate_suggestions(self, issues: list[Issue], code: str) -> list[Suggestion]:
        """Generate fix suggestions for given issues"""
        pass
    
    @abstractmethod
    def validate(self, suggestion: Suggestion) -> bool:
        """Validate a suggestion"""
        pass
    
    def apply(self, suggestion: Suggestion, file_path: str) -> None:  # TODO: Phase 2
        """Apply suggestion to file"""
        pass
