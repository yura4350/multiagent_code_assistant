from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import tempfile
from typing import Any

from src.agents.code_style_agent import StyleAgent
from src.agents.idioms_agent import IdiomsAgent
from src.agents.testing_agent import TestingAgent
from src.models.issue import Issue
from src.models.suggestion import Suggestion

app = FastAPI()

AGENT_REGISTRY = {
    "CODE_STYLE": StyleAgent,
    "IDIOMS": IdiomsAgent,
    "TESTS": TestingAgent,
    # "DESIGN": None,  # Placeholder for DesignAgent
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

# Helper functions
def _get_agent(agent_name: str):
    agent_class = AGENT_REGISTRY.get(agent_name)
    if agent_class is None:
        raise HTTPException(status_code=400, detail=f"Unknown/unsupported agent: {agent_name}")
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


# Endpoints

@app.post("/agents/{agent}/scan", response_model=ScanResponse)
def scan_endpoint(agent: str, request: ScanRequest):
    a = _get_agent(agent)
    issues = _scan(a, request.file_content, request.file_name)
    return ScanResponse(issues=issues)

# Analyze code and return issues and suggestions
@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    agents_to_run = (
        list(AGENT_REGISTRY.values())
        if request.agent is None
        else [AGENT_REGISTRY.get(request.agent)]
    )

    if None in agents_to_run:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {request.agent}")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(request.file_content)
        temp_path = f.name

    try:
        all_issues = []
        all_suggestions = []
        for agent_class in agents_to_run:
            agent = agent_class()
            issues = agent.scan(temp_path)
            suggestions = agent.get_suggestions(issues, request.file_content)
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
