from pathlib import Path


class PromptRegistry:
    def __init__(self, prompts_dir: Path | None = None) -> None:
        # project_root/prompts
        self.prompts_dir = (
            prompts_dir or Path(__file__).resolve().parents[2] / "prompts"
        )

        self._name_to_file = {
            "idioms.generate_suggestions": "idioms/generate_suggestions.txt",
            "idioms.scan": "idioms/scan.txt",
            # "idioms.apply": "idioms_apply.txt",
        }

    def load(self, prompt_name: str) -> str:
        if prompt_name not in self._name_to_file:
            raise ValueError(f"Unknown prompt name: {prompt_name}")

        prompt_path = self.prompts_dir / self._name_to_file[prompt_name]
        return prompt_path.read_text(encoding="utf-8")
