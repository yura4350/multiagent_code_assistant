from unittest.mock import MagicMock

from src.util.llm_generator import LLMGenerator
from src.util.issue import Issue


def _make_issue(rule_id: str = "R1") -> Issue:
    return Issue(
        line=10,
        message="Sample issue",
        severity="warning",
        rule_id=rule_id,
        column=0,
    )


def _make_llm_response(content: str) -> MagicMock:
    resp = MagicMock()
    resp.choices[0].message.content = content
    return resp


def test_render_prompt_replaces_placeholders():
    mock_client = MagicMock()
    mock_registry = MagicMock()
    generator = LLMGenerator(client=mock_client, model="GPT 4.1", prompt_registry=mock_registry)

    template = "Code:\n{{ code }}\nIssues:\n{{ issues_json }}"
    context = {"code": "print('x')", "issues_json": '[{"rule_id":"R1"}]'}

    rendered = generator._render_prompt(template, context)

    assert "{{ code }}" not in rendered
    assert "{{ issues_json }}" not in rendered
    assert "print('x')" in rendered
    assert '[{"rule_id":"R1"}]' in rendered


def test_generate_suggestions_calls_registry_and_openai():
    mock_client = MagicMock()
    mock_registry = MagicMock()
    mock_registry.load.return_value = "Code:\n{{ code }}\nIssues:\n{{ issues_json }}"
    mock_client.chat.completions.create.return_value = _make_llm_response(
        """[
            {
                "issue": {"rule_id": "R1"},
                "original_code": "a=1",
                "fixed_code": "a = 1",
                "rationale": "Spacing",
                "confidence": 0.9
            }
        ]"""
    )

    generator = LLMGenerator(client=mock_client, model="GPT 4.1", prompt_registry=mock_registry)
    issues = [_make_issue("R1")]
    context = {"code": "a=1", "issues_json": '[{"rule_id":"R1"}]'}

    suggestions = generator.generate_suggestions("idioms.suggestions", context, issues)

    mock_registry.load.assert_called_once_with("idioms.suggestions")
    mock_client.chat.completions.create.assert_called_once()
    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "GPT 4.1"
    assert kwargs["messages"][0]["role"] == "user"
    assert "a=1" in kwargs["messages"][0]["content"]
    assert len(suggestions) == 1
    assert suggestions[0].issue.rule_id == "R1"


def test_generate_suggestions_returns_empty_when_llm_returns_no_content():
    mock_client = MagicMock()
    mock_registry = MagicMock()
    mock_registry.load.return_value = "Anything"
    mock_client.chat.completions.create.return_value = _make_llm_response(None)

    generator = LLMGenerator(client=mock_client, model="GPT 4.1", prompt_registry=mock_registry)
    issues = [_make_issue("R1")]

    suggestions = generator.generate_suggestions(
        "idioms.suggestions",
        {"code": "x", "issues_json": "[]"},
        issues,
    )

    assert suggestions == []


def test_parse_suggestions_valid_json_maps_to_issue():
    mock_client = MagicMock()
    mock_registry = MagicMock()
    generator = LLMGenerator(client=mock_client, model="GPT 4.1", prompt_registry=mock_registry)

    issues = [_make_issue("R1")]
    raw = """[
        {
            "issue": {"rule_id": "R1"},
            "original_code": "bad",
            "fixed_code": "good",
            "rationale": "fix it",
            "confidence": 1.0
        }
    ]"""

    suggestions = generator._parse_suggestions(raw, issues)

    assert len(suggestions) == 1
    assert suggestions[0].issue.rule_id == "R1"
    assert suggestions[0].original_code == "bad"
    assert suggestions[0].fixed_code == "good"
    assert suggestions[0].rationale == "fix it"
    assert suggestions[0].confidence == 1.0


def test_parse_suggestions_supports_space_keys():
    mock_client = MagicMock()
    mock_registry = MagicMock()
    generator = LLMGenerator(client=mock_client, model="GPT 4.1", prompt_registry=mock_registry)

    issues = [_make_issue("R1")]
    raw = """[
        {
            "issue": {"rule_id": "R1"},
            "original code": "bad",
            "fixed code": "good",
            "rationale": "legacy keys",
            "confidence": 0.8
        }
    ]"""

    suggestions = generator._parse_suggestions(raw, issues)

    assert len(suggestions) == 1
    assert suggestions[0].original_code == "bad"
    assert suggestions[0].fixed_code == "good"


def test_parse_suggestions_skips_unmatched_rule_id():
    mock_client = MagicMock()
    mock_registry = MagicMock()
    generator = LLMGenerator(client=mock_client, model="GPT 4.1", prompt_registry=mock_registry)

    issues = [_make_issue("R1")]
    raw = """[
        {
            "issue": {"rule_id": "R999"},
            "original_code": "bad",
            "fixed_code": "good",
            "rationale": "no matching issue"
        }
    ]"""

    suggestions = generator._parse_suggestions(raw, issues)

    assert suggestions == []


def test_parse_suggestions_invalid_json_returns_empty():
    mock_client = MagicMock()
    mock_registry = MagicMock()
    generator = LLMGenerator(client=mock_client, model="GPT 4.1", prompt_registry=mock_registry)

    issues = [_make_issue("R1")]
    suggestions = generator._parse_suggestions("not-json", issues)

    assert suggestions == []


def test_generate_suggestions_propagates_prompt_registry_error():
    mock_client = MagicMock()
    mock_registry = MagicMock()
    mock_registry.load.side_effect = ValueError("Unknown prompt name")

    generator = LLMGenerator(client=mock_client, model="GPT 4.1", prompt_registry=mock_registry)

    try:
        generator.generate_suggestions("bad.prompt", {"code": "x", "issues_json": "[]"}, [_make_issue()])
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Unknown prompt name" in str(exc)
