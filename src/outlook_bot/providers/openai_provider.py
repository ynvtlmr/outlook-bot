"""OpenAI LLM provider."""

from __future__ import annotations

import os
import re
import ssl

from outlook_bot.providers.base import LLMProvider, ModelInfo

EXCLUDED_MODEL_KEYWORDS = [
    "image",
    "vision",
    "audio",
    "video",
    "tts",
    "speech",
    "transcribe",
    "whisper",
    "dall-e",
    "embedding",
    "search",
    "moderation",
    "realtime",
    "creation",
    "edit",
    "001",
    "002",
    "exp",
    "codex",
    "legacy",
    "robotics",
]


def _create_openai_client(api_key: str, ssl_verify: ssl.SSLContext | str, base_url: str | None = None):
    """Create an OpenAI client with proper SSL configuration."""
    from openai import OpenAI

    from outlook_bot.utils.ssl import setup_ssl_environment

    setup_ssl_environment(ssl_verify)

    kwargs: dict = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url

    if isinstance(ssl_verify, ssl.SSLContext):
        import httpx

        kwargs["http_client"] = httpx.Client(verify=ssl_verify)
    elif isinstance(ssl_verify, str) and os.path.exists(ssl_verify):
        pass  # env vars set by setup_ssl_environment

    return OpenAI(**kwargs)


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    name = "openai"

    def __init__(self) -> None:
        self.client = None

    def initialize(self, api_key: str, ssl_verify: ssl.SSLContext | str) -> None:
        self.client = _create_openai_client(api_key, ssl_verify)

    def discover_models(self) -> list[ModelInfo]:
        if not self.client:
            return []

        models: list[ModelInfo] = []
        try:
            print("  -> Querying OpenAI for available models...")
            models_page = self.client.models.list()
            for m in models_page.data:
                mid = m.id
                lower_id = mid.lower()

                if not mid.startswith("gpt"):
                    continue
                if any(k in lower_id for k in EXCLUDED_MODEL_KEYWORDS):
                    continue
                if re.search(r"-\d{4}-\d{2}-\d{2}", lower_id):
                    continue
                if re.search(r"-\d{4}$", lower_id):
                    continue

                models.append(ModelInfo(id=mid, provider=self.name))
        except Exception as e:
            print(f"  -> OpenAI model discovery failed: {e}")

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
        if not self.client:
            return ""
        completion = self.client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content
        return content if content else ""

    def test_connection(self, api_key: str, ssl_verify: ssl.SSLContext | str) -> tuple[bool, str]:
        if not api_key:
            return False, "API Key is empty."
        try:
            client = _create_openai_client(api_key, ssl_verify)
            client.models.list()
            return True, "Connection Successful!"
        except Exception as e:
            return False, f"Connection Failed: {e}"
