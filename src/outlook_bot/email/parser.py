"""Email parsing from AppleScript output into structured data."""

from __future__ import annotations

from outlook_bot.core.config import BODY_END, BODY_START, MSG_DELIMITER
from outlook_bot.core.models import Email
from outlook_bot.utils.dates import parse_date_string
from outlook_bot.utils.text import normalize_subject


def parse_raw_data(raw_data: str) -> list[Email]:
    """Parse raw AppleScript output string into a list of Email objects."""
    emails: list[Email] = []
    raw_msgs = raw_data.split(MSG_DELIMITER)

    for raw_msg in raw_msgs:
        if not raw_msg.strip():
            continue

        try:
            email = _parse_single_message(raw_msg)
            if email:
                emails.append(email)
        except Exception as e:
            print(f"Warning: Failed to parse message block: {e}")

    return emails


def _parse_single_message(raw_msg: str) -> Email | None:
    """Parse a single message block into an Email object."""
    lines = raw_msg.splitlines()
    content_lines: list[str] = []
    in_body = False

    msg_id = ""
    sender = ""
    date_str = ""
    subject = "No Subject"
    flag_status = ""
    message_id = ""

    for line in lines:
        stripped = line.strip()

        if stripped == BODY_START:
            in_body = True
            continue
        if stripped == BODY_END:
            in_body = False
            continue

        if in_body:
            content_lines.append(line)
        elif line.startswith("ID: "):
            msg_id = line[4:].strip()
        elif line.startswith("From: "):
            sender = line[6:].strip()
        elif line.startswith("Date: "):
            date_str = line[6:].strip()
        elif line.startswith("Subject: "):
            subject = line[9:].strip()
        elif line.startswith("FlagStatus: "):
            flag_status = line[12:].strip()
        elif line.startswith("MessageID: "):
            message_id = line[11:].strip()

    # Fallback for missing/generic IDs
    if not msg_id or msg_id == "NO_ID":
        msg_id = normalize_subject(subject)

    timestamp = parse_date_string(date_str)

    return Email(
        id=msg_id,
        subject=subject,
        sender=sender,
        date_str=date_str,
        timestamp=timestamp,
        content="\n".join(content_lines),
        flag_status=flag_status,
        message_id=message_id,
    )
