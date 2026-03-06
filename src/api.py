import os
import tempfile

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.agents.code_style_agent import StyleAgent
from src.agents.idioms_agent import IdiomsAgent
from src.agents.testing_agent import TestingAgent
from src.agents.clean_code_agent import CleanCodeAgent
from src.util.issue import Issue
from src.util.suggestion import Suggestion

app = FastAPI()

AGENT_REGISTRY = {
    "CODE_STYLE": StyleAgent,
    "IDIOMS": IdiomsAgent,
    "TESTS": TestingAgent,
    "CLEAN_CODE": CleanCodeAgent
}

# Request / Response models


class AgentApplyResult(BaseModel):
    agent: str
    issues: list[Issue]
    suggestions: list[Suggestion]
    fixed_content: str
    remaining_issues: list[Issue]
    test_file_name: str | None = None


class AnalyzeRequest(BaseModel):
    file_content: str
    file_name: str = "temp.py"
    agent: str | None = None  # None will run all agents
    apply: bool = False 


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
    # Only set for TESTS agent: the name of the test file written
    test_file_name: str | None = None


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


def _apply_testing(file_content: str, file_name: str, suggestions: list[Suggestion]) -> tuple[str, str]:
    """
    Apply testing suggestions to a temporary test file.
    Returns (test_file_content, test_file_name).
    Does not modify the source file.
    """
    from src.util.testing_applier import Applier
    test_file_name = f"test_{file_name}"
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_test_path = os.path.join(tmpdir, test_file_name)
        Applier().apply(suggestions, test_file_path=temp_test_path)
        try:
            with open(temp_test_path, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            content = ""
    return content, test_file_name


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
    For the TESTS agent, fixed_content is the generated test file content and
    test_file_name is set to the suggested test file name.
    """
    a = _get_agent(agent)
    if agent == "TESTS":
        fixed_content, test_file_name = _apply_testing(
            request.file_content, request.file_name, request.suggestions
        )
        remaining_issues = _scan(a, request.file_content, request.file_name)
        return ApplyResponse(
            fixed_content=fixed_content,
            remaining_issues=remaining_issues,
            test_file_name=test_file_name,
        )
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


# Analyze code and return issues and suggestions (with optional apply)
@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    """
    Run the full scan → suggest pipeline for one or all agents.
    Pass agent=null (or omit it) to run all agents.
    Pass apply=true to also apply fixes; response will include apply_results per agent.
    """
    if request.agent is not None:
        agent_entries = [(request.agent, AGENT_REGISTRY.get(request.agent))]
        if agent_entries[0][1] is None:
            raise HTTPException(
                status_code=400, detail=f"Unknown agent: {request.agent}"
            )
    else:
        agent_entries = list(AGENT_REGISTRY.items())

    all_issues: list[Issue] = []
    all_suggestions: list[Suggestion] = []
    apply_results: list[dict] = []

    for agent_name, agent_class in agent_entries:
        a = agent_class()
        issues = _scan(a, request.file_content, request.file_name)
        suggestions = a.get_suggestions(issues, request.file_content)
        all_issues.extend(issues)
        all_suggestions.extend(suggestions)

        if request.apply:
            if agent_name == "TESTS":
                fixed_content, test_file_name = _apply_testing(
                    request.file_content, request.file_name, suggestions
                )
                remaining_issues = _scan(a, request.file_content, request.file_name)
                apply_results.append(AgentApplyResult(
                    agent=agent_name,
                    issues=issues,
                    suggestions=suggestions,
                    fixed_content=fixed_content,
                    remaining_issues=remaining_issues,
                    test_file_name=test_file_name,
                ).model_dump())
            else:
                fixed_content = _apply(a, request.file_content, request.file_name, suggestions)
                remaining_issues = _scan(a, fixed_content, request.file_name)
                apply_results.append(AgentApplyResult(
                    agent=agent_name,
                    issues=issues,
                    suggestions=suggestions,
                    fixed_content=fixed_content,
                    remaining_issues=remaining_issues,
                ).model_dump())

    response: dict = {
        "issues": [i.model_dump() for i in all_issues],
        "suggestions": [s.model_dump() for s in all_suggestions],
    }
    if request.apply:
        response["apply_results"] = apply_results
    return response


# Simple health check endpoint
@app.get("/health")
def health():
    return {"status": "ok"}
