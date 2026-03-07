"""Integration tests for LLM service (requires API keys)."""

import os

import pytest

from outlook_bot.providers.registry import ProviderRegistry


@pytest.mark.integration
class TestLLMServiceIntegration:
    @pytest.fixture(autouse=True)
    def _check_keys(self):
        has_any_key = any(
            [
                os.getenv("GEMINI_API_KEY"),
                os.getenv("OPENAI_API_KEY"),
                os.getenv("OPENROUTER_API_KEY"),
            ]
        )
        if not has_any_key:
            pytest.skip("No API keys available for integration tests")

    def test_registry_init(self):
        registry = ProviderRegistry()
        assert len(registry.available_models) > 0

    def test_generate_reply(self):
        registry = ProviderRegistry()
        result = registry.generate_reply("Hello, how are you?", "Reply briefly.")
        assert result is not None
        assert len(result) > 0
