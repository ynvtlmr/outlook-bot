"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ssl


@dataclass
class ModelInfo:
    """Information about an available LLM model."""

    id: str
    provider: str


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    name: str = "base"

    @abstractmethod
    def initialize(self, api_key: str, ssl_verify: ssl.SSLContext | str) -> None:
        """Initialize the provider client."""

    @abstractmethod
    def discover_models(self) -> list[ModelInfo]:
        """Discover available models from this provider."""

    @abstractmethod
    def generate(self, model_id: str, prompt: str) -> str:
        """Generate a text response."""

    @abstractmethod
    def generate_json(self, model_id: str, prompt: str) -> str:
        """Generate a JSON response."""

    @abstractmethod
    def test_connection(self, api_key: str, ssl_verify: ssl.SSLContext | str) -> tuple[bool, str]:
        """Test connectivity. Returns (success, message)."""
