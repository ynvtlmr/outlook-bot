import html
import traceback
from datetime import datetime

import llm
from config import APPLESCRIPTS_DIR, DAYS_THRESHOLD, PREFERRED_MODEL, SYSTEM_PROMPT_PATH
from date_utils import get_current_date_context, get_latest_date
from outlook_client import OutlookClient, get_outlook_version
from scraper import run_scraper


def print_separator(char="-", length=30):
    print(char * length)


def check_outlook_status():
    """Detects if Outlook is running and returns version."""
    version = get_outlook_version()
    if version:
        print(f"Target Client: Microsoft Outlook {version}")
        return True
    else:
        print("Warning: Could not detect Outlook version. Is it running?")
        return False


def load_system_prompt():
    """Loads text from system_prompt.txt or returns default."""
    try:
        with open(SYSTEM_PROMPT_PATH, "r") as f:
            return f.read()
    except Exception as e:
        print(f"  -> Warning: Could not read system prompt: {e}")
        return "You are a helpful assistant."


def filter_threads_for_replies(threads):
    """
    Identifies threads that need a reply based on flag status and activity date.
    Returns a list of dicts: {'thread': thread, 'target_msg': msg, 'subject': subject}
    """
    candidates = []

    for i, thread in enumerate(threads):
        # 1. Check if thread has ANY active flag
        has_active_flag = any(m.get("flag_status") == "Active" for m in thread)

        if not has_active_flag:
            continue

        subject = thread[0].get("subject", "No Subject")
        print(f"\nAnalyzing Thread {i + 1}: {subject}")

        # 2. Find the TRULY latest activity date
        all_dates = []
        for m in thread:
            # Timestamp from header
            if m.get("timestamp") and m.get("timestamp") != datetime.min:
                all_dates.append(m.get("timestamp"))

            # Timestamp from body
            buried_date = get_latest_date(m.get("content", ""))
            if buried_date:
                all_dates.append(buried_date)

        if not all_dates:
            print("  -> Warning: Could not determine any activity date. Skipping.")
            continue

        latest_activity = max(all_dates)
        days_ago = (datetime.now() - latest_activity).days

        print(f"  -> Latest activity: {latest_activity.strftime('%Y-%m-%d %H:%M:%S')} ({days_ago} days ago)")

        # 3. Apply 7-day threshold
        if days_ago <= DAYS_THRESHOLD:
            print(f"  -> Activity within {DAYS_THRESHOLD} days. No reply needed yet.")
            continue

        print(f"  -> No activity for > {DAYS_THRESHOLD} days. Proceeding with draft.")

        # 4. Find target message (latest in thread)
        sorted_thread = sorted(thread, key=lambda m: m.get("timestamp", datetime.min))
        target_msg = sorted_thread[-1]

        candidates.append({"thread": thread, "target_msg": target_msg, "subject": subject})

    return candidates


def process_replies(candidates, client, system_prompt, llm_service):
    """
    Generates replies for candidates and creates drafts.
    """
    if not candidates:
        print("  -> No active threads requiring replies found.")
        return

    # Prepare Batch
    batch_jobs = []
    for item in candidates:
        target_msg = item["target_msg"]
        msg_id = target_msg.get("message_id")

        if not msg_id:
            print(f"  -> Error: No Message ID found for target message in '{item['subject']}'.")
            continue

        batch_jobs.append({"id": msg_id, "subject": item["subject"], "content": target_msg.get("content", "")})

    if not batch_jobs:
        return

    print(f"\nProcessing batch of {len(batch_jobs)} emails with LLM Service...")
    batch_replies = llm_service.generate_batch_replies(batch_jobs, system_prompt, preferred_model=PREFERRED_MODEL)

    print(f"Received {len(batch_replies)} replies from LLM Service.")

    for job in batch_jobs:
        msg_id = job["id"]
        subject = job["subject"]
        reply_text = batch_replies.get(msg_id)

        if reply_text:
            create_draft_reply(client, msg_id, subject, reply_text)
        else:
            print(f"  -> Warning: No reply generated for '{subject}' (ID: {msg_id})")


def create_draft_reply(client, msg_id, subject, reply_text):
    """Creates the actual draft in Outlook."""
    print(f"\nCreating draft for: {subject}")
    print("#" * 30)
    print(f"REPLY: {reply_text[:100]}...")
    print("#" * 30)

    try:
        # Prepare for HTML insertion
        html_safe_reply = html.escape(reply_text)
        formatted_reply = html_safe_reply.replace("\n", "<br>")

        result = client.reply_to_message(msg_id, formatted_reply)
        print(f"  -> {result}")
    except Exception as e:
        print(f"  -> Failed to create draft: {e}")


def main():
    print("--- Outlook Bot Generic Scraper ---")

    if not check_outlook_status():
        print_separator()
        # We continue anyway as some scripts might work or failure is soft
    else:
        print_separator()

    try:
        # 1. Scrape Flagged
        print("\n" + "=" * 30 + "\n")
        flagged_threads = run_scraper(mode="flagged")

        if not flagged_threads:
            print("No flagged threads found.")
            return

        # 2. Process Active Flags
        print("\n--- Processing Active Flags ---")
        client = OutlookClient(APPLESCRIPTS_DIR)
        # Load System Prompt and Date Context
        base_system_prompt = load_system_prompt()
        date_context = get_current_date_context()
        combined_system_prompt = f"{date_context}\n\n{base_system_prompt}"

        print(f"System Prompt Context: {date_context}")

        # Initialize LLM Service (Detects models)
        try:
            llm_service = llm.LLMService()
        except Exception as e:
            print(f"Error initializing LLM Service: {e}")
            return

        candidates = filter_threads_for_replies(flagged_threads)
        process_replies(candidates, client, combined_system_prompt, llm_service)

    except Exception as e:
        print(f"Error during execution: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
