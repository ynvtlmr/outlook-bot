"""Custom exceptions for the Outlook Bot application."""


class OutlookBotError(Exception):
    """Base exception for all Outlook Bot errors."""


class ConfigError(OutlookBotError):
    """Raised when configuration is invalid or missing."""


class LLMError(OutlookBotError):
    """Raised when LLM operations fail."""


class ProviderError(LLMError):
    """Raised when a specific LLM provider fails."""

    def __init__(self, provider: str, model: str, message: str) -> None:
        self.provider = provider
        self.model = model
        super().__init__(f"[{provider}:{model}] {message}")


class EmailClientError(OutlookBotError):
    """Raised when email client operations fail."""


class OutlookNotRunningError(EmailClientError):
    """Raised when Outlook is not running or not responsive."""
