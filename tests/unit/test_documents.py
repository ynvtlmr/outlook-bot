"""Tests for Word document generation."""

import os

from outlook_bot.core.models import ThreadSummary
from outlook_bot.utils.documents import create_summary_document


class TestCreateSummaryDocument:
    def test_creates_document(self, tmp_path):
        output_path = str(tmp_path / "test_summary.docx")
        summaries = [
            ThreadSummary(
                subject="Test Thread",
                client_name="Test Client",
                summary="This is a test summary.",
                sf_note="3/7/26 Sent follow-up email.",
            ),
        ]

        result = create_summary_document(summaries, output_path)
        assert result == output_path
        assert os.path.exists(output_path)

    def test_multiple_summaries(self, tmp_path):
        output_path = str(tmp_path / "multi_summary.docx")
        summaries = [
            ThreadSummary(subject="Thread 1", client_name="Client A", summary="Summary 1"),
            ThreadSummary(subject="Thread 2", client_name="Client B", summary="Summary 2", sf_note="Note"),
        ]

        result = create_summary_document(summaries, output_path)
        assert result == output_path

    def test_empty_summaries(self, tmp_path):
        output_path = str(tmp_path / "empty_summary.docx")
        result = create_summary_document([], output_path)
        assert result == output_path  # Creates doc even with empty list
