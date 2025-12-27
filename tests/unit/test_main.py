import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import main


class TestMainLogic(unittest.TestCase):
    def test_check_outlook_status_success(self):
        """Test detection of running Outlook."""
        with patch("main.get_outlook_version", return_value="16.0"):
            assert main.check_outlook_status() is True

    def test_check_outlook_status_failure(self):
        """Test failure when Outlook not running."""
        with patch("main.get_outlook_version", return_value=None):
            assert main.check_outlook_status() is False

    @patch("main.DAYS_THRESHOLD", 7)
    def test_filter_threads_for_replies(self):
        """Test filtering logic based on flags and dates."""

        # Case 1: Active flag, Old date (should reply)
        old_date = datetime.now() - timedelta(days=10)
        thread1 = [
            {
                "subject": "Old Active",
                "flag_status": "Active",
                "timestamp": old_date,
                "content": "Body",
                "message_id": "id1",
            }
        ]

        # Case 2: Active flag, Recent date (should skip)
        recent_date = datetime.now() - timedelta(days=2)
        thread2 = [
            {
                "subject": "Recent Active",
                "flag_status": "Active",
                "timestamp": recent_date,
                "content": "Body",
                "message_id": "id2",
            }
        ]

        # Case 3: Completed/No flag (should skip)
        thread3 = [
            {
                "subject": "No Flag",
                "flag_status": "Completed",
                "timestamp": old_date,
                "content": "Body",
                "message_id": "id3",
            }
        ]

        threads = [thread1, thread2, thread3]

        candidates = main.filter_threads_for_replies(threads)

        assert len(candidates) == 1
        assert candidates[0]["subject"] == "Old Active"

    def test_process_replies(self):
        """Test the reply processing flow."""
        mock_client = MagicMock()
        mock_service = MagicMock()

        candidates = [{"subject": "Subj", "target_msg": {"message_id": "mid1", "content": "HI"}}]

        # Mock batch response
        mock_service.generate_batch_replies.return_value = {"mid1": "Generated Reply"}

        with patch("main.create_draft_reply") as mock_create_draft:
            main.process_replies(candidates, mock_client, "sys prompt", mock_service)

            mock_service.generate_batch_replies.assert_called_once()
            mock_create_draft.assert_called_once_with(mock_client, "mid1", "Subj", "Generated Reply")

    def test_process_replies_no_candidates(self):
        """Test early return if no candidates."""
        mock_client = MagicMock()
        mock_service = MagicMock()

        main.process_replies([], mock_client, "sys", mock_service)
        mock_service.generate_batch_replies.assert_not_called()

    def test_wait_for_outlook_ready_success(self):
        """Test wait loop success."""
        with patch("main.get_outlook_version", return_value="16.0"):
            assert main.wait_for_outlook_ready(timeout=1) is True

    @patch("main.time.sleep", return_value=None) # Speed up test
    def test_wait_for_outlook_ready_timeout(self, mock_sleep):
        """Test wait loop timeout."""
        with patch("main.get_outlook_version", return_value=None):
            assert main.wait_for_outlook_ready(timeout=1) is False

    @patch("main.wait_for_outlook_ready", return_value=True)
    @patch("main.run_scraper")
    @patch("main.OutlookClient")
    @patch("main.llm.LLMService")
    def test_main_execution_flow(self, mock_llm, mock_client_cls, mock_scraper, mock_wait):
        """Test proper main flow: Activate -> Wait -> Scrape."""
        mock_scraper.return_value = []
        
        main.main()
        
        mock_client_instance = mock_client_cls.return_value
        mock_client_instance.activate_outlook.assert_called_once()
        mock_wait.assert_called_once()
