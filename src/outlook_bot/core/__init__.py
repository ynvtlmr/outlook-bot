"""Core data models and configuration."""

from outlook_bot.core.config import Config, CredentialManager, Paths
from outlook_bot.core.exceptions import (
    ConfigError,
    EmailClientError,
    LLMError,
    OutlookBotError,
    OutlookNotRunningError,
    ProviderError,
)
from outlook_bot.core.models import Draft, Email, Lead, Thread, ThreadSummary

__all__ = [
    "Config",
    "ConfigError",
    "CredentialManager",
    "Draft",
    "Email",
    "EmailClientError",
    "LLMError",
    "Lead",
    "OutlookBotError",
    "OutlookNotRunningError",
    "Paths",
    "ProviderError",
    "Thread",
    "ThreadSummary",
]
