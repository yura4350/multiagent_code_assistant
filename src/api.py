import os
import tempfile

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.agents.code_style_agent import StyleAgent
from src.agents.idioms_agent import IdiomsAgent

app = FastAPI()

AGENT_REGISTRY = {
    "CODE_STYLE": StyleAgent,
    "IDIOMS": IdiomsAgent,
    "TESTS": None,  # Placeholder for TestAgent
    "DESIGN": None,  # Placeholder for DesignAgent
}

class AnalyzeRequest(BaseModel):
    file_content: str
    file_name: str = "temp.py"
    agent: str | None = None  # None will run all agents

# Analyze code and return issues and suggestions
@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
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
            suggestions = agent.generate_suggestions(issues, request.file_content)
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
async def health():
    return {"status": "ok"}
