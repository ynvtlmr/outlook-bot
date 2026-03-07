"""Tests for email parsing."""

from outlook_bot.email.parser import parse_raw_data
from outlook_bot.email.threading import group_into_threads


class TestParseRawData:
    def test_parses_messages(self, mock_raw_applescript_output):
        emails = parse_raw_data(mock_raw_applescript_output)
        assert len(emails) == 2

        e1 = emails[0]
        assert e1.id == "101"
        assert e1.subject == "Re: Project Update"
        assert "This is the email body" in e1.content
        assert e1.message_id == "<123@example.com>"
        assert e1.timestamp is not None
        assert e1.timestamp.year == 2025

    def test_empty_input(self):
        assert parse_raw_data("") == []

    def test_fallback_id_from_subject(self):
        raw = """Subject: Test Subject
FlagStatus: Active
MessageID: <test@example.com>
---BODY_START---
Body
---BODY_END---
///END_OF_MESSAGE///
"""
        emails = parse_raw_data(raw)
        assert len(emails) == 1
        assert emails[0].id == "Test Subject"

    def test_flag_status_parsed(self, mock_raw_applescript_output):
        emails = parse_raw_data(mock_raw_applescript_output)
        assert emails[0].flag_status == "Active"


class TestGroupIntoThreads:
    def test_groups_by_id(self):
        from outlook_bot.core.models import Email

        emails = [
            Email(id="A", subject="Thread A"),
            Email(id="A", subject="Re: Thread A"),
            Email(id="B", subject="Thread B"),
        ]
        threads = group_into_threads(emails)
        assert len(threads) == 2

        lengths = sorted(len(t.emails) for t in threads)
        assert lengths == [1, 2]

    def test_empty_input(self):
        assert group_into_threads([]) == []
