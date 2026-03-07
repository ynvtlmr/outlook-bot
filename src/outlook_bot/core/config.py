"""Configuration management for Outlook Bot."""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Environment variable names
ENV_GEMINI_API_KEY = "GEMINI_API_KEY"
ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
ENV_OPENROUTER_API_KEY = "OPENROUTER_API_KEY"

# Parsing delimiters (must match AppleScript output format)
MSG_DELIMITER = "\n///END_OF_MESSAGE///\n"
BODY_START = "---BODY_START---"
BODY_END = "---BODY_END---"


class Paths:
    """Centralized path management with support for PyInstaller bundling."""

    def __init__(self) -> None:
        if getattr(sys, "frozen", False):
            self.resource_dir = Path(getattr(sys, "_MEIPASS", ".")).resolve()
            self.user_data_dir = Path.home() / "Documents" / "OutlookBot"
        else:
            self.resource_dir = Path(__file__).resolve().parent.parent.parent.parent
            self.user_data_dir = self.resource_dir

        self.user_data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def config_path(self) -> Path:
        return self.user_data_dir / "config.yaml"

    @property
    def env_path(self) -> Path:
        return self.user_data_dir / ".env"

    @property
    def system_prompt_path(self) -> Path:
        return self.user_data_dir / "system_prompt.txt"

    @property
    def system_prompt_example_path(self) -> Path:
        return self.resource_dir / "system_prompt.example.txt"

    @property
    def cold_outreach_prompt_path(self) -> Path:
        return self.user_data_dir / "cold_outreach_prompt.txt"

    @property
    def cold_outreach_prompt_example_path(self) -> Path:
        return self.resource_dir / "cold_outreach_prompt.example.txt"

    @property
    def output_dir(self) -> Path:
        return self.user_data_dir / "output"

    @property
    def applescripts_dir(self) -> Path:
        return self.resource_dir / "src" / "apple_scripts"

    def ensure_defaults(self) -> None:
        """Copy example files to user directory if they don't exist yet."""
        pairs = [
            (self.system_prompt_example_path, self.system_prompt_path),
            (self.cold_outreach_prompt_example_path, self.cold_outreach_prompt_path),
        ]
        for source, dest in pairs:
            if not dest.exists() and source.exists():
                try:
                    shutil.copy2(source, dest)
                except OSError as e:
                    print(f"Warning: Could not create default {dest.name}: {e}")

    def ensure_output_dir(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)


class CredentialManager:
    """Central accessor for API keys from environment variables."""

    @staticmethod
    def get_gemini_key() -> str | None:
        return os.getenv(ENV_GEMINI_API_KEY)

    @staticmethod
    def get_openai_key() -> str | None:
        return os.getenv(ENV_OPENAI_API_KEY)

    @staticmethod
    def get_openrouter_key() -> str | None:
        return os.getenv(ENV_OPENROUTER_API_KEY)


@dataclass
class Config:
    """Application configuration loaded from config.yaml."""

    days_threshold: int = 5
    default_reply: str = "Thank you for your email. I will review it and get back to you shortly."
    preferred_model: str | None = None
    salesforce_bcc: str = ""
    cold_outreach_enabled: bool = False
    cold_outreach_csv_path: str = ""
    cold_outreach_daily_limit: int = 10
    ssl_mode: str = "disabled"  # "disabled", "auto", "custom_bundle"
    _extra: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def load(cls, paths: Paths) -> Config:
        """Load configuration from YAML file and environment."""
        load_dotenv(paths.env_path)
        paths.ensure_defaults()

        data: dict[str, Any] = {}
        if paths.config_path.exists():
            try:
                with open(paths.config_path) as f:
                    data = yaml.safe_load(f) or {}
            except (yaml.YAMLError, OSError) as e:
                print(f"Warning: Error loading config.yaml: {e}")

        known_keys = {
            "days_threshold",
            "default_reply",
            "preferred_model",
            "salesforce_bcc",
            "cold_outreach_enabled",
            "cold_outreach_csv_path",
            "cold_outreach_daily_limit",
            "ssl_mode",
        }
        extra = {k: v for k, v in data.items() if k not in known_keys}

        return cls(
            days_threshold=data.get("days_threshold", 5),
            default_reply=data.get("default_reply", cls.default_reply),
            preferred_model=data.get("preferred_model"),
            salesforce_bcc=data.get("salesforce_bcc", ""),
            cold_outreach_enabled=data.get("cold_outreach_enabled", False),
            cold_outreach_csv_path=data.get("cold_outreach_csv_path", ""),
            cold_outreach_daily_limit=data.get("cold_outreach_daily_limit", 10),
            ssl_mode=data.get("ssl_mode", "disabled"),
            _extra=extra,
        )

    def save(self, paths: Paths) -> None:
        """Save configuration to YAML file, preserving unknown keys."""
        data = {
            **self._extra,
            "days_threshold": self.days_threshold,
            "default_reply": self.default_reply,
            "preferred_model": self.preferred_model,
            "salesforce_bcc": self.salesforce_bcc,
            "cold_outreach_enabled": self.cold_outreach_enabled,
            "cold_outreach_csv_path": self.cold_outreach_csv_path,
            "cold_outreach_daily_limit": self.cold_outreach_daily_limit,
            "ssl_mode": self.ssl_mode,
        }
        with open(paths.config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
