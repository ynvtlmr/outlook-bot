"""Provider registry with discovery, fallback chain, and retry logic."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any

from outlook_bot.core.config import CredentialManager
from outlook_bot.providers.gemini import GeminiProvider
from outlook_bot.providers.openai_provider import OpenAIProvider
from outlook_bot.providers.openrouter import OpenRouterProvider
from outlook_bot.utils.ssl import get_ssl_verify_option

if TYPE_CHECKING:
    from outlook_bot.providers.base import LLMProvider, ModelInfo


def _extract_json(text: str) -> Any:
    """Extract and parse JSON from LLM response text, stripping markdown fences."""
    clean_text = text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    if clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    return json.loads(clean_text)


class ProviderRegistry:
    """Manages multiple LLM providers with automatic discovery and fallback."""

    def __init__(self, ssl_mode: str = "disabled", max_retries: int = 2) -> None:
        self.ssl_mode = ssl_mode
        self.max_retries = max_retries
        self.providers: dict[str, LLMProvider] = {}
        self.available_models: list[ModelInfo] = []

        self._init_providers()
        self._discover_all_models()

    def _init_providers(self) -> None:
        ssl_verify = get_ssl_verify_option(self.ssl_mode)

        if self.ssl_mode == "disabled":
            print("[Security Warning] SSL Verification is DISABLED (configured for Zscaler compatibility)")

        gemini_key = CredentialManager.get_gemini_key()
        if gemini_key:
            try:
                provider = GeminiProvider()
                provider.initialize(gemini_key, ssl_verify)
                self.providers["gemini"] = provider
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini: {e}")

        openai_key = CredentialManager.get_openai_key()
        if openai_key:
            try:
                provider = OpenAIProvider()
                provider.initialize(openai_key, ssl_verify)
                self.providers["openai"] = provider
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI: {e}")

        openrouter_key = CredentialManager.get_openrouter_key()
        if openrouter_key:
            try:
                provider = OpenRouterProvider()
                provider.initialize(openrouter_key, ssl_verify)
                self.providers["openrouter"] = provider
            except Exception as e:
                print(f"Warning: Failed to initialize OpenRouter: {e}")

    def _discover_all_models(self) -> None:
        self.available_models = []
        print("Detecting available LLM models...")

        for provider in self.providers.values():
            models = provider.discover_models()
            self.available_models.extend(models)

        if not self.available_models:
            print("  -> No suitable models found. Please check API Keys.")
        else:
            model_ids = ", ".join(m.id for m in self.available_models)
            print(f"  -> Discovered {len(self.available_models)} suitable models: {model_ids}")

    def get_models_list(self) -> list[str]:
        return [m.id for m in self.available_models]

    def refresh(self) -> list[str]:
        """Re-initialize and rediscover models."""
        self.providers.clear()
        self._init_providers()
        self._discover_all_models()
        return self.get_models_list()

    def _ordered_models(self, preferred_model: str | None = None) -> list[ModelInfo]:
        models = list(self.available_models)
        if preferred_model:
            for i, m in enumerate(models):
                if m.id == preferred_model:
                    models.insert(0, models.pop(i))
                    print(f"[Info] Using preferred model: {preferred_model}")
                    break
            else:
                print(f"[Warning] Preferred model '{preferred_model}' not found. Using default order.")
        return models

    def _with_retry(self, fn, *args, **kwargs):
        """Execute fn with exponential backoff retry."""
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    wait = 2**attempt
                    print(f"  -> Retry {attempt + 1}/{self.max_retries} after {wait}s...")
                    time.sleep(wait)
        raise last_error  # type: ignore[misc]

    def generate_reply(self, email_body: str, system_prompt: str, preferred_model: str | None = None) -> str | None:
        """Generate a reply using available models with fallback."""
        if not self.available_models:
            print("Error: No available models to generate reply.")
            return None

        prompt = f"{system_prompt}\n\nEmail Thread:\n{email_body}\n\nResponse:"

        for model in self._ordered_models(preferred_model):
            provider = self.providers.get(model.provider)
            if not provider:
                continue

            print(f"Attempting generate with {model.provider}:{model.id}...")
            try:
                result = self._with_retry(provider.generate, model.id, prompt)
                if result:
                    print(f"  -> Selected model: {model.provider}:{model.id}")
                    return result
            except Exception as e:
                print(f"  -> Failed with {model.id}: {e}")

        print("Error: All models failed.")
        return None

    def generate_batch_replies(
        self,
        email_batch: list[dict[str, str]],
        system_prompt: str,
        preferred_model: str | None = None,
    ) -> dict[str, str]:
        """Generate batch replies using JSON-based prompting."""
        if not self.available_models:
            return {}

        prompt_intro = (
            f"{system_prompt}\n\n"
            "TASK: You are processing a batch of emails. For each email provided in the JSON list below, "
            "generate a reply based on the persona.\n"
            "OUTPUT FORMAT: You MUST return a raw JSON list of objects. "
            "Each object must have exactly two fields:\n"
            '  - "id": The exact id from the input.\n'
            '  - "reply_text": Your generated response.\n\n'
            "Do not output markdown formatting (like ```json), just the raw JSON.\n\n"
            "INPUT DATA:\n"
        )

        batch_data = [
            {"id": item["id"], "subject": item["subject"], "content": item["content"]} for item in email_batch
        ]
        full_prompt = prompt_intro + json.dumps(batch_data, indent=2)

        for model in self._ordered_models(preferred_model):
            provider = self.providers.get(model.provider)
            if not provider:
                continue

            print(f"Attempting batch generate with {model.provider}:{model.id}...")
            try:
                if model.provider == "gemini":
                    raw_text = self._with_retry(provider.generate_json, model.id, full_prompt)
                else:
                    raw_text = self._with_retry(provider.generate_json, model.id, full_prompt)

                parsed = _extract_json(raw_text)
                results = self._parse_batch_response(parsed)

                if results:
                    print(f"  -> Selected model for batch: {model.provider}:{model.id}")
                    return results

            except json.JSONDecodeError:
                print(f"  -> JSON parse failed for {model.id} output.")
            except Exception as e:
                print(f"  -> Failed batch with {model.id}: {e}")

        return {}

    @staticmethod
    def _parse_batch_response(parsed: Any) -> dict[str, str]:
        """Parse batch response, handling both list and dict formats."""
        results: dict[str, str] = {}

        if isinstance(parsed, list):
            items = parsed
        elif isinstance(parsed, dict):
            values = list(parsed.values())
            items = values[0] if values and isinstance(values[0], list) else []
        else:
            return results

        for item in items:
            if isinstance(item, dict) and "id" in item and "reply_text" in item:
                results[item["id"]] = item["reply_text"]

        return results

    def generate_thread_summary(self, thread_content: str, preferred_model: str | None = None) -> str | None:
        """Generate a one-paragraph thread summary."""
        prompt = (
            "You are summarizing an email thread. Create a concise, one-paragraph summary that covers:\n"
            "- The main topic or purpose of the thread\n"
            "- Current status and any key decisions made\n"
            "- Next steps or action items (if any)\n\n"
            "Keep it to one paragraph. Be clear and business-focused.\n\n"
            f"Email Thread:\n{thread_content}\n\n"
            "Summary (one paragraph):"
        )
        return self._generate_with_fallback(prompt, preferred_model)

    def generate_sf_note(self, thread_content: str, preferred_model: str | None = None) -> str | None:
        """Generate a Salesforce activity note."""
        from datetime import datetime

        today = datetime.now()
        date_str = f"{today.month}/{today.day}/{str(today.year)[-2:]}"

        prompt = (
            f"Email Thread:\n{thread_content}\n\n"
            f"Write a one-sentence Salesforce note starting with {date_str}. "
            f"TL;DR style, punchy, straight to the point. "
            f"Drop the subject pronoun - say 'reached out' not 'we reached out', 'pushing' not 'we're pushing'. "
            f"Just the note, nothing else."
        )
        result = self._generate_with_fallback(prompt, preferred_model)
        if result and not result.strip().startswith(date_str):
            result = f"{date_str} {result.strip()}"
        return result

    def _generate_with_fallback(self, prompt: str, preferred_model: str | None = None) -> str | None:
        """Generate text using models with fallback."""
        if not self.available_models:
            return None

        for model in self._ordered_models(preferred_model):
            provider = self.providers.get(model.provider)
            if not provider:
                continue
            try:
                result = self._with_retry(provider.generate, model.id, prompt)
                if result:
                    return result.strip()
            except Exception as e:
                print(f"  -> Failed with {model.id}: {e}")

        return None

    def test_connection(self, provider_name: str, api_key: str) -> tuple[bool, str]:
        """Test connectivity for a specific provider."""
        ssl_verify = get_ssl_verify_option(self.ssl_mode)
        provider_map: dict[str, type[LLMProvider]] = {
            "gemini": GeminiProvider,
            "openai": OpenAIProvider,
            "openrouter": OpenRouterProvider,
        }
        provider_cls = provider_map.get(provider_name)
        if not provider_cls:
            return False, f"Unknown provider: {provider_name}"
        return provider_cls().test_connection(api_key, ssl_verify)
