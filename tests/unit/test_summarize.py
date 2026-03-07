"""Tests for the summarization workflow."""

from unittest.mock import MagicMock

from outlook_bot.core.models import Email, Thread
from outlook_bot.workflows.summarize import generate_thread_summaries


class TestGenerateThreadSummaries:
    def test_generates_summaries(self, tmp_path):
        mock_registry = MagicMock()
        mock_registry.generate_thread_summary.return_value = "Test summary paragraph."
        mock_registry.generate_sf_note.return_value = "3/7/26 Follow-up sent."

        thread = Thread(
            emails=[
                Email(id="1", subject="Test Thread", sender="client@example.com", content="Hello"),
            ]
        )

        mock_paths = MagicMock()
        mock_paths.output_dir = tmp_path / "output"
        mock_paths.ensure_output_dir.side_effect = lambda: (tmp_path / "output").mkdir(exist_ok=True)

        generate_thread_summaries([thread], mock_registry, paths=mock_paths)
        mock_registry.generate_thread_summary.assert_called_once()
        mock_registry.generate_sf_note.assert_called_once()

    def test_empty_threads(self):
        mock_registry = MagicMock()
        generate_thread_summaries([], mock_registry)
        mock_registry.generate_thread_summary.assert_not_called()

    def test_skips_empty_thread(self, tmp_path):
        mock_registry = MagicMock()
        mock_registry.generate_thread_summary.return_value = None

        empty_thread = Thread()

        mock_paths = MagicMock()
        mock_paths.output_dir = tmp_path / "output"
        mock_paths.ensure_output_dir.side_effect = lambda: (tmp_path / "output").mkdir(exist_ok=True)

        generate_thread_summaries([empty_thread], mock_registry, paths=mock_paths)
        mock_registry.generate_thread_summary.assert_not_called()
