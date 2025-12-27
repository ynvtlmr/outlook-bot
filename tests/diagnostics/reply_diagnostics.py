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
from src.outlook_client import OutlookClient  # noqa: E402


def log_msg(message, level="INFO"):
    """Log a message with timestamp and level."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [{level}] {message}", flush=True)


def get_latest_draft_content(client):
    """Retrieves the content of the latest draft using our helper script."""
    log_msg("Fetching latest draft content...")
    # We call the script directly using osascript as it is a new helper
    script_path = os.path.join(APPLESCRIPTS_DIR, "get_latest_draft.scpt")
    cmd = ["osascript", script_path]
    log_msg(f"Running command: {' '.join(cmd)}")
    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
        elapsed = time.time() - start_time
        content = result.stdout.strip()
        log_msg(f"Successfully retrieved draft content (took {elapsed:.2f}s, length: {len(content)} chars)")
        if len(content) > 0:
            log_msg(f"First 150 chars: {content[:150]}...")
        return content
    except subprocess.TimeoutExpired:
        log_msg("Timeout while fetching draft content", "ERROR")
        return ""
    except subprocess.CalledProcessError as e:
        log_msg(f"Error fetching latest draft: {e.stderr}", "ERROR")
        if e.stdout:
            log_msg(f"Script stdout: {e.stdout}", "DEBUG")
        return ""


def log(test_name, status, details=""):
    """Log test result with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [{status}] {test_name}", flush=True)
    if details:
        print(f"      Details: {details}", flush=True)


def run_diagnostics():
    log_msg("=" * 60, "HEADER")
    log_msg("OUTLOOK REPLY-ALL INJECTION DIAGNOSTICS", "HEADER")
    log_msg("=" * 60, "HEADER")
    log_msg(f"Starting diagnostics at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_msg(f"Scripts directory: {APPLESCRIPTS_DIR}")

    # 1. SETUP: Find a flagged email thread
    log_msg("Step 1: Looking for flagged emails to use as test targets...")
    try:
        # We reuse the scraper logic to ensure we are testing "the same way"
        log_msg("Running scraper to find flagged threads...")
        start_time = time.time()
        threads = scraper.run_scraper(mode="flagged")
        elapsed = time.time() - start_time
        log_msg(f"Scraper completed in {elapsed:.2f}s, found {len(threads)} thread(s)")
    except Exception as e:
        log_msg(f"CRITICAL ERROR: Failed to scrape flagged threads: {e}", "ERROR")
        import traceback

        log_msg(f"Traceback: {traceback.format_exc()}", "DEBUG")
        return

    if not threads:
        log_msg(
            "CRITICAL ERROR: No flagged threads found. Please flag at least one email in Outlook and try again.",
            "ERROR",
        )
        return

    # Use the first thread found
    target_thread = threads[0]
    log_msg(f"Selected thread with {len(target_thread)} message(s)")
    # Use the last message in that thread (latest)
    # Sorting by timestamp handled in main.py usually, but scraper returns list.
    # We'll just take the last one in the list as a best guess for 'latest' or 'target'
    target_msg = target_thread[-1]
    msg_id = target_msg.get("message_id")
    subject = target_msg.get("subject", "Unknown Subject")

    log_msg(f"Target selected: '{subject}'")
    log_msg(f"Target Message ID: {msg_id}")
    log_msg("-" * 60)

    if not msg_id:
        log_msg("CRITICAL ERROR: Target message has no Message ID.", "ERROR")
        return

    log_msg("Initializing OutlookClient...")
    client = OutlookClient(APPLESCRIPTS_DIR)
    log_msg("OutlookClient initialized")

    # TEST SUITE

    # CASE 1: Multiline Text
    test_name = "TEST 1: Multiline Injection"
    log_msg(f"\n{'=' * 60}", "TEST")
    log_msg(f"Running {test_name}...", "TEST")
    log_msg(f"{'=' * 60}", "TEST")

    payload = "This is line 1.\nThis is line 2.\nThis is line 3."
    log_msg(f"Original payload: {payload}")

    # Inject
    # Note: main.py does: html.escape(reply_text).replace("\n", "<br>")
    # We should replicate that preprocessing if we want to confirm the *whole pipeline*
    # OR test raw injection to see if AppleScript handles it.
    # The user asked to "inject this text... into a reply all draft".
    # Our AppleScript expects HTML-ish for breaks if we want them rendered, or just raw text.
    # Let's use the exact transformation main.py uses, as that is "the same way our script currently attempts to do".

    import html

    formatted_payload = html.escape(payload).replace("\n", "<br>")
    log_msg(f"Formatted payload (HTML): {formatted_payload}")
    log_msg(f"Payload length: {len(formatted_payload)} chars")

    log_msg("Calling reply_to_message...")
    start_time = time.time()
    result = client.reply_to_message(msg_id, formatted_payload)
    elapsed = time.time() - start_time
    log_msg(f"reply_to_message completed in {elapsed:.2f}s")
    log_msg(f"Result: {result}")

    if result is None or "Success" not in result:
        log(test_name, "FAIL", f"AppleScript error: {result}")
    else:
        log_msg("AppleScript reported success, waiting for draft to save/sync...")
        # Wait for draft to save/sync
        for i in range(2):
            time.sleep(1)
            log_msg(f"  Waiting... ({i + 1}/2)")

        log_msg("Retrieving draft content...")
        draft_content = get_latest_draft_content(client)

        log_msg("Verifying content...")
        # Verify
        found_line1 = "This is line 1." in draft_content
        found_line3 = "This is line 3." in draft_content
        log_msg(f"  'This is line 1.' found: {found_line1}")
        log_msg(f"  'This is line 3.' found: {found_line3}")

        if found_line1 and found_line3:
            log(test_name, "PASS")
        else:
            debug_file = "output/debug_fail_test_1.html"
            os.makedirs("output", exist_ok=True)
            with open(debug_file, "w") as f:
                f.write(draft_content)
            log_msg(f"Saved draft content to {debug_file}")
            log(test_name, "FAIL", f"Content mismatch. Saved to {debug_file}")

    log_msg("-" * 30)

    # CASE 2: Unicode / Emojis
    test_name = "TEST 2: Unicode/Emoji Injection"
    log_msg(f"\n{'=' * 60}", "TEST")
    log_msg(f"Running {test_name}...", "TEST")
    log_msg(f"{'=' * 60}", "TEST")

    payload_uni = "Testing Emojis: 🤖 ✅ 🚀"
    log_msg(f"Original payload: {payload_uni}")
    formatted_uni = html.escape(payload_uni).replace("\n", "<br>")
    log_msg(f"Formatted payload: {formatted_uni}")
    log_msg(f"Payload length: {len(formatted_uni)} chars")

    log_msg("Calling reply_to_message...")
    start_time = time.time()
    result = client.reply_to_message(msg_id, formatted_uni)
    elapsed = time.time() - start_time
    log_msg(f"reply_to_message completed in {elapsed:.2f}s")
    log_msg(f"Result: {result}")

    if result is None or "Success" not in result:
        log(test_name, "FAIL", f"AppleScript error: {result}")
    else:
        log_msg("AppleScript reported success, waiting for draft to save/sync...")
        for i in range(2):
            time.sleep(1)
            log_msg(f"  Waiting... ({i + 1}/2)")

        log_msg("Retrieving draft content...")
        draft_content = get_latest_draft_content(client)

        log_msg("Verifying emojis...")
        found_robot = "🤖" in draft_content
        found_rocket = "🚀" in draft_content
        log_msg(f"  '🤖' found: {found_robot}")
        log_msg(f"  '🚀' found: {found_rocket}")

        if found_robot and found_rocket:
            log(test_name, "PASS")
        else:
            debug_file = "output/debug_fail_test_2.html"
            os.makedirs("output", exist_ok=True)
            with open(debug_file, "w") as f:
                f.write(draft_content)
            log_msg(f"Saved draft content to {debug_file}")
            log(test_name, "FAIL", f"Content mismatch. Saved to {debug_file}")

    log_msg("-" * 30)

    # CASE 3: Large Block
    test_name = "TEST 3: Large Payload Injection (2KB)"
    log_msg(f"\n{'=' * 60}", "TEST")
    log_msg(f"Running {test_name}...", "TEST")
    log_msg(f"{'=' * 60}", "TEST")

    payload_large = "Repeat " * 300  # ~2100 chars
    log_msg(f"Original payload length: {len(payload_large)} chars")
    log_msg(f"First 50 chars: {payload_large[:50]}...")
    formatted_large = html.escape(payload_large)
    log_msg(f"Formatted payload length: {len(formatted_large)} chars")

    log_msg("Calling reply_to_message...")
    start_time = time.time()
    result = client.reply_to_message(msg_id, formatted_large)
    elapsed = time.time() - start_time
    log_msg(f"reply_to_message completed in {elapsed:.2f}s")
    log_msg(f"Result: {result}")

    if result is None or "Success" not in result:
        log(test_name, "FAIL", f"AppleScript error: {result}")
    else:
        log_msg("AppleScript reported success, waiting for draft to save/sync...")
        for i in range(2):
            time.sleep(1)
            log_msg(f"  Waiting... ({i + 1}/2)")

        log_msg("Retrieving draft content...")
        draft_content = get_latest_draft_content(client)

        log_msg("Verifying large payload...")
        log_msg(f"  Draft content length: {len(draft_content)} chars")
        found_repeat = "Repeat Repeat" in draft_content
        log_msg(f"  'Repeat Repeat' found: {found_repeat}")

        # Check for significant length and content
        if len(draft_content) > 1000 and found_repeat:
            log(test_name, "PASS")
        else:
            log_msg("  Expected: >1000 chars and 'Repeat Repeat'")
            log_msg(f"  Got: {len(draft_content)} chars, 'Repeat Repeat'={found_repeat}")
            log(test_name, "FAIL", f"Content truncated? Len: {len(draft_content)}")

    log_msg("=" * 60)
    log_msg("Diagnostics functionality complete. Check 'Drafts' folder in Outlook to visually confirm.")
    log_msg(f"Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    run_diagnostics()
