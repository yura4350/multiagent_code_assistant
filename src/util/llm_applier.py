import logging

from openai import OpenAI

from src.util.prompt_registry import PromptRegistry

logger = logging.getLogger(__name__)


class LLMApplier:
    def __init__(self, client: OpenAI, model: str, prompt_registry: PromptRegistry):
        """Initialize the LLMApplier"""
        self.client = client
        self.model = model
        self.prompt_registry = prompt_registry

    def apply(self, prompt_name: str, context: dict, file_path):
        template = self.prompt_registry.load(prompt_name)
        prompt = self._render_prompt(template, context)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.choices[0].message.content
        if raw:
            logger.info("raw: %s", raw)
            return self._parse_applied_suggestion(raw, file_path)

        return []

    def _render_prompt(self, template: str, context: dict[str, str]) -> str:
        rendered = template
        for key, value in context.items():
            rendered = rendered.replace(f"{{{{ {key} }}}}", value)
        return rendered

    def _parse_applied_suggestion(self, response: str, file_path: str) -> None:
        """Write the LLM-returned fixed code back to the file."""
        clean = response.strip().removeprefix("```python").removesuffix("```").strip()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(clean)
        logger.info("Applied suggestions to %s", file_path)
