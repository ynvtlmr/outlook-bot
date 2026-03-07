"""Tests for text processing utilities."""

from datetime import datetime

from outlook_bot.core.models import Email, Thread
from outlook_bot.utils.text import (
    extract_client_name,
    extract_client_name_from_subject,
    format_thread_content,
    is_gen_ii_email,
    normalize_subject,
    strip_gen_ii_footer,
)


class TestNormalizeSubject:
    def test_removes_re(self):
        assert normalize_subject("RE: Test Subject") == "Test Subject"

    def test_removes_fwd(self):
        assert normalize_subject("FWD: Test Subject") == "Test Subject"

    def test_removes_fw(self):
        assert normalize_subject("FW: Test Subject") == "Test Subject"

    def test_case_insensitive(self):
        assert normalize_subject("re: Test Subject") == "Test Subject"

    def test_no_prefix(self):
        assert normalize_subject("Test Subject") == "Test Subject"


class TestIsGenIIEmail:
    def test_gen2fund_domain(self):
        assert is_gen_ii_email("john@gen2fund.com") is True

    def test_gen_ii_name(self):
        assert is_gen_ii_email("Gen II Fund") is True

    def test_gen2_name(self):
        assert is_gen_ii_email("gen2 team") is True

    def test_other_domain(self):
        assert is_gen_ii_email("john@example.com") is False

    def test_empty(self):
        assert is_gen_ii_email("") is False


class TestExtractClientNameFromSubject:
    def test_colon_pattern(self):
        assert extract_client_name_from_subject("Acme Corp: Project Update") == "Acme Corp"

    def test_dash_pattern(self):
        assert extract_client_name_from_subject("Acme Corp - Meeting") == "Acme Corp"

    def test_between_pattern(self):
        assert extract_client_name_from_subject("between Acme Corp and Gen II") == "Acme Corp"

    def test_empty(self):
        assert extract_client_name_from_subject("") == "Unknown Client"

    def test_gen_ii_filtered(self):
        result = extract_client_name_from_subject("Gen II Fund: Update")
        assert result != "Gen II Fund"


class TestExtractClientName:
    def test_from_sender(self):
        thread = Thread(
            emails=[
                Email(id="1", sender="John Smith <john@example.com>", subject="Test"),
            ]
        )
        assert extract_client_name(thread) == "John Smith"

    def test_skips_gen_ii(self):
        thread = Thread(
            emails=[
                Email(id="1", sender="John <john@gen2fund.com>", subject="Acme Corp: Test"),
            ]
        )
        result = extract_client_name(thread)
        assert "gen2" not in result.lower()

    def test_empty_thread(self):
        thread = Thread()
        assert extract_client_name(thread) == "Unknown Client"


class TestStripGenIIFooter:
    def test_removes_footer(self):
        content = "Hello there.\n\nNOTICE: Unless otherwise stated, blah blah which can be found here."
        result = strip_gen_ii_footer(content)
        assert "NOTICE" not in result

    def test_preserves_content_without_footer(self):
        content = "Hello there. This is normal content."
        assert strip_gen_ii_footer(content) == content

    def test_empty_content(self):
        assert strip_gen_ii_footer("") == ""


class TestFormatThreadContent:
    def test_formats_thread(self):
        thread = Thread(
            emails=[
                Email(
                    id="1",
                    sender="test@example.com",
                    date_str="Dec 18, 2025",
                    subject="Test",
                    content="Hello",
                    timestamp=datetime.now(),
                ),
            ]
        )
        result = format_thread_content(thread)
        assert "From: test@example.com" in result
        assert "Hello" in result
        assert "--- Message 1 ---" in result
