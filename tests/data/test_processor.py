# tests/utils/test_processor.py
from data.processor import calculate_average, get_user_status

def test_calculate_average_basic():
    # Weak test: Only tests standard input
    assert calculate_average([10, 20]) == 15.0

def test_get_user_status_basic():
    # Weak test: No assertions for edge cases like 0 or 18
    status = get_user_status(25)
    # This test has no assertion! The agent should flag this.