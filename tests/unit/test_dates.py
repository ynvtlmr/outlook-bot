"""Tests for date parsing utilities."""

from datetime import datetime

from outlook_bot.utils.dates import (
    extract_dates_from_text,
    get_current_date_context,
    get_latest_date,
    parse_date_string,
)


class TestParseDateString:
    def test_standard_format(self):
        result = parse_date_string("December 18, 2025")
        assert result is not None
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 18

    def test_outlook_verbose_format(self):
        result = parse_date_string("Thursday, December 18, 2025 at 12:45:49 PM")
        assert result is not None
        assert result.year == 2025

    def test_narrow_nonbreaking_space(self):
        result = parse_date_string("December 18, 2025 12:45\u202fPM")
        assert result is not None

    def test_none_input(self):
        assert parse_date_string(None) is None

    def test_empty_string(self):
        assert parse_date_string("") is None

    def test_invalid_string(self):
        assert parse_date_string("not a date") is None


class TestExtractDatesFromText:
    def test_finds_date_header(self):
        text = "Date: December 18, 2025\nSome content"
        dates = extract_dates_from_text(text)
        assert len(dates) >= 1
        assert dates[0].year == 2025

    def test_finds_on_pattern(self):
        text = "On Dec 18, 2025, at 12:45 PM, someone wrote:"
        dates = extract_dates_from_text(text)
        assert len(dates) >= 1

    def test_empty_text(self):
        assert extract_dates_from_text("") == []


class TestGetLatestDate:
    def test_finds_latest(self):
        text = "Date: December 18, 2025\nDate: January 5, 2026"
        result = get_latest_date(text)
        assert result is not None
        assert result.month == 1
        assert result.year == 2026

    def test_no_dates(self):
        assert get_latest_date("no dates here") is None


class TestGetCurrentDateContext:
    def test_format(self):
        result = get_current_date_context()
        assert result.startswith("Today is")
        assert str(datetime.now().year) in result
