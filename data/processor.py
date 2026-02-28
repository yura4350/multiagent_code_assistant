def calculate_average(numbers):
    """Calculates average. Missing check for empty list."""
    return sum(numbers) / len(numbers)

def get_user_status(age):
    """Returns status string based on age."""
    if age < 0:
        return "Invalid"
    if age < 18:
        return "Minor"
    elif age < 65:
        return "Adult"
    else:
        return "Senior"

def parse_config(config_str):
    """
    Parses a comma-separated string into a dict.
    Complex logic that needs edge case testing (e.g., malformed strings).
    """
    items = config_str.split(",")
    result = {}
    for item in items:
        key, value = item.split(":")
        result[key.strip()] = value.strip()
    return result