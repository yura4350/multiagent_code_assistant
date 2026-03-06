import logging
import subprocess

from src.util.suggestion import Suggestion

logger = logging.getLogger(__name__)


class Applier:
    def __init__(self):
        pass

    def apply(self, suggestions: list[Suggestion] | None, file_path: str) -> None:
        self._run_ruff_fix(file_path)
        self._run_ruff_format(file_path)

    def _run_ruff_fix(self, file_path: str) -> None:
        result = subprocess.run(
            ["ruff", "check", file_path, "--fix"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode not in (0, 1):
            logger.warning("Ruff fix failed: %s", result.stderr.strip())

    def _run_ruff_format(self, file_path: str) -> None:
        result = subprocess.run(
            ["ruff", "format", file_path],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode not in (0, 1):
            logger.warning("Ruff format failed: %s", result.stderr.strip())
