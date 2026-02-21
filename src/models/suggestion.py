from models.issue import Issue
from pydantic import BaseModel


class Suggestion(BaseModel):
    issue: Issue
    original_code: str | None = None
    fixed_code: str | None = None
    rationale: str
    confidence: float | None = None  # 0.0-1.0, how confident is the fix
