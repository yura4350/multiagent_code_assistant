import logging
import json
import os

from src.models.suggestion import Suggestion
from src.model.testing_validator import Validator

logger = logging.getLogger(__name__)


class Applier:
    def __init__(self):
        pass

    def apply(self, suggestions: list[Suggestion], test_file_path):
        """Write suggested tests to the corresponding test file."""
        valid_suggestions = [s for s in suggestions if Validator(s).validate()]

        if not valid_suggestions:
            logger.warning("No valid suggestions to apply.")
            return

        # Combine all suggested test functions
        fixed_code_all = "\n\n".join(s.fixed_code for s in valid_suggestions)

        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(test_file_path), exist_ok=True)

        # Append the new tests to the end of the file
        with open(test_file_path, "a", encoding="utf-8") as f:
            f.write("\n\n" + fixed_code_all)
        logger.info(
            "Appended %d suggestions to %s", len(valid_suggestions), test_file_path
        )
    
    def _get_test_file_path(self, source_path: str) -> str:
        """Derive the test file path from a source file path.

        Example: src/agents/idioms_agent.py -> tests/agents/test_idioms_agent.py
        """
        if "src/" in source_path:
            source_path = source_path[source_path.index("src/") :]
        elif "data/" in source_path:
            source_path = source_path[source_path.index("data/") :]

        directory = source_path.rsplit("/", 1)[0]
        filename = source_path.rsplit("/", 1)[1]
        return f"tests/{directory}/test_{filename}"
