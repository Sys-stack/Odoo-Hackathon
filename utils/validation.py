import re
from datetime import datetime

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def is_valid_email(value):
    return bool(value) and bool(EMAIL_RE.match(value))


def parse_date(value, field_name="date"):
    """Parse an ISO 'YYYY-MM-DD' string into a date object, or raise ValueError."""
    if not value:
        raise ValueError(f"{field_name} is required.")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"{field_name} must be in YYYY-MM-DD format.")
