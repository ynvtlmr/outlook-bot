"""Follow-up reply workflow: scrape flagged threads, generate replies, create drafts."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from outlook_bot.utils.dates import get_latest_date

if TYPE_CHECKING:
    from outlook_bot.core.models import Thread
    from outlook_bot.email.client import EmailClient
    from outlook_bot.providers.registry import ProviderRegistry


def filter_threads_for_replies(threads: list[Thread], days_threshold: int) -> list[dict[str, Any]]:
    """Identify threads that need a reply based on flag status and activity date.

    Returns a list of dicts with keys: thread, target_email, subject.
    """
    candidates = []

    for i, thread in enumerate(threads):
        if not thread.has_active_flag:
            continue

        subject = thread.subject
        print(f"\nAnalyzing Thread {i + 1}: {subject}")

        # Find the latest activity date from headers and body content
        all_dates: list[datetime] = []
        for email in thread.emails:
            if email.has_valid_timestamp:
                all_dates.append(email.timestamp)  # type: ignore[arg-type]
            buried_date = get_latest_date(email.content)
            if buried_date:
                all_dates.append(buried_date)

        if not all_dates:
            print("  -> Warning: Could not determine any activity date. Skipping.")
            continue

        latest_activity = max(all_dates)
        days_ago = (datetime.now() - latest_activity).days

        print(f"  -> Latest activity: {latest_activity.strftime('%Y-%m-%d %H:%M:%S')} ({days_ago} days ago)")

        if days_ago <= days_threshold:
            print(f"  -> Activity within {days_threshold} days. No reply needed yet.")
            continue

        print(f"  -> No activity for > {days_threshold} days. Proceeding with draft.")

        target_email = thread.latest_email
        if target_email:
            candidates.append({"thread": thread, "target_email": target_email, "subject": subject})

    return candidates


def process_replies(
    candidates: list[dict[str, Any]],
    client: EmailClient,
    system_prompt: str,
    registry: ProviderRegistry,
    preferred_model: str | None = None,
    salesforce_bcc: str = "",
) -> None:
    """Generate replies for candidates and create drafts in the email client."""
    if not candidates:
        print("  -> No active threads requiring replies found.")
        return

    batch_jobs = []
    for item in candidates:
        target = item["target_email"]
        msg_id = target.message_id
        if not msg_id:
            print(f"  -> Error: No Message ID for target in '{item['subject']}'.")
            continue
        batch_jobs.append({"id": msg_id, "subject": item["subject"], "content": target.content})

    if not batch_jobs:
        return

    print(f"\nProcessing batch of {len(batch_jobs)} emails with LLM Service...")
    batch_replies = registry.generate_batch_replies(batch_jobs, system_prompt, preferred_model=preferred_model)
    print(f"Received {len(batch_replies)} replies from LLM Service.")

    for job in batch_jobs:
        msg_id = job["id"]
        subject = job["subject"]
        reply_text = batch_replies.get(msg_id)

        if reply_text:
            _create_draft_reply(client, msg_id, subject, reply_text, salesforce_bcc)
        else:
            print(f"  -> Warning: No reply generated for '{subject}' (ID: {msg_id})")


def _create_draft_reply(client: EmailClient, msg_id: str, subject: str, reply_text: str, bcc_address: str = "") -> None:
    """Create the actual draft reply in the email client."""
    print(f"\nCreating draft for: {subject}")
    print("#" * 30)
    print(f"REPLY: {reply_text[:100]}...")
    print("#" * 30)

    try:
        formatted_reply = reply_text.replace("\n", "<br>")
        result = client.reply_to_message(msg_id, formatted_reply, bcc_address)
        print(f"  -> {result}")
    except Exception as e:
        print(f"  -> Failed to create draft: {e}")


def run_follow_up(
    client: EmailClient,
    registry: ProviderRegistry,
    system_prompt: str,
    days_threshold: int,
    preferred_model: str | None = None,
    salesforce_bcc: str = "",
) -> None:
    """Execute the complete follow-up workflow."""
    from outlook_bot.workflows.summarize import generate_thread_summaries

    print("\n" + "=" * 30 + "\n")
    flagged_threads = client.scrape_flagged_threads()

    if not flagged_threads:
        print("No flagged threads found.")
        return

    print("\n--- Processing Active Flags ---")
    candidates = filter_threads_for_replies(flagged_threads, days_threshold)
    process_replies(candidates, client, system_prompt, registry, preferred_model, salesforce_bcc)

    # Generate summaries for threads that need replies
    print("\n" + "=" * 30 + "\n")
    reply_threads = [item["thread"] for item in candidates]
    if reply_threads:
        generate_thread_summaries(reply_threads, registry, preferred_model)
