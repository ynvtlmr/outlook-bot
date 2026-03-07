"""OpenRouter LLM provider (uses OpenAI SDK with custom base URL)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from outlook_bot.providers.base import LLMProvider, ModelInfo
from outlook_bot.providers.openai_provider import EXCLUDED_MODEL_KEYWORDS, _create_openai_client

if TYPE_CHECKING:
    import ssl

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider (OpenAI-compatible)."""

    name = "openrouter"

    def __init__(self) -> None:
        self.client = None

    def initialize(self, api_key: str, ssl_verify: ssl.SSLContext | str) -> None:
        self.client = _create_openai_client(api_key, ssl_verify, base_url=OPENROUTER_BASE_URL)

    def discover_models(self) -> list[ModelInfo]:
        if not self.client:
            return []

        models: list[ModelInfo] = []
        try:
            print("  -> Querying OpenRouter for available models...")
            models_page = self.client.models.list()
            for m in models_page.data:
                mid = m.id
                lower_id = mid.lower()

                if any(k in lower_id for k in EXCLUDED_MODEL_KEYWORDS):
                    continue

                models.append(ModelInfo(id=mid, provider=self.name))

            print(f"  -> Discovered {len(models)} suitable OpenRouter models.")
        except Exception as e:
            print(f"  -> OpenRouter model discovery failed: {e}")

        return models

    def generate(self, model_id: str, prompt: str) -> str:
        if not self.client:
            return ""
        completion = self.client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
        )
        content = completion.choices[0].message.content
        return content.strip() if content else ""

    def generate_json(self, model_id: str, prompt: str) -> str:
        # OpenRouter models may not support json_object response format
        return self.generate(model_id, prompt)

    def test_connection(self, api_key: str, ssl_verify: ssl.SSLContext | str) -> tuple[bool, str]:
        if not api_key:
            return False, "API Key is empty."
        try:
            client = _create_openai_client(api_key, ssl_verify, base_url=OPENROUTER_BASE_URL)
            client.models.list()
            return True, "Connection Successful!"
        except Exception as e:
            return False, f"Connection Failed: {e}"
