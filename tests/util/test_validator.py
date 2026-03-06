"""Tests for Validator (validator.py) and Validator (testing_validator.py)"""
from unittest.mock import MagicMock

from src.util.validator import Validator
from src.util.testing_validator import Validator as TestingValidator
from src.util.issue import Issue
from src.util.suggestion import Suggestion


def _make_issue():
    return Issue(line=1, message="msg", severity="warning", rule_id="R1", column=0)


def _make_suggestion(fixed_code):
    return Suggestion(
        issue=_make_issue(),
        fixed_code=fixed_code,
        rationale="reason",
    )


def test_validator_empty_issues_returns_true():
    assert Validator([]).validate() is True


def test_validator_with_issues_returns_false():
    assert Validator([_make_issue()]).validate() is False


def test_validator_multiple_issues_returns_false():
    assert Validator([_make_issue(), _make_issue()]).validate() is False



def test_testing_validator_list_returns_true():
    # When passed a list (controller misuse), should pass through
    assert TestingValidator([_make_issue()]).validate() is True


def test_testing_validator_valid_test_suggestion_returns_true():
    s = _make_suggestion("def test_foo():\n    assert True")
    assert TestingValidator(s).validate() is True


def test_testing_validator_no_test_function_returns_false():
    s = _make_suggestion("print('not a test')")
    assert TestingValidator(s).validate() is False


def test_testing_validator_empty_fixed_code_returns_false():
    s = _make_suggestion("")
    assert TestingValidator(s).validate() is False


def test_testing_validator_whitespace_only_fixed_code_returns_false():
    s = _make_suggestion("   \n  ")
    assert TestingValidator(s).validate() is False


def test_testing_validator_no_fixed_code_attr_returns_true():
    obj = MagicMock(spec=[])  # no attributes
    assert TestingValidator(obj).validate() is True
