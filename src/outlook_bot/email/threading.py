"""Email threading - group messages into conversation threads."""

from __future__ import annotations

from outlook_bot.core.models import Email, Thread


def group_into_threads(emails: list[Email]) -> list[Thread]:
    """Group emails by their conversation ID into Thread objects."""
    threads_map: dict[str, list[Email]] = {}

    for email in emails:
        thread_id = email.id
        if not thread_id:
            continue
        threads_map.setdefault(thread_id, []).append(email)

    return [Thread(emails=msgs) for msgs in threads_map.values()]
