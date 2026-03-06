import json
import logging
import os

from openai import OpenAI

from src.agents.abstract_agent import BaseAgent
from src.model.llm_applier import LLMApplier
from src.model.llm_generator import LLMGenerator
from src.model.llm_scanner import LLMScanner
from src.model.prompt_registry import PromptRegistry
from src.model.validator import Validator
from src.models.issue import Issue
from src.models.suggestion import Suggestion

logger = logging.getLogger(__name__)

class CleanCodeAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Clean Code")

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
        """Scan the code for adherence to the Clean Code principles"""
        content = self._read_file(file_path)
        client = self._get_client()
        model = self._get_model()

        llm_scanner = LLMScanner(
            client=client, model=model, prompt_registry=PromptRegistry()
        )

        context = {
            "content": content,
        }

        return llm_scanner.scan(prompt_name="cleancode.scan", context=context)

    def _read_file(self, file_path: str) -> str:
        with open(file_path, "r") as file:
            content = file.read()
            logger.info("File Successfully Read")
        return content