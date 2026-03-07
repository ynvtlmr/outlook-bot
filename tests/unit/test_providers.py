"""Tests for the LLM provider layer."""

import json
from unittest.mock import MagicMock, patch

from outlook_bot.providers.base import ModelInfo
from outlook_bot.providers.registry import ProviderRegistry, _extract_json


class TestExtractJson:
    def test_plain_json(self):
        assert _extract_json('{"key": "value"}') == {"key": "value"}

    def test_markdown_fenced(self):
        assert _extract_json('```json\n{"key": "value"}\n```') == {"key": "value"}

    def test_triple_backtick_only(self):
        assert _extract_json('```\n{"key": "value"}\n```') == {"key": "value"}

    def test_json_list(self):
        result = _extract_json('[{"id": "1", "reply_text": "hello"}]')
        assert isinstance(result, list)


class TestProviderRegistry:
    @patch("outlook_bot.providers.registry.CredentialManager")
    @patch("outlook_bot.providers.registry.get_ssl_verify_option", return_value="dummy")
    def test_init_no_keys(self, mock_ssl, mock_cred):
        mock_cred.get_gemini_key.return_value = None
        mock_cred.get_openai_key.return_value = None
        mock_cred.get_openrouter_key.return_value = None

        registry = ProviderRegistry()
        assert len(registry.providers) == 0
        assert len(registry.available_models) == 0

    @patch("outlook_bot.providers.registry.CredentialManager")
    @patch("outlook_bot.providers.registry.get_ssl_verify_option", return_value="dummy")
    def test_ordered_models_preferred(self, mock_ssl, mock_cred):
        mock_cred.get_gemini_key.return_value = None
        mock_cred.get_openai_key.return_value = None
        mock_cred.get_openrouter_key.return_value = None

        registry = ProviderRegistry()
        registry.available_models = [
            ModelInfo(id="model-a", provider="gemini"),
            ModelInfo(id="model-b", provider="openai"),
        ]

        ordered = registry._ordered_models("model-b")
        assert ordered[0].id == "model-b"

    @patch("outlook_bot.providers.registry.CredentialManager")
    @patch("outlook_bot.providers.registry.get_ssl_verify_option", return_value="dummy")
    def test_ordered_models_not_found(self, mock_ssl, mock_cred):
        mock_cred.get_gemini_key.return_value = None
        mock_cred.get_openai_key.return_value = None
        mock_cred.get_openrouter_key.return_value = None

        registry = ProviderRegistry()
        registry.available_models = [ModelInfo(id="model-a", provider="gemini")]

        ordered = registry._ordered_models("nonexistent")
        assert ordered[0].id == "model-a"

    @patch("outlook_bot.providers.registry.CredentialManager")
    @patch("outlook_bot.providers.registry.get_ssl_verify_option", return_value="dummy")
    def test_generate_reply_no_models(self, mock_ssl, mock_cred):
        mock_cred.get_gemini_key.return_value = None
        mock_cred.get_openai_key.return_value = None
        mock_cred.get_openrouter_key.return_value = None

        registry = ProviderRegistry()
        result = registry.generate_reply("body", "prompt")
        assert result is None

    @patch("outlook_bot.providers.registry.CredentialManager")
    @patch("outlook_bot.providers.registry.get_ssl_verify_option", return_value="dummy")
    def test_generate_reply_with_fallback(self, mock_ssl, mock_cred):
        mock_cred.get_gemini_key.return_value = None
        mock_cred.get_openai_key.return_value = None
        mock_cred.get_openrouter_key.return_value = None

        registry = ProviderRegistry(max_retries=0)
        registry.available_models = [
            ModelInfo(id="model-fail", provider="gemini"),
            ModelInfo(id="model-ok", provider="openai"),
        ]

        mock_gemini = MagicMock()
        mock_gemini.generate.side_effect = Exception("fail")
        mock_openai = MagicMock()
        mock_openai.generate.return_value = "Success reply"

        registry.providers = {"gemini": mock_gemini, "openai": mock_openai}

        result = registry.generate_reply("body", "prompt")
        assert result == "Success reply"

    def test_parse_batch_response_list(self):
        parsed = [{"id": "1", "reply_text": "hello"}, {"id": "2", "reply_text": "world"}]
        result = ProviderRegistry._parse_batch_response(parsed)
        assert result == {"1": "hello", "2": "world"}

    def test_parse_batch_response_dict_wrapped(self):
        parsed = {"replies": [{"id": "1", "reply_text": "hello"}]}
        result = ProviderRegistry._parse_batch_response(parsed)
        assert result == {"1": "hello"}

    def test_parse_batch_response_invalid(self):
        assert ProviderRegistry._parse_batch_response("not json") == {}

    @patch("outlook_bot.providers.registry.CredentialManager")
    @patch("outlook_bot.providers.registry.get_ssl_verify_option", return_value="dummy")
    def test_generate_batch_replies(self, mock_ssl, mock_cred):
        mock_cred.get_gemini_key.return_value = None
        mock_cred.get_openai_key.return_value = None
        mock_cred.get_openrouter_key.return_value = None

        registry = ProviderRegistry(max_retries=0)
        registry.available_models = [ModelInfo(id="test-model", provider="gemini")]

        mock_provider = MagicMock()
        mock_provider.generate_json.return_value = json.dumps(
            [
                {"id": "msg1", "reply_text": "Reply 1"},
            ]
        )
        registry.providers = {"gemini": mock_provider}

        batch = [{"id": "msg1", "subject": "Test", "content": "Hi"}]
        result = registry.generate_batch_replies(batch, "system prompt")
        assert result == {"msg1": "Reply 1"}
