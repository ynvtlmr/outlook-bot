from datetime import datetime

from date_utils import get_latest_date, parse_date_string


def test_parse_date_string_formats():
    # Standard format
    d1 = parse_date_string("December 18, 2025 at 12:00 PM")
    assert d1.year == 2025 and d1.month == 12 and d1.day == 18

    # Short format
    d2 = parse_date_string("Dec 18, 2025, 12:00 PM")
    assert d2.year == 2025

    # Empty
    assert parse_date_string("") == datetime.min

    # Garbage
    assert parse_date_string("Not a date") == datetime.min


def test_parse_date_string_cleaning():
    # Non-breaking space \u202f
    raw = "Dec 18, 2025\u202fat 12:00 PM"
    d = parse_date_string(raw)
    assert d.year == 2025


def test_get_latest_date():
    # Matches strict regex: "On Dec 5, 2025, at 12:00 PM"
    text = """
    On Dec 1, 2025, at 10:00 AM, sent mail.
    Then on Dec 5, 2025, at 12:00 PM, replied.
    """
    latest = get_latest_date(text)
    assert latest is not None
    assert latest.day == 5

    text_no_date = "Just some text"
    assert get_latest_date(text_no_date) is None
