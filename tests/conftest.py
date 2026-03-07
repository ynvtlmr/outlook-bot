"""Shared fixtures for Outlook Bot tests."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from outlook_bot.core.models import Email, Thread


@pytest.fixture
def mock_raw_applescript_output() -> str:
    """Sample string mimicking get_flagged_threads.scpt output."""
    return """ID: 101
From: sender@example.com
Date: Thursday, December 18, 2025 at 12:45:49 PM
Subject: Re: Project Update
FlagStatus: Active
MessageID: <123@example.com>
---BODY_START---
This is the email body.
It has multiple lines.
---BODY_END---
///END_OF_MESSAGE///
ID: 102
From: boss@example.com
Date: Friday, December 19, 2025 at 09:00:00 AM
Subject: Urgent meeting
FlagStatus: Active
MessageID: <456@example.com>
---BODY_START---
Please reply asap.
---BODY_END---
///END_OF_MESSAGE///
"""


@pytest.fixture
def sample_emails() -> list[Email]:
    """Pre-built list of Email objects for testing."""
    now = datetime.now()
    return [
        Email(
            id="1",
            subject="Active Recent",
            sender="client@example.com",
            flag_status="Active",
            timestamp=now - timedelta(days=1),
            content="Recent message",
            message_id="msg1",
        ),
        Email(
            id="2",
            subject="Active Old",
            sender="client@example.com",
            flag_status="Active",
            timestamp=now - timedelta(days=20),
            content="Old message",
            message_id="msg2",
        ),
        Email(
            id="3",
            subject="Completed",
            sender="client@example.com",
            flag_status="Completed",
            timestamp=now - timedelta(days=1),
            content="Done",
            message_id="msg3",
        ),
    ]


@pytest.fixture
def sample_threads(sample_emails: list[Email]) -> list[Thread]:
    """Pre-built list of Thread objects for testing."""
    return [
        Thread(emails=[sample_emails[0]]),  # Active, recent
        Thread(emails=[sample_emails[1]]),  # Active, old
        Thread(emails=[sample_emails[2]]),  # Completed
    ]


@pytest.fixture
def active_old_thread() -> Thread:
    """A single thread with an active flag and old timestamp."""
    return Thread(
        emails=[
            Email(
                id="old-thread",
                subject="Old Active Thread",
                sender="client@example.com",
                flag_status="Active",
                timestamp=datetime.now() - timedelta(days=20),
                content="Old message body",
                message_id="msg-old",
            ),
        ]
    )
