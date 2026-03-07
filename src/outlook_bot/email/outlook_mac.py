"""macOS Outlook client using AppleScript for automation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from outlook_bot.email.client import EmailClient
from outlook_bot.email.parser import parse_raw_data
from outlook_bot.email.threading import group_into_threads

if TYPE_CHECKING:
    from outlook_bot.core.models import Thread


class OutlookMacClient(EmailClient):
    """Outlook client using AppleScript for macOS automation."""

    def __init__(self, scripts_dir: str | Path) -> None:
        self.scripts_dir = Path(scripts_dir)

    def _run_script(self, script_name: str, args: list[str] | None = None) -> str | None:
        """Execute an AppleScript and return its stdout."""
        script_path = self.scripts_dir / script_name
        cmd = ["osascript", str(script_path)]
        if args:
            cmd.extend(args)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error running AppleScript {script_name}: {e.stderr}")
            return None

    def activate(self) -> None:
        self._run_script("activate_outlook.scpt")

    def get_version(self) -> str | None:
        return self._run_script("get_version.scpt")

    def _scrape_and_parse(self, script_name: str) -> list[Thread]:
        """Generic scrape -> parse -> thread pipeline."""
        raw_data = self._run_script(script_name)
        if not raw_data:
            return []

        emails = parse_raw_data(raw_data)
        print(f"Parsed {len(emails)} messages.")

        threads = group_into_threads(emails)
        print(f"Identified {len(threads)} unique threads.")
        return threads

    def scrape_flagged_threads(self) -> list[Thread]:
        print("--- Scraping Flagged Emails (Full Threads) ---")
        return self._scrape_and_parse("get_flagged_threads.scpt")

    def scrape_recent_threads(self) -> list[Thread]:
        print("--- Scraping Recent Emails ---")
        return self._scrape_and_parse("get_recent_threads.scpt")

    def create_draft(self, to_address: str, subject: str, content: str, bcc_address: str = "") -> str | None:
        args = [to_address, subject, content]
        if bcc_address:
            args.append(bcc_address)
        return self._run_script("create_draft.scpt", args)

    def reply_to_message(self, message_id: str, content: str, bcc_address: str = "") -> str | None:
        args = [str(message_id), content]
        if bcc_address:
            args.append(bcc_address)
        return self._run_script("reply_to_message.scpt", args)

    def get_sent_recipients(self) -> set[str]:
        result = self._run_script("check_sent_to.scpt")
        if not result:
            return set()
        return {addr.strip().lower() for addr in result.splitlines() if addr.strip()}

    def save_threads_to_disk(self, threads: list[Thread], output_dir: str | Path, prefix: str = "thread") -> None:
        """Save threads to disk for debugging/reference."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, thread in enumerate(threads[:50]):
            safe_subject = "".join(c for c in thread.subject if c.isalnum() or c in (" ", "-", "_")).strip()[:50]
            filename = f"{prefix}_{i + 1}_{safe_subject}.txt"
            filepath = output_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                for email in thread.emails:
                    f.write(f"From: {email.sender}\n")
                    f.write(f"Date: {email.date_str}\n")
                    f.write(f"Subject: {email.subject}\n")
                    f.write(f"Flag Status: {email.flag_status or 'None'}\n")
                    f.write("-" * 20 + "\n")
                    f.write(email.content + "\n")
                    f.write("=" * 80 + "\n\n")

        print(f"Saved {min(len(threads), 50)} threads to {output_dir}")
