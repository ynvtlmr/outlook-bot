import sys
import os
import time

# Adjust path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from llm import LLMService

def log(test_name, status, details=""):
    print(f"[{status}] {test_name}")
    if details:
        print(f"      Details: {details}")

def test_llm_health():
    print("="*60)
    print("LLM HEALTH & QUOTA DIAGNOSTICS")
    print("="*60)

    # 1. Initialize Service
    try:
        service = LLMService()
    except Exception as e:
        log("LLM Service Init", "FAIL", str(e))
        return

    # 2. Check detected models
    models = service.get_models_list()
    if models:
        log("Model Discovery", "PASS", f"Found {len(models)} models: {', '.join(models[:3])}...")
    else:
        log("Model Discovery", "FAIL", "No models found. Check API Key or Network.")
        return

    # 3. Test Generation (Latency + Quota)
    test_name = "Generation Test"
    prompt = "Reply to: 'Hello, are you there?' with 'Yes, I am working.'"
    
    # We'll try the first available model
    full_prompt = f"System: You are a bot.\n\n{prompt}"
    
    start_time = time.time()
    try:
        # This calls generate_reply which tries ALL models.
        # We want to test if *at least one* works.
        reply = service.generate_reply(prompt, "You are a test bot.")
        duration = time.time() - start_time
        
        if reply:
            log(test_name, "PASS", f"latency={duration:.2f}s. Reply: {reply[:30]}...")
        else:
            log(test_name, "FAIL", "Generation returned empty. Rate limit?")
            
    except Exception as e:
        log(test_name, "FAIL", f"Generation error: {e}")

    print("="*60)

if __name__ == "__main__":
    test_llm_health()
