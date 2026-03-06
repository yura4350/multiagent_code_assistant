import json
import logging

from openai import OpenAI

from src.model.prompt_registry import PromptRegistry
from src.models.issue import Issue
from src.models.suggestion import Suggestion

logger = logging.getLogger(__name__)

class LLMScanner:

    """Initialize the LLMScanner"""
    def __init__(self, client: OpenAI, model: str, prompt_registry: PromptRegistry):
        self.client = client
        self.model = model
        self.prompt_registry = prompt_registry
    
    def scan(self, prompt_name: str, context: dict):
        template = self.prompt_registry.load(prompt_name)
        prompt = self._render_prompt(template, context)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.choices[0].message.content
        if raw:
            logger.info("raw: %s", raw)
            return self._parse_issues(raw)

        return []

    def _render_prompt(self, template: str, context: dict[str, str]) -> str:
        rendered = template
        for key, value in context.items():
            rendered = rendered.replace(f"{{{{ {key} }}}}", value)
        return rendered

    def _parse_issues(self, response: str) -> list[Issue]:
        """Parse LLM JSON response into a list of Issue objects."""
        try:
            clean = response.strip().removeprefix("```json").removesuffix("```").strip()
            data = json.loads(clean)
            issues = [Issue(**item) for item in data]
            logger.info("Parsed %d issues from LLM response", len(issues))
            return issues
        except (json.JSONDecodeError, TypeError) as e:
            logger.error("Failed to parse issues from LLM response: %s", e)
            return []