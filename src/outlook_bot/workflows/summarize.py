"""Thread summarization workflow: generate summaries and Word documents."""

from __future__ import annotations

import os
from datetime import datetime
from typing import TYPE_CHECKING

from outlook_bot.core.config import Paths
from outlook_bot.core.models import Thread, ThreadSummary
from outlook_bot.utils.documents import create_summary_document
from outlook_bot.utils.text import extract_client_name, format_thread_content

if TYPE_CHECKING:
    from outlook_bot.providers.registry import ProviderRegistry


def generate_thread_summaries(
    threads: list[Thread],
    registry: ProviderRegistry,
    preferred_model: str | None = None,
    paths: Paths | None = None,
) -> None:
    """Generate summaries and SF Notes for threads and create a Word document."""
    if not threads:
        print("No flagged threads to summarize.")
        return

    print(f"\n--- Generating Summaries for {len(threads)} Flagged Threads ---")

    summaries: list[ThreadSummary] = []

    for idx, thread in enumerate(threads, 1):
        if not thread.emails:
            print(f"\nSkipping Thread {idx}/{len(threads)}: Empty thread")
            continue

        subject = thread.subject
        print(f"\nProcessing Thread {idx}/{len(threads)}: {subject}")

        client_name = extract_client_name(thread)
        print(f"  -> Client: {client_name}")

        thread_content = format_thread_content(thread)

        print("  -> Generating summary...")
        summary = registry.generate_thread_summary(thread_content, preferred_model=preferred_model)

        print("  -> Generating SF Note...")
        sf_note = registry.generate_sf_note(thread_content, preferred_model=preferred_model)

        if summary:
            summaries.append(
                ThreadSummary(
                    subject=subject,
                    client_name=client_name,
                    summary=summary,
                    sf_note=sf_note or "SF Note generation failed.",
                    thread=thread,
                )
            )
            print("  -> Summary generated successfully")
            if sf_note:
                print("  -> SF Note generated successfully")
            else:
                print(f"  -> Warning: Failed to generate SF Note for '{subject}'")
        else:
            print(f"  -> Warning: Failed to generate summary for '{subject}'")

    if not summaries:
        print("No summaries generated. Skipping document creation.")
        return

    if paths is None:
        paths = Paths()

    paths.ensure_output_dir()
    date_str = datetime.now().strftime("%m-%d-%Y")
    output_path = os.path.join(str(paths.output_dir), f"email_summary_{date_str}.docx")

    print("\n--- Creating Word Document ---")
    result = create_summary_document(summaries, output_path)

    if result:
        print(f"Word document created: {output_path}")
    else:
        print("Failed to create Word document.")
