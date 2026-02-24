import argparse
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

AGENTS = ["CODE_STYLE", "IDIOMS", "TESTS", "DESIGN"]


@dataclass
class ParsedInput:
    agent: str | None
    file_path: str
    file_content: str
    apply: bool  # determine whether or not to apply the suggestions


def parse_input(args=None):
    parser = argparse.ArgumentParser(description="AI Code Assistant")
    parser.add_argument("file", help="Path to the source file")
    parser.add_argument(
        "--agent", choices=AGENTS, default=None, help="Agent to use (optional)"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply auto-fixes to the file",
    )
    parsed = parser.parse_args(args)

    file_path = os.path.abspath(parsed.file)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r") as f:
        file_content = f.read()

    logger.info("Read file: %s (%d chars)", file_path, len(file_content))

    return ParsedInput(
        agent=parsed.agent,
        file_path=file_path,
        file_content=file_content,
        apply=parsed.apply,
    )
