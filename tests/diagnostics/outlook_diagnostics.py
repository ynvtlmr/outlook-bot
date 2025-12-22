import subprocess
import os
import sys
import time

# Helper to run the specific diagnostic applescript
def run_applescript(test_type, payload=""):
    script_path = os.path.join(os.getcwd(), "src/apple_scripts/diagnostic_test.scpt")
    cmd = ["osascript", script_path, test_type, payload]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"OSASCRIPT_ERROR: {e.stderr}"

def log(test_name, status, details=""):
    print(f"[{status}] {test_name}")
    if details:
        print(f"      Details: {details}")

def run_tests():
    print("="*60)
    print("OUTLOOK DRAFT TRANSCRIPTION DIAGNOSTICS")
    print("="*60)
    
    # TEST 1: Basic Draft Creation
    test_name = "TEST 1: Basic Write/Read"
    payload = "Hello World - Basic Test"
    result = run_applescript("basic", payload)
    
    if payload in result:
        log(test_name, "PASS")
    else:
        log(test_name, "FAIL", f"Expected '{payload}', got '{result}'")

    # TEST 2: Special Characters (Emojis/Unicode)
    test_name = "TEST 2: Special Characters (Unicode)"
    # A mix of emojis and foreign scripts
    payload = "Testing 🚀 Emojis: ✨ and Unicode: 株式会社"
    result = run_applescript("basic", payload)
    
    # AppleScript output might transform unicode, so we check for approximate match or specific failure
    # Often 'result' comes back as bytes or escaped. Python's capture_output=True handles decoding usually.
    if "株式会社" in result and "🚀" in result:
        log(test_name, "PASS")
    else:
        log(test_name, "FAIL", f"Expected '{payload}', got '{result}'")

    # TEST 3: Large Payload (Boundaries)
    test_name = "TEST 3: Large Payload (5000 chars)"
    payload = "A" * 5000
    start_time = time.time()
    result = run_applescript("basic", payload)
    duration = time.time() - start_time
    
    if len(result) == 5000:
        log(test_name, "PASS", f"Write/Read took {duration:.2f}s")
    else:
        log(test_name, "FAIL", f"Expected length 5000, got {len(result)}. First 50 chars: {result[:50]}...")

    # TEST 4: HTML Injection / Tags
    test_name = "TEST 4: HTML/Tag Injection"
    # This mimics what our bot does: appends <br>
    payload = "First Line<br>Second Line"
    result = run_applescript("html", payload)
    
    # If Outlook interprets <br> as newline, checking existence might fail if we expect literal <br>
    # We want to see what actually happens.
    if "First Line" in result and "Second Line" in result:
        log(test_name, "PASS", f"returned: {result}")
    else:
        log(test_name, "FAIL", f"Expected parts of '{payload}', got '{result}'")

    # TEST 5: Read-Back Consistency (Timing)
    test_name = "TEST 5: Rapid Read-Back"
    payload = "Timing Test"
    # The applescript 'readback' mode does set -> read immediately
    result = run_applescript("readback", payload)
    
    if result == payload:
        log(test_name, "PASS", "Immediate read-back matched.")
    else:
        log(test_name, "FAIL", f"Expected '{payload}', got '{result}'")

    # TEST 6: Complex Arguments (Quotes/Newlines)
    test_name = "TEST 6: Complex Arguments (Escaping)"
    # Strings that often break shell or applescript parsing
    payload = 'Text with "double quotes", \'single quotes\', and\nNewlines.'
    result = run_applescript("basic", payload)
    
    # We expect exact match or match with minor normalization?
    # Python subprocess handles the shell escaping, but AppleScript might interpret things.
    if 'Double quotes' in result or '"double quotes"' in result:
        log(test_name, "PASS", "Quotes preserved correctly.")
    else:
        log(test_name, "FAIL", f"Arguments likely mangled. Got: {result}")

    # TEST 7: Append Workflow (Simulate Reply)
    test_name = "TEST 7: Append Workflow (Read-Modify-Write)"
    payload = "My Reply Text"
    result = run_applescript("append", payload)
    
    # We expect "My Reply Text<br>Original Signature" (or similar HTML normalized)
    # The return is the Full Content.
    if "My Reply Text" in result and "Original Signature" in result:
        log(test_name, "PASS", "Append logic succeeded.")
    else:
        log(test_name, "FAIL", f"Append failed. Result: {result}")
        
    print("="*60)

if __name__ == "__main__":
    run_tests()
