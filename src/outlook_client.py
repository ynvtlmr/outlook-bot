import os
import subprocess
from typing import Optional

from config import APPLESCRIPTS_DIR


class OutlookClient:
    def __init__(self, scripts_dir: str) -> None:
        self.scripts_dir = scripts_dir

    def _run_script(self, script_name: str, args: Optional[list[str]] = None) -> Optional[str]:
        script_path = os.path.join(self.scripts_dir, script_name)
        cmd = ["osascript", script_path]
        if args:
            cmd.extend(args)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error running AppleScript {script_name}: {e.stderr}")
            return None

    def activate_outlook(self) -> None:
        """
        Activates the Microsoft Outlook application, bringing it to the foreground.
        """
        self._run_script("activate_outlook.scpt")

    def get_emails(self, email_address: str) -> Optional[str]:
        """
        Retrieves emails for a specific address.
        Returns a raw string of emails separated by likely newlines/custom delimiters.
        """
        # Note: The AppleScript needs to be robust enough to handle the arguments
        return self._run_script("get_emails.scpt", [email_address])

    def create_draft(self, to_address: str, subject: str, content: str) -> Optional[str]:
        """
        Creates a draft email.
        """
        return self._run_script("create_draft.scpt", [to_address, subject, content])

    def reply_to_message(
        self, message_id: str, content: Optional[str] = None, bcc_address: Optional[str] = None
    ) -> Optional[str]:
        """
        Replies to a specific message by ID, simulating 'Reply All'.
        """
        args = [str(message_id)]
        if content:
            args.append(content)
        else:
            args.append("Hey, when you have the chance, please send me an update.")

        if bcc_address:
            args.append(bcc_address)

        return self._run_script("reply_to_message.scpt", args)


def get_outlook_version() -> Optional[str]:
    """
    Retrieves the version of the currently installed/running Microsoft Outlook.
    Returns the version string or None if it fails.
    """
    script_path = os.path.join(APPLESCRIPTS_DIR, "get_version.scpt")

    if not os.path.exists(script_path):
        print(f"Error: Script not found at {script_path}")
        return None

    cmd = ["osascript", script_path]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error detecting Outlook version: {e.stderr}")
        return None
