
import os
import re
import time
import traceback
from collections import Counter
from datetime import datetime
from typing import Any

import llm
from config import APPLESCRIPTS_DIR, DAYS_THRESHOLD, OUTPUT_DIR, PREFERRED_MODEL, SYSTEM_PROMPT_PATH
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


def filter_threads_for_replies(threads: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
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


def process_replies(
    candidates: list[dict[str, Any]],
    client: OutlookClient,
    system_prompt: str,
    llm_service: llm.LLMService,
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


def create_draft_reply(client: OutlookClient, msg_id: str, subject: str, reply_text: str) -> None:
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

        result = client.reply_to_message(msg_id, formatted_reply)
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


def generate_thread_summaries(flagged_threads: list[list[dict[str, Any]]], llm_service: llm.LLMService) -> None:
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
        print(f"  -> Generating summary...")
        summary = llm_service.generate_thread_summary(thread_content, preferred_model=PREFERRED_MODEL)
        
        # Generate SF Note
        print(f"  -> Generating SF Note...")
        sf_note = llm_service.generate_sf_note(thread_content, preferred_model=PREFERRED_MODEL)
        
        if summary:
            threads_with_summaries.append({
                'subject': subject,
                'client_name': client_name,
                'summary': summary,
                'sf_note': sf_note if sf_note else "SF Note generation failed.",
                'thread': thread
            })
            print(f"  -> Summary generated successfully")
            if sf_note:
                print(f"  -> SF Note generated successfully")
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
        
        print(f"\n--- Creating Word Document ---")
        result = create_summary_document(threads_with_summaries, output_path)
        
        if result:
            print(f"✓ Word document created: {output_path}")
        else:
            print(f"✗ Failed to create Word document.")
    else:
        print("No summaries generated. Skipping document creation.")


def main() -> None:
    print("--- Outlook Bot Generic Scraper ---")

    try:
        # 0. Initialize Client and Focus Outlook
        client = OutlookClient(APPLESCRIPTS_DIR)
        print("Launching/Focusing Outlook...")
        client.activate_outlook()
        
        # 0.5 Wait for Outlook to load
        if not wait_for_outlook_ready():
            return

        # 1. Scrape Flagged
        print("\n" + "=" * 30 + "\n")
        flagged_threads = run_scraper(mode="flagged")

        if not flagged_threads:
            print("No flagged threads found.")
            return

        # 2. Process Active Flags
        print("\n--- Processing Active Flags ---")
        # client already initialized
        
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
        
        # Generate summaries for all flagged threads
        print("\n" + "=" * 30 + "\n")
        generate_thread_summaries(flagged_threads, llm_service)

    except Exception as e:
        print(f"Error during execution: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
