"""Abstract email client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from outlook_bot.core.models import Thread


class EmailClient(ABC):
    """Abstract interface for email client operations."""

    @abstractmethod
    def activate(self) -> None:
        """Bring the email client to the foreground."""

    @abstractmethod
    def get_version(self) -> str | None:
        """Get the email client version."""

    @abstractmethod
    def scrape_flagged_threads(self) -> list[Thread]:
        """Retrieve all flagged email threads."""

    @abstractmethod
    def scrape_recent_threads(self) -> list[Thread]:
        """Retrieve recent email threads."""

    @abstractmethod
    def create_draft(self, to_address: str, subject: str, content: str, bcc_address: str = "") -> str | None:
        """Create a new draft email."""

    @abstractmethod
    def reply_to_message(self, message_id: str, content: str, bcc_address: str = "") -> str | None:
        """Reply to a message by ID."""

    @abstractmethod
    def get_sent_recipients(self) -> set[str]:
        """Get all recipients from Sent Items."""
