import sys
import os
import time
import subprocess

# Add project root to sys.path to import src modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "src"))

from src import scraper
from src.outlook_client import OutlookClient
from src.config import APPLESCRIPTS_DIR

def get_latest_draft_content(client):
    """Retrieves the content of the latest draft using our helper script."""
    # We call the script directly using osascript as it is a new helper
    script_path = os.path.join(APPLESCRIPTS_DIR, "get_latest_draft.scpt")
    cmd = ["osascript", script_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error fetching latest draft: {e.stderr}")
        return ""

def log(test_name, status, details=""):
    print(f"[{status}] {test_name}")
    if details:
        print(f"      Details: {details}")

def run_diagnostics():
    print("="*60)
    print("OUTLOOK REPLY-ALL INJECTION DIAGNOSTICS")
    print("="*60)

    # 1. SETUP: Find a flagged email thread
    print("Looking for flagged emails to use as test targets...")
    try:
        # We reuse the scraper logic to ensure we are testing "the same way"
        threads = scraper.run_scraper(mode="flagged")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to scrape flagged threads: {e}")
        return

    if not threads:
        print("CRITICAL ERROR: No flagged threads found. Please flag at least one email in Outlook and try again.")
        return

    # Use the first thread found
    target_thread = threads[0]
    # Use the last message in that thread (latest)
    # Sorting by timestamp handled in main.py usually, but scraper returns list.
    # We'll just take the last one in the list as a best guess for 'latest' or 'target'
    target_msg = target_thread[-1]
    msg_id = target_msg.get("message_id")
    subject = target_msg.get("subject", "Unknown Subject")

    print(f"Target selected: '{subject}'")
    print(f"Target Message ID: {msg_id}")
    print("-" * 60)

    if not msg_id:
        print("CRITICAL ERROR: Target message has no Message ID.")
        return

    client = OutlookClient(APPLESCRIPTS_DIR)

    # TEST SUITE
    
    # CASE 1: Multiline Text
    test_name = "TEST 1: Multiline Injection"
    payload = "This is line 1.\nThis is line 2.\nThis is line 3."
    
    print(f"Running {test_name}...")
    # Inject
    # Note: main.py does: html.escape(reply_text).replace("\n", "<br>")
    # We should replicate that preprocessing if we want to confirm the *whole pipeline* 
    # OR test raw injection to see if AppleScript handles it.
    # The user asked to "inject this text... into a reply all draft". 
    # Our AppleScript expects HTML-ish for breaks if we want them rendered, or just raw text.
    # Let's use the exact transformation main.py uses, as that is "the same way our script currently attempts to do".
    
    import html
    formatted_payload = html.escape(payload).replace("\n", "<br>")
    
    result = client.reply_to_message(msg_id, formatted_payload)
    if "Success" not in result:
         log(test_name, "FAIL", f"AppleScript error: {result}")
    else:
        # Wait for draft to save/sync
        time.sleep(2)
        draft_content = get_latest_draft_content(client)
        
        # Verify
        if "This is line 1." in draft_content and "This is line 3." in draft_content:
             log(test_name, "PASS")
        else:
             debug_file = "output/debug_fail_test_1.html"
             with open(debug_file, "w") as f:
                 f.write(draft_content)
             log(test_name, "FAIL", f"Content mismatch. Saved to {debug_file}")

    print("-" * 30)

    # CASE 2: Unicode / Emojis
    test_name = "TEST 2: Unicode/Emoji Injection"
    payload_uni = "Testing Emojis: 🤖 ✅ 🚀"
    formatted_uni = html.escape(payload_uni).replace("\n", "<br>")
    
    print(f"Running {test_name}...")
    result = client.reply_to_message(msg_id, formatted_uni)
    
    if "Success" not in result:
         log(test_name, "FAIL", f"AppleScript error: {result}")
    else:
        time.sleep(2)
        draft_content = get_latest_draft_content(client)
        if "🤖" in draft_content and "🚀" in draft_content:
             log(test_name, "PASS")
        else:
             debug_file = "output/debug_fail_test_2.html"
             with open(debug_file, "w") as f:
                 f.write(draft_content)
             log(test_name, "FAIL", f"Content mismatch. Saved to {debug_file}")

    print("-" * 30)

    # CASE 3: Large Block
    test_name = "TEST 3: Large Payload Injection (2KB)"
    payload_large = "Repeat " * 300 # ~2100 chars
    formatted_large = html.escape(payload_large)
    
    print(f"Running {test_name}...")
    result = client.reply_to_message(msg_id, formatted_large)
    
    if "Success" not in result:
         log(test_name, "FAIL", f"AppleScript error: {result}")
    else:
        time.sleep(2)
        draft_content = get_latest_draft_content(client)
        # Check for significant length and content
        if len(draft_content) > 1000 and "Repeat Repeat" in draft_content:
             log(test_name, "PASS")
        else:
             log(test_name, "FAIL", f"Content truncated? Len: {len(draft_content)}")

    print("="*60)
    print("Diagnostics functionality complete. Check 'Drafts' folder in Outlook to visually confirm.")

if __name__ == "__main__":
    run_diagnostics()
