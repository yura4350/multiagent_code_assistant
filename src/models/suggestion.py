from src.models.issue import Issue
from pydantic import BaseModel


class Suggestion(BaseModel):
    issue: Issue
    original_code: str
    fixed_code: str
    rationale: str
    confidence: float | None = None  # 0.0-1.0, how confident is the fix

    def apply_to_file(self, file_path: str) -> None:
        """Apply this suggestion to a file"""
        # Phase 2 implementation
        pass
