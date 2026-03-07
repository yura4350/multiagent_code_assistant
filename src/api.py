import os
import tempfile

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.agents.clean_code_agent import CleanCodeAgent
from src.agents.code_style_agent import StyleAgent
from src.agents.idioms_agent import IdiomsAgent
from src.agents.testing_agent import TestingAgent
from src.util.issue import Issue
from src.util.suggestion import Suggestion

app = FastAPI()

AGENT_REGISTRY = {
    "CODE_STYLE": StyleAgent,
    "IDIOMS": IdiomsAgent,
    "TESTS": TestingAgent,
    "CLEAN_CODE": CleanCodeAgent,
}

# Request / Response models


class AnalyzeRequest(BaseModel):
    file_content: str
    file_name: str = "temp.py"
    agent: str | None = None  # None will run all agents


class ScanRequest(BaseModel):
    file_content: str
    file_name: str = "temp.py"


class ScanResponse(BaseModel):
    issues: list[Issue]


class SuggestRequest(BaseModel):
    file_content: str
    file_name: str = "temp.py"
    issues: list[Issue]


class SuggestResponse(BaseModel):
    suggestions: list[Suggestion]


class ApplyRequest(BaseModel):
    file_content: str
    file_name: str = "temp.py"
    suggestions: list[Suggestion]


class ApplyResponse(BaseModel):
    fixed_content: str
    # Issues remaining after the fix has been applied
    remaining_issues: list[Issue]


class ValidateRequest(BaseModel):
    issues: list[Issue]


class ValidateResponse(BaseModel):
    is_valid: bool


# Helper functions
def _get_agent(agent_name: str):
    agent_class = AGENT_REGISTRY.get(agent_name)
    if agent_class is None:
        raise HTTPException(
            status_code=400, detail=f"Unknown/unsupported agent: {agent_name}"
        )
    return agent_class()


def _scan(agent, file_content: str, file_name: str) -> list[Issue]:
    """
    Scan code content with an agent that requires a file path.

    We persist `file_content` to a temporary source file, run `agent.scan()`,
    then always remove the temporary file.
    """
    temp_file_path = _write_temp_source_file(file_content, file_name)
    try:
        return agent.scan(temp_file_path)
    finally:
        # Ensure no temporary file remains, even on scan failure.
        os.unlink(temp_file_path)


def _write_temp_source_file(file_content: str, file_name: str) -> str:
    extension = os.path.splitext(file_name)[1] or ".py"
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=extension,
        delete=False,
        encoding="utf-8",
    ) as temp_file:
        temp_file.write(file_content)
        return temp_file.name


def _apply(agent, file_content: str, file_name: str, suggestions: list[Suggestion]):
    """
    Write content to a temp file, apply suggestions in-place, read back the
    fixed content, then delete the temp file.  Returns the fixed text.
    """
    temp_path = _write_temp_source_file(file_content, file_name)
    try:
        agent.apply(suggestions, temp_path)
        with open(temp_path, encoding="utf-8") as f:
            return f.read()
    finally:
        os.unlink(temp_path)


# Endpoints — scan
@app.post("/agents/{agent}/scan", response_model=ScanResponse)
def scan_endpoint(agent: str, request: ScanRequest):
    """Scan a file with the specified agent and return issues."""
    a = _get_agent(agent)
    issues = _scan(a, request.file_content, request.file_name)
    return ScanResponse(issues=issues)


# Endpoints — suggest
@app.post("/agents/{agent}/suggest", response_model=SuggestResponse)
def suggest_endpoint(agent: str, request: SuggestRequest):
    """Generate fix suggestions for a list of issues."""
    a = _get_agent(agent)
    suggestions = a.get_suggestions(request.issues, request.file_content)
    return SuggestResponse(suggestions=suggestions)


# Endpoints - apply
@app.post("/agents/{agent}/apply", response_model=ApplyResponse)
def apply_endpoint(agent: str, request: ApplyRequest):
    """
    Apply suggestions to the file content and return the fixed code together
    with any issues that remain after the fix.
    """
    a = _get_agent(agent)
    fixed_content = _apply(
        a, request.file_content, request.file_name, request.suggestions
    )
    # Re-scan the fixed content so the caller knows what (if anything) is left
    remaining_issues = _scan(a, fixed_content, request.file_name)
    return ApplyResponse(fixed_content=fixed_content, remaining_issues=remaining_issues)


# Endpoints - validate
@app.post("/agents/{agent}/validate", response_model=ValidateResponse)
def validate_endpoint(agent: str, request: ValidateRequest):
    """Validates the agent identified proper issues."""
    a = _get_agent(agent)
    is_valid = a.validate(request.issues)
    return ValidateResponse(is_valid=is_valid)


# Analyze code and return issues and suggestions
@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    """
    Run the full scan to suggest pipeline for one or all agents.
    Pass agent=null (or omit it) to run all agents.
    """
    if request.agent is not None:
        agents_to_run = [AGENT_REGISTRY.get(request.agent)]
        if None in agents_to_run:
            raise HTTPException(
                status_code=400, detail=f"Unknown agent: {request.agent}"
            )
    else:
        agents_to_run = list(AGENT_REGISTRY.values())

    temp_path = _write_temp_source_file(request.file_content, request.file_name)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(request.file_content)
        temp_path = f.name

    try:
        all_issues: list[Issue] = []
        all_suggestions: list[Suggestion] = []
        for agent_class in agents_to_run:
            a = agent_class()
            issues = a.scan(temp_path)
            suggestions = a.get_suggestions(issues, request.file_content)
            all_issues.extend(issues)
            all_suggestions.extend(suggestions)
        return {
            "issues": [i.model_dump() for i in all_issues],
            "suggestions": [s.model_dump() for s in all_suggestions],
        }
    finally:
        os.unlink(temp_path)


# Simple health check endpoint
@app.get("/health")
def health():
    return {"status": "ok"}
