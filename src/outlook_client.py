import subprocess
import os

class OutlookClient:
    def __init__(self, scripts_dir):
        self.scripts_dir = scripts_dir

    def _run_script(self, script_name, args=None):
        script_path = os.path.join(self.scripts_dir, script_name)
        cmd = ['osascript', script_path]
        if args:
            cmd.extend(args)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error running AppleScript {script_name}: {e.stderr}")
            return None

    def get_emails(self, email_address):
        """
        Retrieves emails for a specific address.
        Returns a raw string of emails separated by likely newlines/custom delimiters.
        """
        # Note: The AppleScript needs to be robust enough to handle the arguments
        return self._run_script('get_emails.scpt', [email_address])

    def create_draft(self, to_address, subject, content):
        """
        Creates a draft email.
        """
        return self._run_script('create_draft.scpt', [to_address, subject, content])

    def reply_to_message(self, message_id, content):
        """
        Replies to a specific message by ID, simulating 'Reply All'.
        """
        return self._run_script('reply_to_message.scpt', [str(message_id), content])
