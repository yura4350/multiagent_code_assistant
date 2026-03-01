from openai import OpenAI
import json
from src.models.issue import Issue
from src.models.suggestion import Suggestion
import logging

logger = logging.getLogger(__name__)

class LLMGenerator:
    def __init__(self, client: OpenAI, model: str, issues: list[Issue], code: str, prompt: str):
        """Initialize the LLMGenerator"""
        self.client = client
        self.model = model
        self.issues = issues
        self.code = code
        self.prompt = prompt
    
    def generate_suggestions(self) -> list[Suggestion]:
        """Generate suggestions based on the scanned file and identified issues"""
        issues_json = json.dumps([issue.model_dump() for issue in self.issues], indent=2)

        response = self.client.chat.completions.create(
            model = self.model,
            messages=[{"role": "user", "content": self.prompt}],
        )

        raw = response.choices[0].message.content
        if raw:
            logger.info("raw: %s", raw)
            return self._parse_suggestions(raw, self.issues)

        return []
    
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
    
    


