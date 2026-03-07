"""Text processing utilities for email content."""

from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from outlook_bot.core.models import Thread

# Subject normalization pattern - single source of truth
_REPLY_PREFIX_RE = re.compile(r"^(RE|FWD|FW):\s*", flags=re.IGNORECASE)

# Gen II footer pattern for token-saving removal
_GEN_II_FOOTER_RE = re.compile(
    r"NOTICE:\s*Unless otherwise stated.*?which can be found here\.",
    re.IGNORECASE | re.DOTALL,
)
_GEN_II_FOOTER_START_RE = re.compile(r"NOTICE:\s*Unless otherwise stated", re.IGNORECASE)


def normalize_subject(subject: str) -> str:
    """Remove Re:/Fwd:/FW: prefixes and strip whitespace."""
    return _REPLY_PREFIX_RE.sub("", subject).strip()


def is_gen_ii_email(address: str) -> bool:
    """Check if an email address or name belongs to Gen II."""
    if not address:
        return False
    lower = address.lower()
    return "@gen2fund.com" in lower or "gen ii" in lower or "gen2" in lower


def extract_client_name_from_subject(subject: str) -> str:
    """Extract a client name from the subject line using pattern matching."""
    if not subject:
        return "Unknown Client"

    subject_clean = normalize_subject(subject)

    # Pattern: "between X and Y"
    match = re.search(r"between\s+([^<>]+?)\s+and", subject_clean, re.IGNORECASE)
    if match:
        candidate = match.group(1).strip()
        if not is_gen_ii_email(candidate):
            return candidate

    # Pattern: "Client Name:"
    match = re.search(r"^([^:<>]+?):", subject_clean)
    if match:
        candidate = match.group(1).strip()
        if not is_gen_ii_email(candidate):
            return candidate

    # Pattern: "Client Name -" or "Client Name =>"
    match = re.search(r"^([^<>-]+?)\s*[-=](?:>|\s|$)", subject_clean)
    if match:
        candidate = match.group(1).strip()
        if not is_gen_ii_email(candidate):
            return candidate

    # Fallback: first part before any separator
    parts = re.split(r"[-=<>:]", subject_clean, maxsplit=1)
    if parts and parts[0].strip():
        candidate = parts[0].strip()
        if not is_gen_ii_email(candidate):
            return candidate

    return subject_clean[:50] if subject_clean else "Unknown Client"


def extract_client_name(thread: Thread) -> str:
    """Extract client name from thread, preferring sender info over subject patterns."""
    if not thread.emails:
        return "Unknown Client"

    client_candidates: list[str] = []
    for email in thread.emails:
        if not email.sender:
            continue

        email_match = re.search(r"<([^>]+)>", email.sender)
        addr = email_match.group(1) if email_match else email.sender

        name_match = re.search(r"^([^<]+)", email.sender)
        name = name_match.group(1).strip() if name_match else ""

        if is_gen_ii_email(addr) or is_gen_ii_email(name):
            continue

        if name:
            client_candidates.append(name)
        elif "@" in addr:
            domain = addr.split("@")[1]
            if "gen2fund.com" not in domain.lower():
                client_candidates.append(domain.split(".")[0].title())

    if client_candidates:
        counter = Counter(client_candidates)
        return counter.most_common(1)[0][0]

    return extract_client_name_from_subject(thread.subject)


def strip_gen_ii_footer(content: str) -> str:
    """Remove the Gen II legal footer from email content to save LLM tokens."""
    if not content:
        return content

    cleaned = _GEN_II_FOOTER_RE.sub("", content)

    match = _GEN_II_FOOTER_START_RE.search(cleaned)
    if match:
        marker_pos = match.start()
        if marker_pos > len(cleaned) * 0.7:
            cleaned = cleaned[:marker_pos].rstrip()

    return cleaned


def format_thread_content(thread: Thread) -> str:
    """Format a thread into a readable string for LLM processing."""
    lines: list[str] = []

    for i, email in enumerate(thread.sorted_chronologically(), 1):
        lines.append(f"\n--- Message {i} ---")
        lines.append(f"From: {email.sender or 'Unknown'}")
        lines.append(f"Date: {email.date_str or 'Unknown'}")
        lines.append(f"Subject: {email.subject}")
        if email.flag_status:
            lines.append(f"Flag Status: {email.flag_status}")
        lines.append("\nContent:")
        lines.append(strip_gen_ii_footer(email.content))
        lines.append("\n" + "=" * 80)

    return "\n".join(lines)
