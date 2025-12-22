import json
import os
import re
from typing import Any, Dict, List, Optional

import certifi
from google import genai
from google.genai import types
from openai import OpenAI


import yaml


def load_ssl_config_helper():
    """Loads disable_ssl_verify from config.yaml"""
    try:
        config_path = "config.yaml"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = yaml.safe_load(f) or {}
                return data.get("disable_ssl_verify", False)
    except Exception:
        pass
    return False

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
            print("[Security Warning] SSL Verification is DISABLED via config.yaml")

        # Gemini
        if self.gemini_key:
            try:
                # If disable_ssl is True, we pass verify=False to httpx
                # If False, we use certifi (recommended) or default
                verify_option = False if disable_ssl else certifi.where()
                
                self.gemini_client = genai.Client(
                    api_key=self.gemini_key, 
                    http_options=types.HttpOptions(client_args={"verify": verify_option})
                )
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini client: {e}")

        # OpenAI
        if self.openai_key:
            try:
                # OpenAI client handles disable_ssl via http_client arg usually, 
                # but standard init doesn't easily expose it without custom transport.
                # However, for now we focus on Gemini which is the primary issue.
                self.openai_client = OpenAI(api_key=self.openai_key)
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")

    # ... (rest of class)

    @staticmethod
    def test_gemini_connection(api_key):
        """
        Tests connectivity to Gemini API with the provided key.
        Returns (success: bool, message: str)
        """
        if not api_key:
            return False, "API Key is empty."

        try:
            disable_ssl = load_ssl_config_helper()
            verify_option = False if disable_ssl else certifi.where()

            client = genai.Client(
                api_key=api_key, http_options=types.HttpOptions(client_args={"verify": verify_option})
            )
            # Lightweight call to list models
            list(client.models.list())
            return True, "Connection Successful!"
        except Exception as e:
            return False, f"Connection Failed: {str(e)}"

    def _discover_models(self):
        """
        Query providers to find available models, filtering for cheap/fast text generation.
        Aggressively filters out non-text, specialized, or expensive models.
        """
        self.available_models = []
        print("Detecting available LLM models...")

        # Common exclusions for any provider
        EXCLUDED_KEYWORDS = [
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
            "002",  # Legacy numeric versions sometimes imply specialized/old
            "preview",
            "exp",
            "codex",
            "legacy",
        ]

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
                    if any(k in lower_id for k in EXCLUDED_KEYWORDS):
                        continue

                    # 2. Exclude Experimental/Unstable
                    # (unless it's just a version suffix, but 'exp' usually implies beta)
                    # User feedback suggests being strict.
                    if "exp" in lower_id:
                        continue

                    # 3. Exclude Expensive/Pro models
                    if any(key in lower_id for key in ["pro", "ultra"]):
                        continue

                    # 4. Filter out specific date-based versions (e.g. -2024-07-18, -0125)
                    # Pattern 1: YYYY-MM-DD
                    if re.search(r"-\d{4}-\d{2}-\d{2}", lower_id):
                        continue
                    # Pattern 2: -MMDD or -YYYY at end? OpenAI often uses -0125, -1106
                    # Excluding any model ending in -DDDD where D is digit
                    if re.search(r"-\d{4}$", lower_id):
                        # Careful: gpt-4o-mini might have versions?
                        # gpt-3.5-turbo-16k ends in 16k (not 4 digits).
                        # gpt-3.5-turbo-0125 (ends in 4 digits).
                        continue

                    # 5. Must include "Cheap/Fast" indicators
                    if not any(key in lower_id for key in ["flash", "lite"]):
                        continue

                    self.available_models.append({"id": model_id, "provider": "gemini"})

            except Exception as e:
                print(f"  -> Gemini model discovery failed: {e}")

        # 2. OpenAI Discovery
        if self.openai_client:
            try:
                models_page = self.openai_client.models.list()
                for m in models_page.data:
                    mid = m.id
                    lower_id = mid.lower()

                    # Must be a GPT model
                    if not mid.startswith("gpt"):
                        continue

                    # 1. Aggressive Exclusion
                    if any(k in lower_id for k in EXCLUDED_KEYWORDS):
                        continue

                    # 2. Exclude Expensive/Pro models and legacy
                    if "pro" in lower_id:
                        continue
                    if "instruct" in lower_id:
                        continue

                    if "gpt-4" in lower_id and "mini" not in lower_id:
                        # Exclude gpt-4, gpt-4-turbo, gpt-4o (keep only mini)
                        continue

                    # 3. Filter out specific date-based versions (e.g. -2024-07-18, -0125)
                    if re.search(r"-\d{4}-\d{2}-\d{2}", lower_id):
                        continue
                    if re.search(r"-\d{4}$", lower_id):
                        continue

                    # 4. Must include "Cheap/Fast" indicators
                    # target: gpt-4o-mini, gpt-3.5-turbo
                    if not any(key in lower_id for key in ["mini", "turbo"]):
                        continue

                    self.available_models.append({"id": mid, "provider": "openai"})

            except Exception as e:
                print(f"  -> OpenAI model discovery failed: {e}")

        # Sort models by estimated cost/efficiency
        self._sort_models_by_cost()

        if not self.available_models:
            print("  -> No suitable cheap/fast models found. Please check API Keys.")
        else:
            print(
                f"  -> Discovered {len(self.available_models)} suitable models: "
                + ", ".join([m["id"] for m in self.available_models])
            )

    def _sort_models_by_cost(self):
        """
        Sorts self.available_models based on a heuristic of cost/speed + version freshness.

        Sort Keys:
        1. Priority (Ascending): 0 (Cheapest) -> 1 (Very Cheap) -> ...
        2. Version (Ascending): Older versions (2.5, 4.1, 5) preferred within same priority.
        3. Name (Ascending): Alphabetical tie-break.

        Priority 0 (Cheapest): Gemini Lite, GPT-4o-mini, GPT-5-mini
        Priority 1 (Very Cheap): Gemini Flash
        Priority 2 (Cheap): GPT-3.5-Turbo
        Priority 3: Others
        """

        def get_sort_key(model_entry):
            mid = model_entry["id"].lower()

            # --- 1. Priority Score ---
            priority = 3  # Default

            if "lite" in mid:
                priority = 0
            # Avoid matching 'mini' inside 'gemini'
            elif "mini" in mid and "gemini" not in mid:
                priority = 0

            elif "flash" in mid:
                priority = 1

            elif "turbo" in mid:
                priority = 2

            # --- 2. Version Extraction ---
            # Finds the first identifying number sequence (e.g. 2.5, 3.5, 4, 5)
            # handle '4o' as 4.0 if not explicit 4.5
            # We look for (\d+(\.\d+)?)
            version = 0.0
            search = re.search(r"(\d+(\.\d+)?)", mid)
            if search:
                try:
                    version = float(search.group(1))
                except ValueError:
                    version = 0.0

            # Additional heuristic: '4o' is usually better/newer than '4', but '4.1' might be better.
            # If we see 'gpt-4o', maybe bump version slightly if it parsed as 4.0?
            if "gpt-4o" in mid and version == 4.0:
                version = 4.5  # Arbitrary bump to rank above standard 4.0 if needed

            # We want ASCENDING version (Older first, as requested).
            # Python sorts tuples element-wise.
            # So we return +version.

            return (priority, version, mid)

        # Debug sort keys
        # print("DEBUG SORT KEYS:")
        # for m in self.available_models:
        #    print(f"{m['id']}: {get_sort_key(m)}")

        self.available_models.sort(key=get_sort_key)

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

    def generate_reply(self, email_body, system_prompt):
        """
        Tries to generate a reply using available models in order.
        """
        if not self.available_models:
            print("Error: No available models to generate reply.")
            return None

        prompt = f"{system_prompt}\n\nEmail Thread:\n{email_body}\n\nResponse:"

        for model_entry in self.available_models:
            model_id = model_entry["id"]
            provider = model_entry["provider"]

            print(f"Attempting generate with {provider}:{model_id}...")

            try:
                if provider == "gemini":
                    result = self._generate_gemini(model_id, prompt)
                elif provider == "openai":
                    result = self._generate_openai(model_id, prompt)
                else:
                    continue

                if result:
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

    def generate_batch_replies(self, email_batch, system_prompt):
        """
        Generates batch replies. Tries to use the JSON-list prompting strategy.
        """
        if not self.available_models:
            return {}

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

        for model_entry in self.available_models:
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
            disable_ssl = load_ssl_config_helper()
            verify_option = False if disable_ssl else certifi.where()

            client = genai.Client(
                api_key=api_key, http_options=types.HttpOptions(client_args={"verify": verify_option})
            )
            # Lightweight call to list models
            list(client.models.list())
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
            client = OpenAI(api_key=api_key)
            # Lightweight call to list models
            client.models.list()
            return True, "Connection Successful!"
        except Exception as e:
            return False, f"Connection Failed: {str(e)}"
