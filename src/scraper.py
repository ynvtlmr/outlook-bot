import os
import re
from typing import Any

from config import APPLESCRIPTS_DIR, BODY_END, BODY_START, MSG_DELIMITER, OUTPUT_DIR
from date_utils import parse_date_string
from outlook_client import OutlookClient

# Type aliases for clarity
Message = dict[str, Any]
Thread = list[Message]


def parse_raw_data(raw_data: str) -> list[Message]:
    """
    Parses the raw string from AppleScript into a list of message dicts.
    """
    messages: list[Message] = []
    # Split by message delimiter (added regex for robustness against newline variations)
    raw_msgs = raw_data.split(MSG_DELIMITER)

    for raw_msg in raw_msgs:
        if not raw_msg.strip():
            continue

        msg: Message = {}
        try:
            lines = raw_msg.splitlines()
            content_lines: list[str] = []
            in_body = False

            for line in lines:
                if line.strip() == BODY_START:
                    in_body = True
                    continue
                if line.strip() == BODY_END:
                    in_body = False
                    continue

                if in_body:
                    content_lines.append(line)
                else:
                    if line.startswith("ID: "):
                        msg["id"] = line[4:].strip()
                    elif line.startswith("From: "):
                        msg["from"] = line[6:].strip()
                    elif line.startswith("Date: "):
                        date_str = line[6:].strip()
                        msg["date"] = date_str
                        msg["timestamp"] = parse_date_string(date_str)
                    elif line.startswith("Subject: "):
                        msg["subject"] = line[9:].strip()
                    elif line.startswith("FlagStatus: "):
                        msg["flag_status"] = line[12:].strip()
                    elif line.startswith("MessageID: "):
                        msg["message_id"] = line[11:].strip()

            msg["content"] = "\n".join(content_lines)

            # Fallback for subject grouping if ID is missing or generic
            if not msg.get("id") or msg.get("id") == "NO_ID":
                # Normalize subject (remove Re:, Fwd:)
                subj = msg.get("subject", "No Subject")
                norm_subj = re.sub(r"^(Re|Fwd|FW|RE):\s*", "", subj, flags=re.IGNORECASE).strip()
                msg["id"] = norm_subj

            messages.append(msg)
        except Exception as e:
            print(f"Warning: Failed to parse message block. Error: {e}")
            continue
    return messages


def group_into_threads(messages: list[Message]) -> list[Thread]:
    """
    Groups messages by their ID (conversation ID or Subject).
    Returns a list of threads (lists of messages).
    """
    threads_map: dict[str, Thread] = {}
    for msg in messages:
        t_id = msg.get("id")
        if t_id is None:
            continue
        if t_id not in threads_map:
            threads_map[t_id] = []
        threads_map[t_id].append(msg)

    return list(threads_map.values())


def scrape_messages(script_name: str, file_prefix: str = "thread") -> list[Thread] | None:
    """
    Generic function to run a scraping script and save the results.
    """
    client = OutlookClient(APPLESCRIPTS_DIR)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"Running {script_name}...")
    try:
        raw_data = client._run_script(script_name)
    except Exception as e:
        print(f"Error executing AppleScript: {e}")
        return None

    if not raw_data:
        print("No data returned from Outlook.")
        return None

    messages = parse_raw_data(raw_data)
    print(f"Parsed {len(messages)} messages.")

    threads = group_into_threads(messages)
    print(f"Identified {len(threads)} unique threads.")

    # Save first 50 threads
    top_threads = threads[:50]

    for i, thread in enumerate(top_threads):
        # Determine filename from subject of the first message
        first_msg = thread[0]
        safe_subject = "".join(
            [c for c in first_msg.get("subject", "thread") if c.isalnum() or c in (" ", "-", "_")]
        ).strip()[:50]
        filename = f"{file_prefix}_{i + 1}_{safe_subject}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            for msg in thread:
                f.write(f"From: {msg.get('from')}\n")
                f.write(f"Date: {msg.get('date')}\n")
                f.write(f"Subject: {msg.get('subject')}\n")
                f.write(f"Flag Status: {msg.get('flag_status', 'None')}\n")
                f.write("-" * 20 + "\n")
                f.write(msg.get("content", "") + "\n")
                f.write("=" * 80 + "\n\n")

    print(f"Successfully saved {len(top_threads)} threads to {os.path.abspath(OUTPUT_DIR)}")
    return top_threads


def run_scraper(mode: str = "recent") -> list[Thread]:
    """Run the scraper in the specified mode ('recent' or 'flagged')."""
    if mode == "recent":
        print("--- Scraping Recent Emails ---")
        return scrape_messages("get_recent_threads.scpt", file_prefix="recent") or []
    elif mode == "flagged":
        print("--- Scraping Flagged Emails (Full Threads) ---")
        return scrape_messages("get_flagged_threads.scpt", file_prefix="flagged") or []
    else:
        print(f"Unknown mode: {mode}")
        return []
