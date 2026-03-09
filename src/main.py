import os
import re
import time
import traceback
from collections import Counter
from datetime import datetime
from typing import Any

import yaml

import llm
from cold_outreach import process_cold_outreach
from config import (
    APPLESCRIPTS_DIR,
    COLD_OUTREACH_PROMPT_PATH,
    CONFIG_PATH,
    OUTPUT_DIR,
    SYSTEM_PROMPT_PATH,
    UPSELL_OUTREACH_PROMPT_PATH,
)
from upsell_outreach import process_upsell_outreach
from date_utils import get_current_date_context, get_latest_date
from outlook_client import OutlookClient, get_outlook_version
from scraper import run_scraper
from word_doc import create_summary_document, format_thread_content


def print_separator(char: str = "-", length: int = 30) -> None:
    print(char * length)


def check_outlook_status() -> bool:
    """Detects if Outlook is running and returns version."""
    version = get_outlook_version()
    if version:
        print(f"Target Client: Microsoft Outlook {version}")
        return True
    else:
        print("Warning: Could not detect Outlook version. Please ensure Microsoft Outlook is running.")
        return False


def wait_for_outlook_ready(timeout: int = 60) -> bool:
    """
    Waits for Outlook to become responsive by polling its version.
    Returns True if ready, False if timeout reached.
    """
    print(f"Waiting for Outlook to be ready (timeout: {timeout}s)...")
    start_time = time.time()

    while (time.time() - start_time) < timeout:
        version = get_outlook_version()
        if version:
            print(f"  -> Outlook ({version}) is ready.")
            return True
        print("  -> Waiting for Outlook...")
        time.sleep(2)

    print("  -> Error: Timeout waiting for Outlook to start.")
    return False


def load_system_prompt() -> str:
    """Loads text from system_prompt.txt or returns default."""
    try:
        with open(SYSTEM_PROMPT_PATH, "r") as f:
            return f.read()
    except Exception as e:
        print(f"  -> Warning: Could not read system prompt: {e}")
        return "You are a helpful assistant."


def filter_threads_for_replies(threads: list[list[dict[str, Any]]], days_threshold: int) -> list[dict[str, Any]]:
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
        if days_ago <= days_threshold:
            print(f"  -> Activity within {days_threshold} days. No reply needed yet.")
            continue

        print(f"  -> No activity for > {days_threshold} days. Proceeding with draft.")

        # 4. Find target message (latest in thread)
        sorted_thread = sorted(thread, key=lambda m: m.get("timestamp", datetime.min))
        target_msg = sorted_thread[-1]

        candidates.append({"thread": thread, "target_msg": target_msg, "subject": subject})

    return candidates


def process_replies(
    candidates: list[dict[str, Any]],
    client: OutlookClient,
    system_prompt: str,
    llm_service: llm.LLMService,
    preferred_model: str | None = None,
    salesforce_bcc: str = "",
) -> None:
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
    batch_replies = llm_service.generate_batch_replies(batch_jobs, system_prompt, preferred_model=preferred_model)

    print(f"Received {len(batch_replies)} replies from LLM Service.")

    for job in batch_jobs:
        msg_id = job["id"]
        subject = job["subject"]
        reply_text = batch_replies.get(msg_id)

        if reply_text:
            create_draft_reply(client, msg_id, subject, reply_text, salesforce_bcc)

            # Generate and print SF Note
            print("  -> Generating SF Note...")
            sf_note = llm_service.generate_sf_note(job["content"], preferred_model=preferred_model)
            if sf_note:
                print(f"\n📋 SF Note for '{subject}':\n   {sf_note}\n")
            else:
                print(f"  -> Warning: Failed to generate SF Note for '{subject}'")
        else:
            print(f"  -> Warning: No reply generated for '{subject}' (ID: {msg_id})")


def create_draft_reply(
    client: OutlookClient, msg_id: str, subject: str, reply_text: str, bcc_address: str = ""
) -> None:
    """Creates the actual draft in Outlook."""
    print(f"\nCreating draft for: {subject}")
    print("#" * 30)
    print(f"REPLY: {reply_text[:100]}...")
    print("#" * 30)

    try:
        # Prepare for AppleScript: convert newlines to <br> tags
        # The AppleScript will convert <br> back to newlines for typing
        # We don't need HTML escaping since we're using UI automation (keystrokes)
        formatted_reply = reply_text.replace("\n", "<br>")

        result = client.reply_to_message(msg_id, formatted_reply, bcc_address=bcc_address)
        print(f"  -> {result}")
    except Exception as e:
        print(f"  -> Failed to create draft: {e}")


def is_gen_ii_email(from_address: str) -> bool:
    """Check if an email is from Gen II."""
    if not from_address:
        return False
    from_lower = from_address.lower()
    return "@gen2fund.com" in from_lower or "gen ii" in from_lower or "gen2" in from_lower


def extract_client_name_from_subject(subject: str) -> str:
    """Extract client name from subject line."""
    if not subject:
        return "Unknown Client"

    # Remove common prefixes
    subject_clean = re.sub(r"^(RE|FWD|FW):\s*", "", subject, flags=re.IGNORECASE).strip()

    # Look for patterns like "Client Name:" or "Client Name -"
    # Also look for "between X and Y" patterns
    match = re.search(r"between\s+([^<>]+?)\s+and", subject_clean, re.IGNORECASE)
    if match:
        potential_client = match.group(1).strip()
        if not is_gen_ii_email(potential_client):
            return potential_client

    # Look for "Client Name:" pattern
    match = re.search(r"^([^:<>]+?):", subject_clean)
    if match:
        potential_client = match.group(1).strip()
        if not is_gen_ii_email(potential_client):
            return potential_client

    # Look for "Client Name -" or "Client Name =>" pattern
    # Match both plain hyphens (with or without following text) and arrow patterns (=>)
    match = re.search(r"^([^<>-]+?)\s*[-=](?:>|\s|$)", subject_clean)
    if match:
        potential_client = match.group(1).strip()
        if not is_gen_ii_email(potential_client):
            return potential_client

    # If no pattern found, return first part before any separator
    parts = re.split(r"[-=<>:]", subject_clean, 1)
    if parts and parts[0].strip():
        potential_client = parts[0].strip()
        if not is_gen_ii_email(potential_client):
            return potential_client

    return subject_clean[:50] if subject_clean else "Unknown Client"


def extract_client_name(thread: list[dict[str, Any]]) -> str:
    """
    Extract client name from thread messages, excluding Gen II emails.
    Falls back to subject line extraction if uncertain.
    """
    if not thread:
        return "Unknown Client"

    # Get subject from first message
    subject = thread[0].get("subject", "")

    # Look through all messages for sender names/addresses
    client_candidates = []
    for msg in thread:
        from_field = msg.get("from", "")
        if not from_field:
            continue

        # Extract email address if present
        email_match = re.search(r"<([^>]+)>", from_field)
        email = email_match.group(1) if email_match else from_field

        # Extract name if present
        name_match = re.search(r"^([^<]+)", from_field)
        name = name_match.group(1).strip() if name_match else ""

        # Skip Gen II emails
        if is_gen_ii_email(email) or is_gen_ii_email(name):
            continue

        # Prefer name over email
        if name:
            client_candidates.append(name)
        elif email and "@" in email:
            # Extract domain or username as fallback
            domain = email.split("@")[1] if "@" in email else email
            if "gen2fund.com" not in domain.lower():
                client_candidates.append(domain.split(".")[0].title())

    # If we found candidates, use the most common one
    if client_candidates:
        # Count occurrences
        counter = Counter(client_candidates)
        most_common = counter.most_common(1)[0][0]
        return most_common

    # Fallback to subject line extraction
    return extract_client_name_from_subject(subject)


def generate_thread_summaries(
    flagged_threads: list[list[dict[str, Any]]], llm_service: llm.LLMService, preferred_model: str | None = None
) -> None:
    """
    Generates summaries and SF Notes for all flagged threads and creates a Word document.
    """
    if not flagged_threads:
        print("No flagged threads to summarize.")
        return

    print(f"\n--- Generating Summaries for {len(flagged_threads)} Flagged Threads ---")

    threads_with_summaries = []

    for idx, thread in enumerate(flagged_threads, 1):
        # Guard against empty threads
        if not thread:
            print(f"\nSkipping Thread {idx}/{len(flagged_threads)}: Empty thread")
            continue

        subject = thread[0].get("subject", "No Subject")
        print(f"\nProcessing Thread {idx}/{len(flagged_threads)}: {subject}")

        # Extract client name
        client_name = extract_client_name(thread)
        print(f"  -> Client: {client_name}")

        # Format thread content
        thread_content = format_thread_content(thread)

        # Generate summary
        print("  -> Generating summary...")
        summary = llm_service.generate_thread_summary(thread_content, preferred_model=preferred_model)

        # Generate SF Note
        print("  -> Generating SF Note...")
        sf_note = llm_service.generate_sf_note(thread_content, preferred_model=preferred_model)

        if summary:
            threads_with_summaries.append(
                {
                    "subject": subject,
                    "client_name": client_name,
                    "summary": summary,
                    "sf_note": sf_note if sf_note else "SF Note generation failed.",
                    "thread": thread,
                }
            )
            print("  -> Summary generated successfully")
            if sf_note:
                print("  -> SF Note generated successfully")
            else:
                print(f"  -> Warning: Failed to generate SF Note for '{subject}'")
        else:
            print(f"  -> Warning: Failed to generate summary for '{subject}'")

    if threads_with_summaries:
        # Create Word document
        # Use OUTPUT_DIR from config instead of os.getcwd() for reliability
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        date_str = datetime.now().strftime("%m-%d-%Y")
        output_path = os.path.join(OUTPUT_DIR, f"email_summary_{date_str}.docx")

        print("\n--- Creating Word Document ---")
        result = create_summary_document(threads_with_summaries, output_path)

        if result:
            print(f"✓ Word document created: {output_path}")
        else:
            print("✗ Failed to create Word document.")
    else:
        print("No summaries generated. Skipping document creation.")


def _setup() -> dict[str, Any] | None:
    """Shared setup: initializes Outlook, loads config, and creates the LLM service.

    Returns a dict with shared state, or None if setup failed.
    """
    print("--- Outlook Bot Setup ---")

    # Initialize Client and Focus Outlook
    client = OutlookClient(APPLESCRIPTS_DIR)
    print("Launching/Focusing Outlook...")
    client.activate_outlook()

    # Wait for Outlook to load
    if not wait_for_outlook_ready():
        return None

    # Load Config (Dynamically to catch GUI changes)
    try:
        with open(CONFIG_PATH, "r") as f:
            config_data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        config_data = {}
    except Exception as e:
        print(f"Warning: Error loading config.yaml: {e}")
        config_data = {}

    days_threshold = config_data.get("days_threshold", 5)
    preferred_model = config_data.get("preferred_model", None)
    salesforce_bcc = config_data.get("salesforce_bcc", "")
    cold_outreach_enabled = config_data.get("cold_outreach_enabled", False)
    cold_outreach_csv_path = config_data.get("cold_outreach_csv_path", "")
    follow_up_daily_limit = config_data.get("follow_up_daily_limit", 50)
    cold_outreach_daily_limit = config_data.get("cold_outreach_daily_limit", 10)
    cold_outreach_strategy = config_data.get("cold_outreach_strategy", "default")
    upsell_outreach_enabled = config_data.get("upsell_outreach_enabled", False)
    upsell_outreach_daily_limit = config_data.get("upsell_outreach_daily_limit", 5)
    upsell_principal_csv_path = config_data.get("upsell_principal_csv_path", "")
    upsell_exclude_principals = config_data.get("upsell_exclude_principals", [])
    print(
        f"Configuration Loaded: Days Threshold={days_threshold}, "
        f"Preferred Model={preferred_model}, BCC={salesforce_bcc}, "
        f"Cold Outreach={'ON' if cold_outreach_enabled else 'OFF'}, "
        f"Upsell Outreach={'ON' if upsell_outreach_enabled else 'OFF'}"
    )

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
        return None

    return {
        "client": client,
        "config_data": config_data,
        "days_threshold": days_threshold,
        "preferred_model": preferred_model,
        "salesforce_bcc": salesforce_bcc,
        "follow_up_daily_limit": follow_up_daily_limit,
        "cold_outreach_enabled": cold_outreach_enabled,
        "cold_outreach_csv_path": cold_outreach_csv_path,
        "cold_outreach_daily_limit": cold_outreach_daily_limit,
        "cold_outreach_strategy": cold_outreach_strategy,
        "upsell_outreach_enabled": upsell_outreach_enabled,
        "upsell_outreach_daily_limit": upsell_outreach_daily_limit,
        "upsell_principal_csv_path": upsell_principal_csv_path,
        "upsell_exclude_principals": upsell_exclude_principals,
        "combined_system_prompt": combined_system_prompt,
        "llm_service": llm_service,
    }


def _do_follow_up(ctx: dict[str, Any]) -> None:
    """Execute the flagged-email follow-up logic using an already-initialised context."""
    client = ctx["client"]
    days_threshold = ctx["days_threshold"]
    follow_up_daily_limit = ctx["follow_up_daily_limit"]
    preferred_model = ctx["preferred_model"]
    salesforce_bcc = ctx["salesforce_bcc"]
    combined_system_prompt = ctx["combined_system_prompt"]
    llm_service = ctx["llm_service"]

    t_start = time.time()

    # 1. Scrape Flagged
    print("\n" + "=" * 30 + "\n")
    t_scrape = time.time()
    flagged_threads = run_scraper(mode="flagged")
    print(f"[Timer] Scraping: {time.time() - t_scrape:.1f}s")

    if flagged_threads:
        # 2. Filter
        t_filter = time.time()
        print("\n--- Processing Active Flags ---")
        candidates = filter_threads_for_replies(flagged_threads, days_threshold)
        print(f"[Timer] Filtering: {time.time() - t_filter:.1f}s")

        # 3. Apply daily limit
        if len(candidates) > follow_up_daily_limit:
            print(f"  -> Daily limit: processing {follow_up_daily_limit} of {len(candidates)} candidates.")
            candidates = candidates[:follow_up_daily_limit]

        # 4. Generate replies and create drafts
        t_replies = time.time()
        process_replies(
            candidates,
            client,
            combined_system_prompt,
            llm_service,
            preferred_model=preferred_model,
            salesforce_bcc=salesforce_bcc,
        )
        print(f"[Timer] Replies + drafts: {time.time() - t_replies:.1f}s")
    else:
        print("No flagged threads found.")

    print(f"\n[Timer] Follow-up total: {time.time() - t_start:.1f}s")


def _do_cold_outreach(ctx: dict[str, Any]) -> None:
    """Execute the cold outreach logic using an already-initialised context."""
    client = ctx["client"]
    preferred_model = ctx["preferred_model"]
    salesforce_bcc = ctx["salesforce_bcc"]
    llm_service = ctx["llm_service"]
    cold_outreach_enabled = ctx["cold_outreach_enabled"]
    cold_outreach_csv_path = ctx["cold_outreach_csv_path"]
    cold_outreach_daily_limit = ctx["cold_outreach_daily_limit"]
    cold_outreach_strategy = ctx["cold_outreach_strategy"]

    if not cold_outreach_enabled:
        print("Cold outreach is disabled in configuration. Skipping.")
        return

    try:
        cold_prompt = ""
        if os.path.exists(COLD_OUTREACH_PROMPT_PATH):
            with open(COLD_OUTREACH_PROMPT_PATH, "r") as f:
                cold_prompt = f.read()
        if not cold_prompt:
            print("Warning: Cold outreach prompt is empty. Skipping cold outreach.")
        else:
            process_cold_outreach(
                client=client,
                llm_service=llm_service,
                cold_prompt=cold_prompt,
                preferred_model=preferred_model,
                csv_path=cold_outreach_csv_path,
                daily_limit=cold_outreach_daily_limit,
                salesforce_bcc=salesforce_bcc,
                strategy=cold_outreach_strategy,
            )
    except Exception as e:
        print(f"Error during cold outreach: {e}")
        traceback.print_exc()


def _do_upsell_outreach(ctx: dict[str, Any]) -> None:
    """Execute the upsell outreach logic using an already-initialised context."""
    client = ctx["client"]
    preferred_model = ctx["preferred_model"]
    salesforce_bcc = ctx["salesforce_bcc"]
    llm_service = ctx["llm_service"]
    upsell_outreach_enabled = ctx["upsell_outreach_enabled"]
    upsell_outreach_daily_limit = ctx["upsell_outreach_daily_limit"]
    upsell_principal_csv_path = ctx["upsell_principal_csv_path"]
    upsell_exclude_principals = ctx["upsell_exclude_principals"]
    cold_outreach_csv_path = ctx["cold_outreach_csv_path"]

    if not upsell_outreach_enabled:
        print("Upsell outreach is disabled in configuration. Skipping.")
        return

    try:
        upsell_prompt = ""
        if os.path.exists(UPSELL_OUTREACH_PROMPT_PATH):
            with open(UPSELL_OUTREACH_PROMPT_PATH, "r") as f:
                upsell_prompt = f.read()
        if not upsell_prompt:
            print("Warning: Upsell outreach prompt is empty. Skipping upsell outreach.")
            return

        process_upsell_outreach(
            client=client,
            llm_service=llm_service,
            upsell_prompt=upsell_prompt,
            preferred_model=preferred_model,
            salesforce_csv_path=cold_outreach_csv_path,
            principal_csv_path=upsell_principal_csv_path,
            daily_limit=upsell_outreach_daily_limit,
            salesforce_bcc=salesforce_bcc,
            exclude_principals=upsell_exclude_principals,
        )
    except Exception as e:
        print(f"Error during upsell outreach: {e}")
        traceback.print_exc()


def run_follow_up() -> None:
    """Run only the flagged-email follow-up step (scrape, reply, summarise)."""
    print("--- Outlook Bot: Follow Up ---")
    try:
        ctx = _setup()
        if ctx is None:
            return
        _do_follow_up(ctx)
    except Exception as e:
        print(f"Error during execution: {e}")
        traceback.print_exc()


def run_cold_outreach() -> None:
    """Run only the cold outreach step."""
    print("--- Outlook Bot: Cold Outreach ---")
    try:
        ctx = _setup()
        if ctx is None:
            return
        _do_cold_outreach(ctx)
    except Exception as e:
        print(f"Error during execution: {e}")
        traceback.print_exc()


def run_upsell_outreach() -> None:
    """Run only the upsell outreach step."""
    print("--- Outlook Bot: Upsell Outreach ---")
    try:
        ctx = _setup()
        if ctx is None:
            return
        _do_upsell_outreach(ctx)
    except Exception as e:
        print(f"Error during execution: {e}")
        traceback.print_exc()


def run_test_prompt(email_file: str) -> None:
    """Load a .txt email, generate a reply with the LLM, and create an Outlook draft."""
    print("--- Outlook Bot: Test Prompt ---")
    try:
        if not email_file or not os.path.exists(email_file):
            print(f"[Error] Email file not found: {email_file}")
            return

        with open(email_file, "r", encoding="utf-8") as f:
            email_content = f.read()

        if not email_content.strip():
            print("[Error] Email file is empty.")
            return

        print(f"Loaded email from: {email_file}")
        print(f"Content length: {len(email_content)} chars")

        ctx = _setup()
        if ctx is None:
            return

        llm_service = ctx["llm_service"]
        preferred_model = ctx["preferred_model"]
        combined_system_prompt = ctx["combined_system_prompt"]
        client = ctx["client"]

        # Generate reply via LLM
        print("\nGenerating reply with LLM...")
        reply_text = llm_service.generate_reply(email_content, combined_system_prompt, preferred_model=preferred_model)

        if not reply_text:
            print("[Error] LLM returned no reply.")
            return

        print("\n" + "#" * 30)
        print("GENERATED REPLY:")
        print("#" * 30)
        print(reply_text)
        print("#" * 30)

        # Create draft in Outlook
        subject = "Re: Test Prompt"
        # Try to extract subject from email content
        for line in email_content.splitlines():
            if line.startswith("Subject: "):
                subject = "Re: " + line[9:].strip()
                break

        formatted_reply = reply_text.replace("\n", "<br>")
        client.create_draft("", subject, formatted_reply)
        print("\n[Success] Draft created in Outlook.")

        # Generate and print SF Note
        print("\nGenerating SF Note...")
        sf_note = llm_service.generate_sf_note(email_content, preferred_model=preferred_model)
        if sf_note:
            print(f"\n📋 SF Note:\n   {sf_note}\n")
        else:
            print("[Warning] Failed to generate SF Note.")

    except Exception as e:
        print(f"Error during execution: {e}")
        traceback.print_exc()


def main() -> None:
    """Run follow-up, cold outreach, and upsell outreach."""
    print("--- Outlook Bot: Run All ---")
    try:
        ctx = _setup()
        if ctx is None:
            return
        _do_follow_up(ctx)
        _do_cold_outreach(ctx)
        _do_upsell_outreach(ctx)
    except Exception as e:
        print(f"Error during execution: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--follow-up", action="store_true")
    group.add_argument("--cold-outreach", action="store_true")
    group.add_argument("--upsell-outreach", action="store_true")
    group.add_argument("--run-all", action="store_true")
    group.add_argument("--test-prompt", type=str, metavar="FILE", help="Test prompt with a .txt email file")
    args = parser.parse_args()

    if args.follow_up:
        run_follow_up()
    elif args.cold_outreach:
        run_cold_outreach()
    elif args.upsell_outreach:
        run_upsell_outreach()
    elif args.test_prompt:
        run_test_prompt(args.test_prompt)
    else:
        main()
