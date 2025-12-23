"""
Diagnostic script to test why generate_batch_replies returns 0 replies.

Top 3 potential issues:
1. No available models discovered
2. Gemini client not initialized or API call fails
3. JSON parsing failure or response format mismatch
"""
import sys
import os
import json
import traceback
from dotenv import load_dotenv

# Load .env file from project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
env_path = os.path.join(project_root, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
else:
    # Also try loading from default location
    load_dotenv()

# Adjust path to import src modules
sys.path.append(os.path.join(project_root, "src"))

from llm import LLMService


def test_scenario_1_no_models():
    """Test Scenario 1: No available models discovered"""
    print("=" * 60)
    print("SCENARIO 1: Testing No Available Models")
    print("=" * 60)
    
    try:
        service = LLMService()
        
        print(f"\n[Status] Available models count: {len(service.available_models)}")
        print(f"[Status] Available models: {[m['id'] for m in service.available_models]}")
        print(f"[Status] Gemini client initialized: {service.gemini_client is not None}")
        print(f"[Status] OpenAI client initialized: {service.openai_client is not None}")
        
        if not service.available_models:
            print("\n[FAIL] No available models found!")
            print("[Diagnosis] This will cause generate_batch_replies to return {} immediately")
            return False, "No models available"
        else:
            print(f"\n[PASS] Found {len(service.available_models)} models")
            return True, f"Found {len(service.available_models)} models"
            
    except Exception as e:
        print(f"\n[ERROR] Exception during test: {e}")
        traceback.print_exc()
        return False, f"Exception: {str(e)}"


def test_scenario_2_api_call():
    """Test Scenario 2: Gemini client initialization and API call"""
    print("\n" + "=" * 60)
    print("SCENARIO 2: Testing Gemini Client & API Call")
    print("=" * 60)
    
    try:
        service = LLMService()
        
        # Check client initialization
        if not service.gemini_client:
            print("\n[FAIL] Gemini client is not initialized!")
            print("[Diagnosis] This will cause the batch generation to skip Gemini")
            gemini_key = os.getenv("GEMINI_API_KEY")
            if not gemini_key:
                print("[Root Cause] GEMINI_API_KEY not found in environment")
            else:
                print(f"[Root Cause] Client initialization failed despite API key being set")
            return False, "Gemini client not initialized"
        
        print("\n[PASS] Gemini client is initialized")
        
        # Test a simple API call
        if not service.available_models:
            print("[SKIP] No models available to test API call")
            return True, "Client initialized but no models to test"
        
        # Find a Gemini model
        gemini_model = None
        for model in service.available_models:
            if model["provider"] == "gemini":
                gemini_model = model["id"]
                break
        
        if not gemini_model:
            print("[SKIP] No Gemini models in available_models list")
            return True, "Client initialized but no Gemini models found"
        
        print(f"\n[Testing] Attempting API call with model: {gemini_model}")
        
        # Test a minimal API call
        test_prompt = "Say 'test' in JSON format: {\"test\": \"success\"}"
        try:
            response = service.gemini_client.models.generate_content(
                model=gemini_model,
                contents=test_prompt,
                config={"response_mime_type": "application/json"}
            )
            
            if response and response.text:
                print(f"[PASS] API call successful. Response: {response.text[:100]}...")
                return True, "API call successful"
            else:
                print("[FAIL] API call returned empty response")
                return False, "Empty response from API"
                
        except Exception as api_error:
            print(f"\n[FAIL] API call failed: {api_error}")
            print(f"[Error Type] {type(api_error).__name__}")
            traceback.print_exc()
            return False, f"API call failed: {str(api_error)}"
            
    except Exception as e:
        print(f"\n[ERROR] Exception during test: {e}")
        traceback.print_exc()
        return False, f"Exception: {str(e)}"


def test_scenario_3_json_parsing():
    """Test Scenario 3: JSON parsing and response format"""
    print("\n" + "=" * 60)
    print("SCENARIO 3: Testing JSON Parsing & Response Format")
    print("=" * 60)
    
    try:
        service = LLMService()
        
        if not service.available_models:
            print("[SKIP] No models available to test JSON parsing")
            return True, "No models to test"
        
        if not service.gemini_client:
            print("[SKIP] Gemini client not initialized")
            return True, "No client to test"
        
        # Find a Gemini model
        gemini_model = None
        for model in service.available_models:
            if model["provider"] == "gemini":
                gemini_model = model["id"]
                break
        
        if not gemini_model:
            print("[SKIP] No Gemini models available")
            return True, "No Gemini models"
        
        print(f"\n[Testing] Testing batch reply generation with model: {gemini_model}")
        
        # Create a test batch
        test_batch = [
            {"id": "test-123", "subject": "Test Email", "content": "This is a test email content."}
        ]
        test_system_prompt = "You are a helpful assistant."
        
        print(f"[Info] Test batch: {len(test_batch)} email(s)")
        print(f"[Info] System prompt length: {len(test_system_prompt)} chars")
        
        # Call generate_batch_replies
        try:
            results = service.generate_batch_replies(test_batch, test_system_prompt)
            
            print(f"\n[Result] Received {len(results)} replies")
            print(f"[Result] Results: {results}")
            
            if results:
                print("\n[PASS] Batch generation returned results")
                return True, f"Generated {len(results)} replies"
            else:
                print("\n[FAIL] Batch generation returned empty results")
                print("[Diagnosis] This could be due to:")
                print("  - JSON parsing failure")
                print("  - Response format mismatch (not a list of objects with 'id' and 'reply_text')")
                print("  - Exception during generation (check logs above)")
                return False, "Empty results from batch generation"
                
        except Exception as gen_error:
            print(f"\n[FAIL] Exception during batch generation: {gen_error}")
            print(f"[Error Type] {type(gen_error).__name__}")
            traceback.print_exc()
            return False, f"Generation exception: {str(gen_error)}"
            
    except Exception as e:
        print(f"\n[ERROR] Exception during test: {e}")
        traceback.print_exc()
        return False, f"Exception: {str(e)}"


def test_scenario_3b_detailed_json():
    """Test Scenario 3b: Detailed JSON format testing"""
    print("\n" + "=" * 60)
    print("SCENARIO 3b: Testing JSON Response Format in Detail")
    print("=" * 60)
    
    try:
        service = LLMService()
        
        if not service.available_models or not service.gemini_client:
            print("[SKIP] Prerequisites not met")
            return True, "Skipped"
        
        gemini_model = None
        for model in service.available_models:
            if model["provider"] == "gemini":
                gemini_model = model["id"]
                break
        
        if not gemini_model:
            print("[SKIP] No Gemini model")
            return True, "Skipped"
        
        # Test the actual prompt format
        test_batch = [
            {"id": "test-123", "subject": "Test", "content": "Test content"}
        ]
        system_prompt = "You are helpful."
        
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
            {"id": item["id"], "subject": item["subject"], "content": item["content"]} 
            for item in test_batch
        ]
        
        full_json_input = json.dumps(prompt_batch, indent=2)
        full_prompt = prompt_intro + full_json_input
        
        print(f"[Info] Full prompt length: {len(full_prompt)} chars")
        print(f"[Info] Prompt preview (first 200 chars):\n{full_prompt[:200]}...")
        
        # Make the API call
        print(f"\n[Testing] Calling Gemini API...")
        response = service.gemini_client.models.generate_content(
            model=gemini_model,
            contents=full_prompt,
            config={"response_mime_type": "application/json"}
        )
        
        raw_text = response.text if response.text else ""
        print(f"[Result] Raw response length: {len(raw_text)} chars")
        print(f"[Result] Raw response (first 500 chars):\n{raw_text[:500]}")
        
        # Test parsing
        print(f"\n[Testing] Attempting JSON parsing...")
        clean_text = raw_text.strip()
        
        # Clean markdown
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        
        print(f"[Info] Cleaned text length: {len(clean_text)} chars")
        print(f"[Info] Cleaned text:\n{clean_text}")
        
        try:
            parsed_data = json.loads(clean_text)
            print(f"\n[PASS] JSON parsing successful")
            print(f"[Info] Parsed type: {type(parsed_data).__name__}")
            print(f"[Info] Parsed data: {parsed_data}")
            
            # Check format
            if isinstance(parsed_data, list):
                print(f"[PASS] Response is a list (expected format)")
                if len(parsed_data) > 0:
                    first_item = parsed_data[0]
                    if isinstance(first_item, dict):
                        if "id" in first_item and "reply_text" in first_item:
                            print(f"[PASS] First item has correct format (id + reply_text)")
                            return True, "JSON format correct"
                        else:
                            print(f"[FAIL] First item missing required fields")
                            print(f"[Info] First item keys: {list(first_item.keys())}")
                            return False, "Missing required fields in response"
                    else:
                        print(f"[FAIL] First item is not a dict")
                        return False, "Items not dictionaries"
                else:
                    print(f"[FAIL] List is empty")
                    return False, "Empty list returned"
            elif isinstance(parsed_data, dict):
                print(f"[WARN] Response is a dict (not a list as requested)")
                print(f"[Info] Dict keys: {list(parsed_data.keys())}")
                # Check if it's a wrapped format
                values = list(parsed_data.values())
                if values and isinstance(values[0], list):
                    print(f"[INFO] Dict contains a list in values, might be recoverable")
                    return True, "Dict with list (recoverable)"
                else:
                    print(f"[FAIL] Dict format not recoverable")
                    return False, "Dict format not matching expected structure"
            else:
                print(f"[FAIL] Response is neither list nor dict")
                return False, f"Unexpected type: {type(parsed_data).__name__}"
                
        except json.JSONDecodeError as json_error:
            print(f"\n[FAIL] JSON parsing failed: {json_error}")
            print(f"[Error] {json_error.msg} at position {json_error.pos}")
            return False, f"JSON decode error: {str(json_error)}"
            
    except Exception as e:
        print(f"\n[ERROR] Exception during test: {e}")
        traceback.print_exc()
        return False, f"Exception: {str(e)}"


def run_all_tests():
    """Run all diagnostic tests"""
    print("=" * 60)
    print("BATCH REPLIES DIAGNOSTIC TEST")
    print("=" * 60)
    print("\nThis script tests the top 3 reasons why generate_batch_replies")
    print("might return 0 replies:\n")
    print("1. No available models discovered")
    print("2. Gemini client not initialized or API call fails")
    print("3. JSON parsing failure or response format mismatch\n")
    
    results = []
    
    # Test Scenario 1
    success, message = test_scenario_1_no_models()
    results.append(("Scenario 1: No Available Models", success, message))
    
    # Test Scenario 2
    success, message = test_scenario_2_api_call()
    results.append(("Scenario 2: Client & API Call", success, message))
    
    # Test Scenario 3
    success, message = test_scenario_3_json_parsing()
    results.append(("Scenario 3: JSON Parsing", success, message))
    
    # Test Scenario 3b (detailed)
    success, message = test_scenario_3b_detailed_json()
    results.append(("Scenario 3b: Detailed JSON Format", success, message))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for name, success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n{status} - {name}")
        print(f"  {message}")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    failed_scenarios = [name for name, success, _ in results if not success]
    
    if failed_scenarios:
        print(f"\n❌ {len(failed_scenarios)} scenario(s) failed:")
        for scenario in failed_scenarios:
            print(f"   - {scenario}")
        
        print("\n📝 Next Steps:")
        if "Scenario 1" in failed_scenarios[0]:
            print("   → Check API keys are set in environment (.env file)")
            print("   → Verify API keys are valid")
            print("   → Check SSL configuration if behind corporate proxy")
        elif "Scenario 2" in failed_scenarios[0]:
            print("   → Check Gemini API key is valid")
            print("   → Verify SSL/network connectivity")
            print("   → Check API quota/rate limits")
        elif "Scenario 3" in failed_scenarios[0]:
            print("   → Check Gemini response format")
            print("   → Verify JSON parsing logic")
            print("   → May need to adjust prompt or response handling")
    else:
        print("\n✅ All scenarios passed!")
        print("   If you're still getting 0 replies, check:")
        print("   - The actual email batch content")
        print("   - System prompt format")
        print("   - Error logs during batch generation")


if __name__ == "__main__":
    run_all_tests()

