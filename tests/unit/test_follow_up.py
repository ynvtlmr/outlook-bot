"""Tests for the follow-up workflow."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

from outlook_bot.core.models import Email, Thread
from outlook_bot.workflows.follow_up import filter_threads_for_replies, process_replies


class TestFilterThreadsForReplies:
    def test_filters_old_active_threads(self, sample_threads):
        candidates = filter_threads_for_replies(sample_threads, days_threshold=7)
        assert len(candidates) == 1
        assert candidates[0]["subject"] == "Active Old"

    def test_skips_recent_active(self, sample_threads):
        candidates = filter_threads_for_replies(sample_threads, days_threshold=7)
        subjects = [c["subject"] for c in candidates]
        assert "Active Recent" not in subjects

    def test_skips_completed(self, sample_threads):
        candidates = filter_threads_for_replies(sample_threads, days_threshold=7)
        subjects = [c["subject"] for c in candidates]
        assert "Completed" not in subjects

    def test_edge_case_exact_threshold(self):
        thread = Thread(
            emails=[
                Email(
                    id="edge",
                    subject="Edge Case",
                    flag_status="Active",
                    timestamp=datetime.now() - timedelta(days=7),
                    content="body",
                    message_id="edge-msg",
                ),
            ]
        )
        candidates = filter_threads_for_replies([thread], days_threshold=7)
        assert len(candidates) == 0  # 7 days ago == threshold, not exceeded

    def test_no_timestamp_skipped(self):
        thread = Thread(
            emails=[
                Email(id="no-ts", subject="No Timestamp", flag_status="Active", message_id="no-ts-msg"),
            ]
        )
        candidates = filter_threads_for_replies([thread], days_threshold=7)
        assert len(candidates) == 0


class TestProcessReplies:
    def test_creates_drafts(self):
        mock_client = MagicMock()
        mock_registry = MagicMock()
        mock_registry.generate_batch_replies.return_value = {"mid1": "Generated Reply"}

        candidates = [
            {
                "subject": "Test",
                "target_email": Email(id="1", message_id="mid1", content="Hi"),
            }
        ]

        process_replies(candidates, mock_client, "sys prompt", mock_registry, preferred_model="gpt-4")
        mock_registry.generate_batch_replies.assert_called_once()
        mock_client.reply_to_message.assert_called_once()

    def test_no_candidates_skips(self):
        mock_client = MagicMock()
        mock_registry = MagicMock()

        process_replies([], mock_client, "sys", mock_registry)
        mock_registry.generate_batch_replies.assert_not_called()

    def test_missing_message_id_skipped(self):
        mock_client = MagicMock()
        mock_registry = MagicMock()

        candidates = [
            {
                "subject": "Test",
                "target_email": Email(id="1", content="Hi"),  # no message_id
            }
        ]

        process_replies(candidates, mock_client, "sys", mock_registry)
        mock_registry.generate_batch_replies.assert_not_called()
