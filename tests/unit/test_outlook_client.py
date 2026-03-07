"""Tests for the Outlook Mac client."""

from unittest.mock import MagicMock, patch

from outlook_bot.email.outlook_mac import OutlookMacClient


class TestOutlookMacClient:
    def test_run_script_success(self):
        client = OutlookMacClient("/fake/scripts")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="result\n", returncode=0)
            result = client._run_script("test.scpt")
            assert result == "result"

    def test_run_script_failure(self):
        client = OutlookMacClient("/fake/scripts")
        from subprocess import CalledProcessError

        with patch("subprocess.run", side_effect=CalledProcessError(1, "cmd", stderr="error")):
            result = client._run_script("test.scpt")
            assert result is None

    def test_activate(self):
        client = OutlookMacClient("/fake/scripts")
        with patch.object(client, "_run_script") as mock:
            client.activate()
            mock.assert_called_once_with("activate_outlook.scpt")

    def test_get_version(self):
        client = OutlookMacClient("/fake/scripts")
        with patch.object(client, "_run_script", return_value="16.0") as mock:
            result = client.get_version()
            assert result == "16.0"
            mock.assert_called_once_with("get_version.scpt")

    def test_reply_to_message(self):
        client = OutlookMacClient("/fake/scripts")
        with patch.object(client, "_run_script", return_value="OK") as mock:
            result = client.reply_to_message("msg123", "Reply text", "bcc@example.com")
            assert result == "OK"
            mock.assert_called_once_with("reply_to_message.scpt", ["msg123", "Reply text", "bcc@example.com"])

    def test_get_sent_recipients(self):
        client = OutlookMacClient("/fake/scripts")
        with patch.object(client, "_run_script", return_value="A@x.com\nB@y.com\n"):
            result = client.get_sent_recipients()
            assert result == {"a@x.com", "b@y.com"}

    def test_get_sent_recipients_empty(self):
        client = OutlookMacClient("/fake/scripts")
        with patch.object(client, "_run_script", return_value=None):
            result = client.get_sent_recipients()
            assert result == set()
