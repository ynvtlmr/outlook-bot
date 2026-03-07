"""Date parsing and extraction utilities for Outlook email timestamps."""

from __future__ import annotations

import re
from datetime import datetime

from dateutil import parser as dateutil_parser


def parse_date_string(date_str: str | None) -> datetime | None:
    """Parse a date string with cleaning for common Outlook/macOS oddities.

    Returns a datetime object or None on failure.
    """
    if not date_str:
        return None

    clean_str = date_str.replace("\u202f", " ").strip()

    try:
        return dateutil_parser.parse(clean_str)
    except (ValueError, OverflowError):
        return None


def extract_dates_from_text(text: str) -> list[datetime]:
    """Find all date-like strings in text, especially from email headers.

    Returns a list of successfully parsed datetime objects.
    """
    dates: list[datetime] = []

    patterns = [
        # Outlook verbose: "Date: Thursday, December 18, 2025 at 12:45:49 PM"
        re.compile(r"Date:\s+([A-Za-z]+,\s+[A-Za-z]+\s+\d+,\s+\d+\s+at\s+\d+:\d+:\d+\s+[APM]+)", re.IGNORECASE),
        # Standard reply header: "On Dec 18, 2025, at 12:45 PM"
        re.compile(r"On\s+([A-Za-z]+\s+\d+,\s+\d+,\s+at\s+\d+:\d+\s+[APM]+)", re.IGNORECASE),
        # Generic Date: line
        re.compile(r"^Date:\s+(.*)$", re.MULTILINE | re.IGNORECASE),
    ]

    for pattern in patterns:
        for match in pattern.finditer(text):
            parsed = parse_date_string(match.group(1))
            if parsed is not None:
                dates.append(parsed)

    return dates


def get_latest_date(text: str) -> datetime | None:
    """Return the latest datetime found in the text, or None if none found."""
    dates = extract_dates_from_text(text)
    return max(dates) if dates else None


def get_current_date_context() -> str:
    """Return a formatted string with the current date for the system prompt."""
    now = datetime.now()
    return now.strftime("Today is %A, %B %d, %Y.")
