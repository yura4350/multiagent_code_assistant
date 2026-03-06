import json
import logging
import os

from openai import OpenAI

from src.agents.abstract_agent import BaseAgent
from src.util.issue import Issue
from src.util.llm_applier import LLMApplier
from src.util.llm_generator import LLMGenerator
from src.util.llm_scanner import LLMScanner
from src.util.prompt_registry import PromptRegistry
from src.util.suggestion import Suggestion
from src.util.validator import Validator

logger = logging.getLogger(__name__)


class IdiomsAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Idiom")

    def _get_client(self) -> OpenAI:
        token = os.getenv("LITELLM_TOKEN")
        if not token:
            raise RuntimeError(
                "Missing LITELLM_TOKEN. Put it in .env at project root or export it."
            )

        base_url = os.getenv("LLM_API_URL", "https://litellm.oit.duke.edu/v1")
        return OpenAI(api_key=token, base_url=base_url)

    def _get_model(self) -> str:
        return os.getenv("MODEL_ID", "GPT 4.1")

    def scan(self, file_path: str) -> list[Issue]:
        """Scan the code for adherence to programming language idioms"""
        content = self._read_file(file_path)
        client = self._get_client()
        model = self._get_model()

        llm_scanner = LLMScanner(
            client=client, model=model, prompt_registry=PromptRegistry()
        )

        context = {
            "content": content,
        }

        return llm_scanner.scan(prompt_name="idioms.scan", context=context)

    def get_suggestions(self, issues: list[Issue], code: str) -> list[Suggestion]:
        """Provide suggestions based on the scanned file and identified issues"""
        client = self._get_client()
        model = self._get_model()

        llm_generator = LLMGenerator(
            client=client, model=model, prompt_registry=PromptRegistry()
        )

        context = {
            "code": code,
            "issues_json": json.dumps(
                [issue.model_dump() for issue in issues], indent=2
            ),
        }

        return llm_generator.generate_suggestions(
            prompt_name="idioms.generate_suggestions", context=context, issues=issues
        )

    def validate(self, issues: list[Issue]) -> bool:
        validator = Validator(issues)
        return validator.validate()

    def apply(self, suggestions: list[Suggestion], file_path: str) -> None:
        """
        Suggestion contains an issue with original code and fixed code.
        This functions aggregates these suggestions and provides updated code.
        """
        client = self._get_client()
        model = self._get_model()

        llm_applier = LLMApplier(
            client=client, model=model, prompt_registry=PromptRegistry()
        )

        context = {
            "code": self._read_file(file_path),
            "suggestions_json": json.dumps(
                [s.model_dump() for s in suggestions], indent=2
            ),
        }

        return llm_applier.apply(
            prompt_name="idioms.apply", context=context, file_path=file_path
        )

    def _read_file(self, file_path: str) -> str:
        with open(file_path, "r") as file:
            content = file.read()
            logger.info("File Successfully Read")
        return content
