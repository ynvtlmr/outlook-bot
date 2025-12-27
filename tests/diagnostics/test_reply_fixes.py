"""
Test script to evaluate different fixes for reply content insertion.
Tests multiple versions of reply_to_message.scpt to find which one works.
"""

import os
import subprocess
import sys
import time
from datetime import datetime

# Add project root to sys.path to import src modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "src"))

from src import scraper  # noqa: E402
from src.config import APPLESCRIPTS_DIR  # noqa: E402


def log(message, level="INFO"):
    """Log a message with timestamp and level."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [{level}] {message}", flush=True)


def get_latest_draft_content():
    """Retrieves the content of the latest draft using our helper script."""
    log("Fetching latest draft content...")
    script_path = os.path.join(APPLESCRIPTS_DIR, "get_latest_draft.scpt")
    cmd = ["osascript", script_path]
    try:
        log(f"Running command: {' '.join(cmd)}")
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
        elapsed = time.time() - start_time
        content = result.stdout.strip()
        log(f"Successfully retrieved draft content (took {elapsed:.2f}s, length: {len(content)} chars)")
        if len(content) > 0:
            log(f"First 100 chars of draft: {content[:100]}...")
        return content
    except subprocess.TimeoutExpired:
        log("Timeout while fetching draft content", "ERROR")
        return ""
    except subprocess.CalledProcessError as e:
        log(f"Error fetching latest draft: {e.stderr}", "ERROR")
        if e.stdout:
            log(f"Script stdout: {e.stdout}", "DEBUG")
        return ""


def verify_script_version(script_name, test_payload, test_name):
    """Test a specific version of the reply script."""
    log(f"\n{'=' * 60}", "TEST")
    log(f"Testing: {test_name}", "TEST")
    log(f"Script: {script_name}", "TEST")
    log(f"{'=' * 60}", "TEST")

    # Find a flagged email
    log("Step 1: Finding flagged email threads...")
    try:
        threads = scraper.run_scraper(mode="flagged")
        log(f"Found {len(threads)} flagged thread(s)")
    except Exception as e:
        log(f"ERROR: Failed to scrape flagged threads: {e}", "ERROR")
        return False, "Scrape failed"

    if not threads:
        log("ERROR: No flagged threads found.", "ERROR")
        return False, "No threads"

    target_thread = threads[0]
    target_msg = target_thread[-1]
    msg_id = target_msg.get("message_id")
    subject = target_msg.get("subject", "Unknown")

    log(f"Selected target: '{subject}' (ID: {msg_id})")

    if not msg_id:
        log("ERROR: Target message has no message ID", "ERROR")
        return False, "No message ID"

    # Check if script exists
    script_path = os.path.join(APPLESCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        log(f"ERROR: Script not found at {script_path}", "ERROR")
        return False, "Script not found"

    log(f"Script exists: {script_path}")
    log(f"Test payload length: {len(test_payload)} chars")
    log(f"Test payload preview: {test_payload[:80]}...")

    # Run the script
    cmd = ["osascript", script_path, str(msg_id), test_payload]
    log("Step 2: Running AppleScript...")
    log(f"Command: {' '.join(cmd[:3])} [payload]")

    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        elapsed = time.time() - start_time
        output = result.stdout.strip()

        log(f"Script execution completed in {elapsed:.2f}s")
        log(f"Script output: {output}")

        if result.stderr:
            log(f"Script stderr: {result.stderr}", "WARN")

        if "Success" not in output:
            log(f"Script returned error: {output}", "ERROR")
            return False, f"Script error: {output}"

        log("Step 3: Waiting for draft to be saved by Outlook...")
        # Wait for draft to save
        for i in range(3):
            time.sleep(1)
            log(f"  Waiting... ({i + 1}/3)")

        log("Step 4: Retrieving draft content...")
        # Check draft content
        draft_content = get_latest_draft_content()

        if not draft_content:
            log("ERROR: Could not retrieve draft content", "ERROR")
            return False, "Could not retrieve draft"

        log(f"Draft content retrieved: {len(draft_content)} chars")

        # Check if our test payload is in the draft
        log("Step 5: Checking if test payload is in draft...")
        import html

        escaped_payload = html.escape(test_payload)

        log("  Checking for original payload...")
        found_original = test_payload in draft_content
        log(f"  Original payload found: {found_original}")

        log("  Checking for HTML-escaped payload...")
        found_escaped = escaped_payload in draft_content
        log(f"  Escaped payload found: {found_escaped}")

        log("  Checking for payload without <br> tags...")
        found_no_br = test_payload.replace("<br>", "") in draft_content.replace("<br>", "")
        log(f"  Payload (no <br>) found: {found_no_br}")

        found = found_original or found_escaped or found_no_br

        if found:
            log("✅ SUCCESS: Test payload found in draft!", "SUCCESS")
            log(f"   Draft length: {len(draft_content)} chars")
            # Save successful draft for inspection
            debug_file = f"output/success_{script_name.replace('.scpt', '')}.html"
            os.makedirs("output", exist_ok=True)
            with open(debug_file, "w") as f:
                f.write(draft_content)
            log(f"   Saved to: {debug_file}")

            # Find where the payload appears
            if found_original:
                idx = draft_content.find(test_payload)
                log(f"   Payload found at position: {idx}")
                log(f"   Context: ...{draft_content[max(0, idx - 20) : idx + len(test_payload) + 20]}...")

            return True, "Content found in draft"
        else:
            log("❌ FAIL: Test payload NOT found in draft", "ERROR")
            log(f"   Draft length: {len(draft_content)} chars")
            log(f"   Looking for: '{test_payload[:50]}...'")

            # Try to find similar text
            log("   Analyzing draft content...")
            if "This is line" in draft_content:
                log("   Found 'This is line' in draft (partial match)")
            if "line 1" in draft_content.lower():
                log("   Found 'line 1' in draft (partial match)")
            if "line 3" in draft_content.lower():
                log("   Found 'line 3' in draft (partial match)")

            # Save failed draft for inspection
            debug_file = f"output/fail_{script_name.replace('.scpt', '')}.html"
            os.makedirs("output", exist_ok=True)
            with open(debug_file, "w") as f:
                f.write(draft_content)
            log(f"   Saved to: {debug_file}")
            return False, "Content not found"

    except subprocess.TimeoutExpired:
        log("Script execution timed out after 30 seconds", "ERROR")
        return False, "Script timeout"
    except Exception as e:
        log(f"Exception during script execution: {str(e)}", "ERROR")
        import traceback

        log(f"Traceback: {traceback.format_exc()}", "DEBUG")
        return False, f"Exception: {str(e)}"


def run_all_tests():
    """Run tests for all script versions."""
    log("=" * 60, "HEADER")
    log("REPLY CONTENT INSERTION FIX EVALUATION", "HEADER")
    log("=" * 60, "HEADER")
    log(f"Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Scripts directory: {APPLESCRIPTS_DIR}")

    # Simple test payload
    test_payload = "This is v6. This is line 1.<br>This is line 2.<br>This is line 3."
    log(f"Test payload: {test_payload}")

    results = []

    # # Test original (for baseline)
    # log("\n" + "="*60, "TEST")
    # log("BASELINE: Original script", "TEST")
    # log("="*60, "TEST")
    # success, message = verify_script_version("reply_to_message.scpt", test_payload, "Original Script")
    # results.append(("Original (baseline)", success, message))

    # if success:
    #     log("⚠️  Original script works! No fix needed.", "WARN")
    #     log("Continuing with other tests for comparison...")

    # # Test v2: html content property + delays
    # log("\n" + "="*60, "TEST")
    # log("Testing Fix v2: html content + delays", "TEST")
    # log("="*60, "TEST")
    # success, msg = verify_script_version("reply_to_message_v2.scpt", test_payload, "Fix v2")
    # results.append(("v2: html content + delays", success, message))

    # # Test v3: Content replacement with verification
    # log("\n" + "="*60, "TEST")
    # log("Testing Fix v3: Content replacement + verification", "TEST")
    # log("="*60, "TEST")
    # success, msg = verify_script_version("reply_to_message_v3.scpt", test_payload, "Fix v3")
    # results.append(("v3: Content replacement + verification", success, message))

    # # Test v4: Plain text approach
    # log("\n" + "="*60, "TEST")
    # log("Testing Fix v4: Plain text approach", "TEST")
    # log("="*60, "TEST")
    # # Convert HTML to plain text for this test
    # plain_text_payload = "This is line 1.\nThis is line 2.\nThis is line 3."
    # log(f"Using plain text payload: {plain_text_payload}")
    # success, msg = verify_script_version("reply_to_message_v4.scpt", plain_text_payload, "Fix v4")
    # results.append(("v4: Plain text approach", success, message))

    # Test v5: UI Automation (keystrokes)
    log("\n" + "=" * 60, "TEST")
    log("Testing Fix v5: UI Automation (keystrokes)", "TEST")
    log("=" * 60, "TEST")
    # Use plain text for UI automation
    plain_text_payload = "This is v5. This is line 1.\nThis is line 2.\nThis is line 3."
    log(f"Using plain text payload for UI automation: {plain_text_payload}")
    success, message = verify_script_version("reply_to_message_v5.scpt", plain_text_payload, "Fix v5: UI Automation")
    results.append(("v5: UI Automation (keystrokes)", success, message))

    # Test v6: Extended delays and retries
    log("\n" + "=" * 60, "TEST")
    log("Testing Fix v6: Extended delays and retries", "TEST")
    log("=" * 60, "TEST")
    success, message = verify_script_version(
        "reply_to_message_v6.scpt", test_payload, "Fix v6: Extended delays + retries"
    )
    results.append(("v6: Extended delays + retries", success, message))

    # Summary
    log("\n" + "=" * 60, "SUMMARY")
    log("TEST RESULTS SUMMARY", "SUMMARY")
    log("=" * 60, "SUMMARY")

    for name, success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        log(f"\n{status} - {name}", "RESULT")
        log(f"  {message}", "RESULT")

    # Recommendations
    log("\n" + "=" * 60, "RECOMMENDATIONS")
    log("RECOMMENDATIONS", "RECOMMENDATIONS")
    log("=" * 60, "RECOMMENDATIONS")

    successful_fixes = [name for name, success, _ in results if success]

    if successful_fixes:
        log(f"\n✅ {len(successful_fixes)} fix(es) succeeded:", "SUCCESS")
        for fix in successful_fixes:
            log(f"   - {fix}", "SUCCESS")
        log("\n📝 Next Steps:", "INFO")
        log("   → Use the first successful fix as the new reply_to_message.scpt", "INFO")
        log("   → Test with actual bot workflow to ensure it works end-to-end", "INFO")
    else:
        log("\n❌ No fixes succeeded. All approaches failed.", "ERROR")
        log("\n📝 Next Steps:", "INFO")
        log("   → Investigate Outlook's content property behavior more deeply", "INFO")
        log("   → Try using UI automation (keystrokes) to insert text", "INFO")
        log("   → Check if there's a different property or method for setting reply body", "INFO")
        log("   → Consider using Outlook's COM/API if available on macOS", "INFO")

    log(f"\nCompleted at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    run_all_tests()
