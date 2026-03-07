import json
import logging

from openai import OpenAI

from src.util.issue import Issue
from src.util.prompt_registry import PromptRegistry
from src.util.suggestion import Suggestion

logger = logging.getLogger(__name__)


class LLMGenerator:
    def __init__(self, client: OpenAI, model: str, prompt_registry: PromptRegistry):
        """Initialize the LLMGenerator"""
        self.client = client
        self.model = model
        self.prompt_registry = prompt_registry

    def generate_suggestions(
        self, prompt_name: str, context: dict, issues: list[Issue]
    ) -> list[Suggestion]:
        template = self.prompt_registry.load(prompt_name)
        prompt = self._render_prompt(template, context)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.choices[0].message.content
        if raw:
            logger.info("raw: %s", raw)
            return self._parse_suggestions(raw, issues)

        return []

    def _render_prompt(self, template: str, context: dict[str, str]) -> str:
        rendered = template
        for key, value in context.items():
            rendered = rendered.replace(f"{{{{ {key} }}}}", value)
        return rendered

    def _parse_suggestions(
        self, response: str, issues: list[Issue]
    ) -> list[Suggestion]:
        """Parse LLM JSON response into a list of Suggestion objects."""
        try:
            clean = response.strip().removeprefix("```json").removesuffix("```").strip()
            data = json.loads(clean)
            issue_map = {issue.rule_id: issue for issue in issues}
            suggestions = []
            for item in data:
                rule_id = item.get("issue", {}).get("rule_id")
                issue = issue_map.get(rule_id)
                if not issue:
                    logger.warning(
                        "No matching issue for rule_id %s, skipping.", rule_id
                    )
                    continue
                suggestions.append(
                    Suggestion(
                        issue=issue,
                        original_code=item.get("original_code")
                        or item.get("original code"),
                        fixed_code=item.get("fixed_code") or item.get("fixed code"),
                        rationale=item.get("rationale", ""),
                        confidence=item.get("confidence"),
                    )
                )
            logger.info("Parsed %d suggestions from LLM response", len(suggestions))
            return suggestions
        except (json.JSONDecodeError, TypeError) as e:
            logger.error("Failed to parse suggestions from LLM response: %s", e)
            return []
