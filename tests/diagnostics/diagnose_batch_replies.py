"""
Diagnostic script to test why generate_batch_replies returns 0 replies.

Top 3 potential issues:
1. No available models discovered
2. Gemini client not initialized or API call fails
3. JSON parsing failure or response format mismatch
"""

import os
import sys
import traceback
from typing import Any, List, Optional, Tuple, Type

from dotenv import load_dotenv

# --- Environment Setup (Must be before imports) ---


def setup_environment() -> None:
    """Configures sys.path and loads .dotenv to ensure imports work."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Load .env
    env_path = os.path.join(project_root, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
    else:
        load_dotenv()

    # Add src to path
    src_path = os.path.join(project_root, "src")
    if os.path.exists(src_path) and src_path not in sys.path:
        sys.path.append(src_path)


# --- Diagnostic Class ---


class BatchReplyDiagnoser:
    """Encapsulates diagnostic logic to keep namespaces clean and code DRY."""

    def __init__(self, llm_service_cls: Type):
        self.LLMService = llm_service_cls
        self.results: List[Tuple[str, bool, str]] = []

    def _log_header(self, title: str) -> None:
        print("\n" + "=" * 60)
        print(title)
        print("=" * 60)

    def _log_pass(self, msg: str) -> bool:
        print(f"\n[PASS] {msg}")
        return True

    def _log_fail(self, msg: str, diagnosis: Optional[str] = None) -> bool:
        print(f"\n[FAIL] {msg}")
        if diagnosis:
            print(f"[Diagnosis] {diagnosis}")
        return False

    def _log_skip(self, msg: str) -> bool:
        print(f"[SKIP] {msg}")
        return True

    def _get_gemini_model(self, service: Any) -> Optional[str]:
        """Helper to find the first available Gemini model."""
        for model in service.available_models:
            if model["provider"] == "gemini":
                return model["id"]
        return None

    def run_scenario_1_discovery(self) -> Tuple[bool, str]:
        """Scenario 1: No available models discovered"""
        self._log_header("SCENARIO 1: Testing No Available Models")

        try:
            service = self.LLMService()
            model_count = len(service.available_models)

            print(f"\n[Status] Available models count: {model_count}")
            print(f"[Status] Available models: {[m['id'] for m in service.available_models]}")
            print(f"[Status] Gemini client initialized: {service.gemini_client is not None}")
            print(f"[Status] OpenAI client initialized: {service.openai_client is not None}")

            if not service.available_models:
                self._log_fail(
                    "No available models found!",
                    "This will cause generate_batch_replies to return {} immediately",
                )
                return False, "No models available"

            self._log_pass(f"Found {model_count} models")
            return True, f"Found {model_count} models"

        except Exception as e:
            traceback.print_exc()
            return False, f"Exception: {e}"

    def run_scenario_2_api_call(self) -> Tuple[bool, str]:
        """Scenario 2: Gemini client initialization and API call"""
        self._log_header("SCENARIO 2: Testing Gemini Client & API Call")

        # Local import to avoid top-level dependency
        from config import ENV_GEMINI_API_KEY

        try:
            service = self.LLMService()

            # 1. Check Initialization
            if not service.gemini_client:
                gemini_key = os.getenv(ENV_GEMINI_API_KEY)
                reason = "GEMINI_API_KEY missing" if not gemini_key else "Init failed despite key"
                self._log_fail(
                    "Gemini client is not initialized!",
                    f"{reason}. This causes batch generation to skip Gemini.",
                )
                return False, "Gemini client not initialized"

            print("\n[PASS] Gemini client is initialized")

            # 2. Prerequisites for API Call
            if not service.available_models:
                return self._log_skip("No models available to test API call"), "Client init (no models)"

            gemini_model = self._get_gemini_model(service)
            if not gemini_model:
                return (
                    self._log_skip("No Gemini models in available_models list"),
                    "Client init (no Gemini models)",
                )

            # 3. Test API Call
            print(f"\n[Testing] Attempting API call with model: {gemini_model}")
            test_prompt = 'Say \'test\' in JSON format: {"test": "success"}'

            try:
                response = service.gemini_client.models.generate_content(
                    model=gemini_model,
                    contents=test_prompt,
                    config={"response_mime_type": "application/json"},
                )

                if response and response.text:
                    self._log_pass(f"API call successful. Response: {response.text[:100]}...")
                    return True, "API call successful"
                else:
                    self._log_fail("API call returned empty response")
                    return False, "Empty response from API"

            except Exception as api_error:
                print(f"\n[Error Type] {type(api_error).__name__}")
                traceback.print_exc()
                return False, f"API call failed: {str(api_error)}"

        except Exception as e:
            traceback.print_exc()
            return False, f"Exception: {e}"

    def run_scenario_3_json_parsing(self) -> Tuple[bool, str]:
        """Scenario 3: JSON parsing and response format"""
        self._log_header("SCENARIO 3: Testing JSON Parsing & Response Format")

        try:
            service = self.LLMService()

            # Prerequisites
            if not service.available_models:
                return self._log_skip("No models available"), "No models"
            if not service.gemini_client:
                return self._log_skip("Gemini client not initialized"), "No client"

            gemini_model = self._get_gemini_model(service)
            if not gemini_model:
                return self._log_skip("No Gemini models available"), "No Gemini models"

            print(f"\n[Testing] Testing batch reply generation with model: {gemini_model}")

            # Test Payload
            test_batch = [{"id": "test-123", "subject": "Test Email", "content": "This is a test email content."}]
            test_system_prompt = "You are a helpful assistant."

            # Execution
            try:
                results = service.generate_batch_replies(test_batch, test_system_prompt)
                print(f"\n[Result] Received {len(results)} replies: {results}")

                if results:
                    self._log_pass("Batch generation returned results")
                    return True, f"Generated {len(results)} replies"
                else:
                    self._log_fail(
                        "Batch generation returned empty results",
                        "Likely JSON parsing failure or schema mismatch (check logs).",
                    )
                    return False, "Empty results"

            except Exception as gen_error:
                traceback.print_exc()
                return False, f"Generation exception: {gen_error}"

        except Exception as e:
            traceback.print_exc()
            return False, f"Exception: {e}"

    def run_all(self):
        """Executes all scenarios and prints summary."""
        print("=" * 60)
        print("BATCH REPLIES DIAGNOSTIC TEST")
        print("=" * 60)

        # Scenarios
        scenarios = [
            self.run_scenario_1_discovery,
            self.run_scenario_2_api_call,
            self.run_scenario_3_json_parsing,
        ]

        for scenario in scenarios:
            success, message = scenario()
            name = scenario.__doc__.split(":")[0] if scenario.__doc__ else scenario.__name__
            self.results.append((name, success, message))

        # Summary
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)

        for name, success, message in self.results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"\n{status} - {name}")
            print(f"  {message}")

        # Recommendations
        failed = [res for res in self.results if not res[1]]
        if failed:
            print(f"\n❌ {len(failed)} scenario(s) failed. Check logs above.")
        else:
            print("\n✅ All scenarios passed!")


# --- Entry Point ---


if __name__ == "__main__":
    setup_environment()

    # Import here after setup_environment has modified sys.path
    # This avoids E402 and ImportError
    try:
        from llm import LLMService

        diagnoser = BatchReplyDiagnoser(LLMService)
        diagnoser.run_all()
    except ImportError as e:
        print(f"CRITICAL ERROR: Could not import project modules. {e}")
        print(f"Current sys.path: {sys.path}")
