import json
import os
import re
import ssl
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types
from openai import OpenAI

from ssl_utils import get_ssl_verify_option

# Model exclusion keywords for filtering out non-text/specialized models
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


def load_ssl_config_helper():
    """
    Returns SSL verification status.
    HARDCODED: Always returns True (SSL verification disabled) due to Zscaler corporate proxy issues.
    This cannot be configured via config.yaml to prevent accidental removal.
    """
    # Hardcoded to True - SSL verification must be disabled for Zscaler compatibility
    return True


class LLMService:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

        self.gemini_client: Optional[genai.Client] = None
        self.openai_client: Optional[OpenAI] = None

        # List of dicts: {'id': str, 'provider': str}
        # Sorted by preference if possible, but detection order is likely sufficient for now.
        self.available_models: List[Dict[str, Any]] = []

        self._init_clients()
        self._discover_models()

    def _init_clients(self):
        disable_ssl = load_ssl_config_helper()
        if disable_ssl:
            print("[Security Warning] SSL Verification is DISABLED (hardcoded for Zscaler compatibility)")

        # Gemini
        if self.gemini_key:
            try:
                # Use ssl_utils to get the best verify option (Path or SSL Context)
                verify_option = get_ssl_verify_option(disable_ssl)

                # Global ENV Configuration for robustness (Fixes OpenAI and others)
                if isinstance(verify_option, str) and os.path.exists(verify_option):
                    print(f"[Info] Using merged certificate bundle: {verify_option}")
                    print(f"Global SSL Configuration: Setting SSL_CERT_FILE to {verify_option}")
                    os.environ["SSL_CERT_FILE"] = verify_option
                    os.environ["REQUESTS_CA_BUNDLE"] = verify_option
                elif isinstance(verify_option, ssl.SSLContext):
                    print("[Info] SSL verification disabled (using CERT_NONE context)")
                    # Clear env vars that might point to failing bundles when SSL is disabled
                    # This ensures the SSL context is used instead of env vars
                    if "SSL_CERT_FILE" in os.environ:
                        del os.environ["SSL_CERT_FILE"]
                    if "REQUESTS_CA_BUNDLE" in os.environ:
                        del os.environ["REQUESTS_CA_BUNDLE"]

                self.gemini_client = genai.Client(
                    api_key=self.gemini_key, http_options=types.HttpOptions(client_args={"verify": verify_option})
                )
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini client: {e}")

        # OpenAI
        if self.openai_key:
            try:
                # Use the same SSL configuration approach as test_openai_connection
                verify_option = get_ssl_verify_option(disable_ssl)

                if isinstance(verify_option, str) and os.path.exists(verify_option):
                    # Use certificate bundle via environment variables
                    os.environ["SSL_CERT_FILE"] = verify_option
                    os.environ["REQUESTS_CA_BUNDLE"] = verify_option
                    self.openai_client = OpenAI(api_key=self.openai_key)
                elif isinstance(verify_option, ssl.SSLContext):
                    # For CERT_NONE, use custom httpx client
                    import httpx

                    httpx_client = httpx.Client(verify=verify_option)
                    self.openai_client = OpenAI(api_key=self.openai_key, http_client=httpx_client)
                else:
                    # Default initialization
                    self.openai_client = OpenAI(api_key=self.openai_key)
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")

        # OpenRouter
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if self.openrouter_key:
            try:
                verify_option = get_ssl_verify_option(disable_ssl)
                OR_BASE_URL = "https://openrouter.ai/api/v1"

                # Similar SSL handling for OpenRouter (via OpenAI SDK)
                if isinstance(verify_option, str) and os.path.exists(verify_option):
                    # Globals likely already set if OpenAI init ran, but safe to set again or rely on them
                    os.environ["SSL_CERT_FILE"] = verify_option
                    os.environ["REQUESTS_CA_BUNDLE"] = verify_option
                    self.openrouter_client = OpenAI(base_url=OR_BASE_URL, api_key=self.openrouter_key)
                elif isinstance(verify_option, ssl.SSLContext):
                    import httpx

                    httpx_client = httpx.Client(verify=verify_option)
                    self.openrouter_client = OpenAI(
                        base_url=OR_BASE_URL, api_key=self.openrouter_key, http_client=httpx_client
                    )
                else:
                    self.openrouter_client = OpenAI(base_url=OR_BASE_URL, api_key=self.openrouter_key)
            except Exception as e:
                print(f"Warning: Failed to initialize OpenRouter client: {e}")
                self.openrouter_client = None
        else:
            self.openrouter_client = None

    def _discover_models(self):
        """
        Query providers to find available models, filtering for cheap/fast text generation.
        Aggressively filters out non-text, specialized, or expensive models.
        """
        self.available_models = []
        print("Detecting available LLM models...")

        # 1. Gemini Discovery
        if self.gemini_client:
            try:
                for m in self.gemini_client.models.list():
                    name = m.name
                    if not name:
                        continue
                    model_id = name.split("/")[-1] if "/" in name else name
                    lower_id = model_id.lower()

                    # Base checks
                    if "gemini" not in lower_id:
                        continue

                    # 1. Aggressive Exclusion
                    if any(k in lower_id for k in EXCLUDED_MODEL_KEYWORDS):
                        continue

                    # Exclude Experimental/Unstable
                    if "exp" in lower_id:
                        continue

                    # Filter out specific date-based versions (e.g. -2024-07-18, -0125)
                    if re.search(r"-\d{4}-\d{2}-\d{2}", lower_id):
                        continue
                    if re.search(r"-\d{4}$", lower_id):
                        continue

                    self.available_models.append({"id": model_id, "provider": "gemini"})

            except Exception as e:
                print(f"  -> Gemini model discovery failed: {e}")

        # 2. OpenAI Discovery
        if self.openai_client:
            try:
                print("  -> Querying OpenAI for available models...")
                models_page = self.openai_client.models.list()
                print(f"  -> Received {len(models_page.data)} models from OpenAI")
                for m in models_page.data:
                    mid = m.id
                    lower_id = mid.lower()

                    # Must be a GPT model
                    if not mid.startswith("gpt"):
                        continue

                    # Aggressive Exclusion
                    if any(k in lower_id for k in EXCLUDED_MODEL_KEYWORDS):
                        continue

                    # Filter out specific date-based versions (e.g. -2024-07-18, -0125)
                    if re.search(r"-\d{4}-\d{2}-\d{2}", lower_id):
                        continue
                    if re.search(r"-\d{4}$", lower_id):
                        continue

                    self.available_models.append({"id": mid, "provider": "openai"})

                if len(self.available_models) == 0:
                    print("  -> Warning: No OpenAI models passed filtering criteria")
                    print("  -> Consider checking filter rules if models are expected")

            except Exception as e:
                print(f"  -> OpenAI model discovery failed: {e}")
                import traceback

                print(f"  -> Traceback: {traceback.format_exc()}")

        # 3. OpenRouter Discovery
        if self.openrouter_client:
            try:
                print("  -> Querying OpenRouter for available models...")
                models_page = self.openrouter_client.models.list()

                count = 0
                for m in models_page.data:
                    mid = m.id
                    lower_id = mid.lower()

                    # Aggressive Exclusion
                    if any(k in lower_id for k in EXCLUDED_MODEL_KEYWORDS):
                        continue

                    self.available_models.append({"id": mid, "provider": "openrouter"})
                    count += 1

                print(f"  -> Discovered {count} suitable OpenRouter models.")

            except Exception as e:
                print(f"  -> OpenRouter model discovery failed: {e}")

        if not self.available_models:
            print("  -> No suitable cheap/fast models found. Please check API Keys.")
        else:
            print(
                f"  -> Discovered {len(self.available_models)} suitable models: "
                + ", ".join([m["id"] for m in self.available_models])
            )

    def get_models_list(self):
        """Returns list of model names for display."""
        return [m["id"] for m in self.available_models]

    def refresh_models(self):
        """Re-initializes clients and rediscovers models (useful for GUI)."""
        # Reload env vars in case they changed in memory
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self._init_clients()
        self._discover_models()
        return self.get_models_list()

    def generate_reply(self, email_body, system_prompt, preferred_model=None):
        """
        Tries to generate a reply using available models in order.
        If preferred_model is specified, tries that model first.
        """
        if not self.available_models:
            print("Error: No available models to generate reply.")
            return None

        prompt = f"{system_prompt}\n\nEmail Thread:\n{email_body}\n\nResponse:"

        # Reorder models to try preferred_model first if specified
        models_to_try = self.available_models.copy()
        if preferred_model:
            # Find the preferred model and move it to the front
            preferred_entry = None
            for i, model_entry in enumerate(models_to_try):
                if model_entry["id"] == preferred_model:
                    preferred_entry = models_to_try.pop(i)
                    break

            if preferred_entry:
                models_to_try.insert(0, preferred_entry)
                print(f"[Info] Using preferred model: {preferred_model}")
            else:
                print(f"[Warning] Preferred model '{preferred_model}' not found. Using default order.")

        for model_entry in models_to_try:
            model_id = model_entry["id"]
            provider = model_entry["provider"]

            print(f"Attempting generate with {provider}:{model_id}...")

            try:
                if provider == "gemini":
                    result = self._generate_gemini(model_id, prompt)
                elif provider == "openai":
                    result = self._generate_openai(model_id, prompt)
                elif provider == "openrouter":
                    result = self._generate_openrouter(model_id, prompt)
                else:
                    continue

                if result:
                    print(f"✓ Selected model: {provider}:{model_id}")
                    return result
            except Exception as e:
                print(f"  -> Failed with {model_id}: {e}")
                continue

        print("Error: All models failed.")
        return None

    def _generate_gemini(self, model_id, prompt):
        if not self.gemini_client:
            return ""
        response = self.gemini_client.models.generate_content(model=model_id, contents=prompt)
        if not response.text:
            return ""
        return response.text.strip()

    def _generate_openai(self, model_id, prompt):
        if not self.openai_client:
            return ""
        completion = self.openai_client.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }  # System prompt is part of 'prompt' arg in legacy signature, but we can split if we want.
                # To match exact legacy behavior of genai.py which concat'd them:
                # We'll just send it as one user message or split it?
                # The arg is 'prompt' which is system_prompt + body.
                # OpenAI Chat models prefer setup.
                # However, for compat with the exact string passed:
            ],
        )
        return completion.choices[0].message.content.strip() if completion.choices[0].message.content else ""

    def generate_batch_replies(self, email_batch, system_prompt, preferred_model=None):
        """
        Generates batch replies. Tries to use the JSON-list prompting strategy.
        If preferred_model is specified, tries that model first.
        """
        if not self.available_models:
            return {}

        # Reorder models to try preferred_model first if specified
        models_to_try = self.available_models.copy()
        if preferred_model:
            # Find the preferred model and move it to the front
            preferred_entry = None
            for i, model_entry in enumerate(models_to_try):
                if model_entry["id"] == preferred_model:
                    preferred_entry = models_to_try.pop(i)
                    break

            if preferred_entry:
                models_to_try.insert(0, preferred_entry)
                print(f"[Info] Using preferred model for batch: {preferred_model}")
            else:
                print(f"[Warning] Preferred model '{preferred_model}' not found. Using default order.")

        # Prepare the centralized prompt (same as in genai.py)
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

        prompt_batch = [
            {"id": item["id"], "subject": item["subject"], "content": item["content"]} for item in email_batch
        ]

        full_json_input = json.dumps(prompt_batch, indent=2)
        full_prompt = prompt_intro + full_json_input

        for model_entry in models_to_try:
            model_id = model_entry["id"]
            provider = model_entry["provider"]

            print(f"Attempting batch generate with {provider}:{model_id}...")

            try:
                raw_text = ""
                if provider == "gemini":
                    if not self.gemini_client:
                        continue
                    response = self.gemini_client.models.generate_content(
                        model=model_id, contents=full_prompt, config={"response_mime_type": "application/json"}
                    )
                    raw_text = response.text if response.text else ""
                elif provider == "openai":
                    if not self.openai_client:
                        continue
                    # OpenAI supports json_object response format on newer models
                    # We need to set the system message nicely if possible, or just dump it all in user.
                    # For robust JSON, we ask for json_object type.
                    completion = self.openai_client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                            {"role": "user", "content": full_prompt},
                        ],
                        response_format={"type": "json_object"},
                        # Note: 'json_object' requires 'json' in the prompt. prompt_intro has it.
                        # Also, this returns a JSON object, but our prompt asks for a LIST.
                        # OpenAI's 'json_object' mode ensures valid JSON,
                        # but usually expects a root object { "data": [...] }
                        # If our prompt asks for a list, it might complain or wrap it.
                        # Let's adjust safety: If provider is OpenAI, we might wrap the request or just trust it.
                        # For now, let's try standard mode if we aren't sure about the structure,
                        # or strictly ask for an object.
                    )
                    content = completion.choices[0].message.content
                    raw_text = content if content else ""
                elif provider == "openrouter":
                    # OpenRouter uses OpenAI client but might point to non-OpenAI models that don't support json_object
                    if not self.openrouter_client:
                        continue
                    # Try standard generation without response_format first for max compatibility
                    completion = self.openrouter_client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "user", "content": full_prompt},
                        ],
                    )
                    content = completion.choices[0].message.content
                    raw_text = content if content else ""

                # Parse JSON
                # Clean up markdown if present
                clean_text = raw_text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]

                parsed_data = json.loads(clean_text)

                # OpenAI json_object mode might wrap it?
                # If prompt asked for list, valid JSON is [].
                # If parsed_data is dict, maybe it has a key?
                results = {}

                if isinstance(parsed_data, list):
                    items = parsed_data
                elif isinstance(parsed_data, dict):
                    # Check values for list
                    # Maybe it wrapped it in "replies": [...]?
                    # Or maybe it's just a dict of id->reply?
                    # Let's hope the model followed instructions.
                    # If dict, keys might be IDs?
                    # We'll try to walk it.
                    values = list(parsed_data.values())
                    if values and isinstance(values[0], list):
                        items = values[0]
                    else:
                        # Maybe it returned {"id": "reply"} mapping?
                        # Let's assume list of objects as requested.
                        items = []
                else:
                    items = []

                for item in items:
                    if isinstance(item, dict) and "id" in item and "reply_text" in item:
                        results[item["id"]] = item["reply_text"]

                if results:
                    print(f"✓ Selected model for batch: {provider}:{model_id}")
                    return results

            except Exception as e:
                print(f"  -> Failed batch with {model_id}: {e}")
                continue

        return {}

    @staticmethod
    def test_gemini_connection(api_key):
        """
        Tests connectivity to Gemini API with the provided key.
        Returns (success: bool, message: str)
        """
        if not api_key:
            return False, "API Key is empty."

        try:
            # Load SSL config and use it
            disable_ssl = load_ssl_config_helper()
            verify_option = get_ssl_verify_option(disable_ssl)

            # Set global ENVs for consistency (only if using certificate bundle)
            # If using SSL context (CERT_NONE), don't set env vars as they might interfere
            if isinstance(verify_option, str) and os.path.exists(verify_option):
                os.environ["SSL_CERT_FILE"] = verify_option
                os.environ["REQUESTS_CA_BUNDLE"] = verify_option
            elif isinstance(verify_option, ssl.SSLContext):
                # When SSL is disabled, clear env vars that might point to failing bundles
                # This ensures the SSL context is used instead of env vars
                if "SSL_CERT_FILE" in os.environ:
                    del os.environ["SSL_CERT_FILE"]
                if "REQUESTS_CA_BUNDLE" in os.environ:
                    del os.environ["REQUESTS_CA_BUNDLE"]

            client = genai.Client(
                api_key=api_key, http_options=types.HttpOptions(client_args={"verify": verify_option})
            )
            # Lightweight call to list models
            list(client.models.list())
            return True, "Connection Successful!"
        except Exception as e:
            return False, f"Connection Failed: {str(e)}"

    def _generate_openrouter(self, model_id, prompt):
        if not self.openrouter_client:
            return ""
        # Reuse OpenAI SDK logic for OpenRouter
        completion = self.openrouter_client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
        )
        return completion.choices[0].message.content.strip() if completion.choices[0].message.content else ""

    @staticmethod
    def test_openrouter_connection(api_key):
        """
        Tests connectivity to OpenRouter API.
        """
        if not api_key:
            return False, "API Key is empty."

        try:
            disable_ssl = load_ssl_config_helper()
            verify_option = get_ssl_verify_option(disable_ssl)
            OR_BASE_URL = "https://openrouter.ai/api/v1"

            if isinstance(verify_option, str) and os.path.exists(verify_option):
                os.environ["SSL_CERT_FILE"] = verify_option
                os.environ["REQUESTS_CA_BUNDLE"] = verify_option
                client = OpenAI(base_url=OR_BASE_URL, api_key=api_key)
            elif isinstance(verify_option, ssl.SSLContext):
                import httpx

                httpx_client = httpx.Client(verify=verify_option)
                client = OpenAI(base_url=OR_BASE_URL, api_key=api_key, http_client=httpx_client)
            else:
                client = OpenAI(base_url=OR_BASE_URL, api_key=api_key)

            # Lightweight call
            client.models.list()
            return True, "Connection Successful!"
        except Exception as e:
            return False, f"Connection Failed: {str(e)}"

    @staticmethod
    def test_openai_connection(api_key):
        """
        Tests connectivity to OpenAI API with the provided key.
        Returns (success: bool, message: str)
        """
        if not api_key:
            return False, "API Key is empty."

        try:
            # OpenAI respects SSL_CERT_FILE and REQUESTS_CA_BUNDLE env vars
            # These are set in _init_clients when SSL is configured
            # For CERT_NONE, we need to use custom httpx client
            disable_ssl = load_ssl_config_helper()
            verify_option = get_ssl_verify_option(disable_ssl)

            # Set env vars if using certificate bundle
            if isinstance(verify_option, str) and os.path.exists(verify_option):
                os.environ["SSL_CERT_FILE"] = verify_option
                os.environ["REQUESTS_CA_BUNDLE"] = verify_option
                client = OpenAI(api_key=api_key)
            elif isinstance(verify_option, ssl.SSLContext):
                # For CERT_NONE, we need custom httpx client
                import httpx

                httpx_client = httpx.Client(verify=verify_option)
                client = OpenAI(api_key=api_key, http_client=httpx_client)
            else:
                client = OpenAI(api_key=api_key)

            # Lightweight call to list models
            client.models.list()
            return True, "Connection Successful!"
        except Exception as e:
            return False, f"Connection Failed: {str(e)}"
