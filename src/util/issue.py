from pydantic import BaseModel


class Issue(BaseModel):
    line: int
    message: str
    severity: str  # "error", "warning", or "info" # TODO: Use Enum
    rule_id: str  # pylint rule code (like "C0103")
    column: int | None = 0
