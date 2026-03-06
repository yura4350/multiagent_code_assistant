"""Tests for PromptRegistry"""
import pytest
from pathlib import Path

from src.util.prompt_registry import PromptRegistry


def test_load_unknown_prompt_raises_value_error():
    registry = PromptRegistry()
    with pytest.raises(ValueError, match="Unknown prompt name"):
        registry.load("nonexistent.prompt")


def test_load_known_prompt_reads_file(tmp_path):
    prompt_file = tmp_path / "idioms" / "scan.txt"
    prompt_file.parent.mkdir()
    prompt_file.write_text("Scan this: {{ content }}")

    registry = PromptRegistry(prompts_dir=tmp_path)
    content = registry.load("idioms.scan")

    assert content == "Scan this: {{ content }}"


def test_load_all_registered_prompts_exist():
    registry = PromptRegistry()
    for name in registry._name_to_file:
        path = registry.prompts_dir / registry._name_to_file[name]
        assert path.exists(), f"Prompt file missing: {path}"
