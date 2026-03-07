"""Google Gemini LLM provider."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from outlook_bot.providers.base import LLMProvider, ModelInfo

if TYPE_CHECKING:
    import ssl

# Keywords for filtering out non-text models
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


class GeminiProvider(LLMProvider):
    """Google Gemini API provider."""

    name = "gemini"

    def __init__(self) -> None:
        self.client = None

    def initialize(self, api_key: str, ssl_verify: ssl.SSLContext | str) -> None:
        from google import genai
        from google.genai import types

        from outlook_bot.utils.ssl import setup_ssl_environment

        setup_ssl_environment(ssl_verify)
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(client_args={"verify": ssl_verify}),
        )

    def discover_models(self) -> list[ModelInfo]:
        if not self.client:
            return []

        models: list[ModelInfo] = []
        try:
            for m in self.client.models.list():
                name = m.name
                if not name:
                    continue
                model_id = name.split("/")[-1] if "/" in name else name
                lower_id = model_id.lower()

                if "gemini" not in lower_id:
                    continue
                if any(k in lower_id for k in EXCLUDED_MODEL_KEYWORDS):
                    continue
                if "exp" in lower_id:
                    continue
                if re.search(r"-\d{4}-\d{2}-\d{2}", lower_id):
                    continue
                if re.search(r"-\d{4}$", lower_id):
                    continue

                models.append(ModelInfo(id=model_id, provider=self.name))
        except Exception as e:
            print(f"  -> Gemini model discovery failed: {e}")

        return models

    def generate(self, model_id: str, prompt: str) -> str:
        if not self.client:
            return ""
        response = self.client.models.generate_content(model=model_id, contents=prompt)
        return response.text.strip() if response.text else ""

    def generate_json(self, model_id: str, prompt: str) -> str:
        if not self.client:
            return ""
        response = self.client.models.generate_content(
            model=model_id,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        return response.text if response.text else ""

    def test_connection(self, api_key: str, ssl_verify: ssl.SSLContext | str) -> tuple[bool, str]:
        if not api_key:
            return False, "API Key is empty."
        try:
            from google import genai
            from google.genai import types

            from outlook_bot.utils.ssl import setup_ssl_environment

            setup_ssl_environment(ssl_verify)
            client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(client_args={"verify": ssl_verify}),
            )
            list(client.models.list())
            return True, "Connection Successful!"
        except Exception as e:
            return False, f"Connection Failed: {e}"
