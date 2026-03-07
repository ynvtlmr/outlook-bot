"""Tests for the CLI entry point."""

from unittest.mock import MagicMock, patch

from outlook_bot.cli import _wait_for_outlook_ready
from outlook_bot.email.outlook_mac import OutlookMacClient


class TestWaitForOutlookReady:
    def test_success_immediate(self):
        client = MagicMock(spec=OutlookMacClient)
        client.get_version.return_value = "16.0"

        result = _wait_for_outlook_ready(client, timeout=1)
        assert result is True

    @patch("outlook_bot.cli.time.sleep")
    def test_timeout(self, mock_sleep):
        client = MagicMock(spec=OutlookMacClient)
        client.get_version.return_value = None

        result = _wait_for_outlook_ready(client, timeout=1)
        assert result is False
