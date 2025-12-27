import json
import os
import unittest
from typing import Any, cast
from unittest.mock import MagicMock, patch

import llm


class TestLLMService(unittest.TestCase):
    def setUp(self):
        # Mock env vars and CredentialManager before initializing LLMService
        self.env_patcher = patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "fake_gemini_key",
                "OPENAI_API_KEY": "fake_openai_key",
                "OPENROUTER_API_KEY": "fake_or_key",
            },
        )
        self.env_patcher.start()

        # Mock credential manager to return these keys
        self.cred_patcher = patch("llm.CredentialManager")
        self.mock_cred_mgr = self.cred_patcher.start()
        self.mock_cred_mgr.get_gemini_key.return_value = "fake_gemini_key"
        self.mock_cred_mgr.get_openai_key.return_value = "fake_openai_key"
        self.mock_cred_mgr.get_openrouter_key.return_value = "fake_or_key"

        # Mock SSL utils to avoid real network/file ops during init
        self.ssl_patcher = patch("llm.setup_ssl_environment")
        self.ssl_patcher.start()
        self.get_ssl_patcher = patch("llm.get_ssl_verify_option", return_value="dummy_cert_path")
        self.get_ssl_patcher.start()

        # Mock Clients
        self.genai_patcher = patch("llm.genai.Client")
        self.mock_genai_client_cls = self.genai_patcher.start()
        self.mock_gemini_client = self.mock_genai_client_cls.return_value

        self.openai_patcher = patch("llm.OpenAI")
        self.mock_openai_client_cls = self.openai_patcher.start()
        # Return distinct mocks for each instantiation (OpenAI vs OpenRouter)
        self.mock_openai_client_cls.side_effect = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        # We might need more depending on how many times it's called.
        # Typically initialized twice in __init__ (OpenAI, OpenRouter).
        # But setup_ssl might trigger things too if we aren't careful?
        # Let's just use side_effect to return unique mocks.
        self.mock_openai_client_cls.side_effect = lambda **kwargs: MagicMock()

    def tearDown(self):
        self.env_patcher.stop()
        self.cred_patcher.stop()
        self.ssl_patcher.stop()
        self.get_ssl_patcher.stop()
        self.genai_patcher.stop()
        self.openai_patcher.stop()

    def test_init_clients(self):
        """Test that clients are initialized with keys."""
        service = llm.LLMService()
        assert service.gemini_client is not None
        assert service.openai_client is not None
        assert service.openrouter_client is not None

    def test_discover_models_filtering(self):
        """Test user-defined filtering logic for models."""
        service = llm.LLMService()

        # Setup Gemini models
        mock_gemini_model1 = MagicMock()
        mock_gemini_model1.name = "models/gemini-1.5-flash"
        mock_gemini_model2 = MagicMock()
        mock_gemini_model2.name = "models/gemini-pro-vision"  # Should be excluded
        self.mock_gemini_client.models.list.return_value = [mock_gemini_model1, mock_gemini_model2]

        # Setup OpenAI models
        mock_gpt_model = MagicMock()
        mock_gpt_model.id = "gpt-4o"
        mock_dalle_model = MagicMock()
        mock_dalle_model.id = "dall-e-3"  # Should be excluded

        # Setup OpenRouter models
        mock_or_model = MagicMock()
        mock_or_model.id = "anthropic/claude-3-haiku"

        # Configure OpenAI mock to return different lists for OpenAI vs OpenRouter
        # Since they both use the same client class mock in this setup, it's tricky.
        # But wait, LLMService instantiates two OpenAI clients.
        # Ideally we'd mock the specific instances on the service.

        # Let's mock the network calls of the *actual* service instances
        # effectively doing what _discover_models does.

        # OpenAI "models.list()" return objects
        openai_list_mock = MagicMock()
        openai_list_mock.data = [mock_gpt_model, mock_dalle_model]

        or_list_mock = MagicMock()
        or_list_mock.data = [mock_or_model]

        cast(Any, service.openai_client).models.list.return_value = openai_list_mock
        cast(Any, service.openrouter_client).models.list.return_value = or_list_mock

        # Run discovery
        service._discover_models()

        model_ids = [m["id"] for m in service.available_models]

        # Check Gemini
        assert "gemini-1.5-flash" in model_ids
        assert "gemini-pro-vision" not in model_ids  # excluded keyword

        # Check OpenAI
        assert "gpt-4o" in model_ids
        assert "dall-e-3" not in model_ids  # excluded keyword/not starting with gpt

        # Check OpenRouter
        assert "anthropic/claude-3-haiku" in model_ids

    def test_generate_reply_preferred(self):
        """Test using a preferred model."""
        service = llm.LLMService()
        service.available_models = [
            {"id": "gpt-3.5", "provider": "openai"},
            {"id": "gemini-flash", "provider": "gemini"},
        ]

        # Mock _generate_gemini
        with patch.object(service, "_generate_gemini", return_value="Gemini Reply") as mock_gen_gemini:
            result = service.generate_reply("body", "prompt", preferred_model="gemini-flash")

            assert result == "Gemini Reply"
            mock_gen_gemini.assert_called_once()  # Should be called first

    def test_generate_reply_fallback(self):
        """Test fallback when preferred fails."""
        service = llm.LLMService()
        service.available_models = [{"id": "gemini-flash", "provider": "gemini"}, {"id": "gpt-4", "provider": "openai"}]

        with (
            patch.object(service, "_generate_gemini", side_effect=Exception("Fail")),
            patch.object(service, "_generate_openai", return_value="GPT Reply"),
        ):
            result = service.generate_reply("body", "prompt", preferred_model="gemini-flash")

            assert result == "GPT Reply"

    def test_extract_json(self):
        """Test JSON extraction helper."""
        text = '```json\n{"key": "value"}\n```'
        data = llm._extract_json(text)
        assert data == {"key": "value"}

        text2 = '{"key": "value"}'
        data2 = llm._extract_json(text2)
        assert data2 == {"key": "value"}

    def test_generate_batch_replies(self):
        """Test batch generation logic."""
        service = llm.LLMService()
        service.available_models = [{"id": "gemini-flash", "provider": "gemini"}]

        email_batch = [{"id": "1", "subject": "Test", "content": "Hi"}]

        json_response_text = json.dumps([{"id": "1", "reply_text": "Batch Reply"}])

        mock_response = MagicMock()
        mock_response.text = json_response_text
        cast(Any, service.gemini_client).models.generate_content.return_value = mock_response

        results = service.generate_batch_replies(email_batch, "sys prompt")

        assert results["1"] == "Batch Reply"

    def test_connections(self):
        """Test static connection methods."""
        # These are static methods that create their own clients.
        # We need to mock Client/OpenAI inside them or mock the helper functions they use.
        # Since we patched class level imports in setUp, those patches generally persist if imports are right.
        # But static methods import locally or use file-level imports.
        # The imports in llm.py are top-level.

        # test_gemini_connection
        success, msg = llm.LLMService.test_gemini_connection("key")
        assert success is True
        assert "Successful" in msg

        # test_openai_connection (mocking specific call inside)
        # Using the patched OpenAI class from setUp
        self.mock_openai_client_cls.return_value.models.list.return_value = []
        success, msg = llm.LLMService.test_openai_connection("key")
        assert success is True
