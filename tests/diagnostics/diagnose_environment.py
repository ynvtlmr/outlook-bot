import sys
import os
import yaml

# Adjust path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from outlook_client import get_outlook_version
from config import CONFIG_PATH, OUTPUT_DIR, APPLESCRIPTS_DIR

def log(test_name, status, details=""):
    print(f"[{status}] {test_name}")
    if details:
        print(f"      Details: {details}")

def test_environment():
    print("="*60)
    print("ENVIRONMENT & CONFIG DIAGNOSTICS")
    print("="*60)

    # TEST 1: Outlook Detection
    test_name = "Outlook Detection"
    version = get_outlook_version()
    if version:
        log(test_name, "PASS", f"Found Version: {version}")
        # Identify "New Outlook" if possible? usually version > 16... but 'New Outlook' returns different string?
        # Actually New Outlook lacks applescript support, so get_version might failing or return specific text?
        # If it returns, it's usually good.
    else:
        log(test_name, "FAIL", "Could not detect Outlook. Is it running?")

    # TEST 2: Config Validity
    test_name = "Config Check"
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                log(test_name, "PASS", "config.yaml is valid.")
            else:
                log(test_name, "FAIL", "config.yaml is not a dictionary.")
        except Exception as e:
            log(test_name, "FAIL", f"Invalid YAML: {e}")
    else:
        log(test_name, "WARN", "config.yaml missing (using defaults).")

    # TEST 3: Disk Write Permissions
    test_name = "Disk Write (Output)"
    try:
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        
        test_file = os.path.join(OUTPUT_DIR, "write_test.tmp")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        log(test_name, "PASS", f"Writable: {OUTPUT_DIR}")
    except Exception as e:
        log(test_name, "FAIL", f"Cannot write to output dir: {e}")

    # TEST 4: AppleScripts Presence
    test_name = "AppleScripts Check"
    required_scripts = ["get_flagged_threads.scpt", "reply_to_message.scpt"]
    missing = []
    for s in required_scripts:
        if not os.path.exists(os.path.join(APPLESCRIPTS_DIR, s)):
            missing.append(s)
            
    if not missing:
        log(test_name, "PASS", "All core AppleScripts found.")
    else:
        log(test_name, "FAIL", f"Missing scripts: {missing}")

    print("="*60)

if __name__ == "__main__":
    test_environment()
