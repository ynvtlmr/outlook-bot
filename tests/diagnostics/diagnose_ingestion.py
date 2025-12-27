import os
import sys
from datetime import datetime

# Adjust path to import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from date_utils import parse_date_string
from scraper import run_scraper


def log(test_name, status, details=""):
    print(f"[{status}] {test_name}")
    if details:
        print(f"      Details: {details}")


def test_ingestion():
    print("=" * 60)
    print("INGESTION & PARSING DIAGNOSTICS")
    print("=" * 60)

    # TEST 1: Parsing Date Formats (Locale Check)
    test_name = "TEST 1: Date Parsing Logic"
    test_dates = [
        ("Thursday, December 18, 2025 at 12:45:49 PM", 2025, 12, 18),
        ("Dec 18, 2025, at 12:45 PM", 2025, 12, 18),
        # US Format
        ("12/18/2025 12:45 PM", 2025, 12, 18),
        # EU Format (potential failure point if parser assumes US)
        ("18/12/2025 12:45", 2025, 12, 18),
    ]

    date_failures = []
    for d_str, y, m, d in test_dates:
        parsed = parse_date_string(d_str)
        if parsed == datetime.min:
            date_failures.append(f"Failed to parse: {d_str}")
        elif parsed.year != y or parsed.month != m or parsed.day != d:
            # Note: dateutil.parser is smart, but ambiguous cases like 01/02 might flip
            # Here we test unambiguous > 12 days
            date_failures.append(f"Parsed incorrectly: {d_str} -> {parsed}")

    if not date_failures:
        log(test_name, "PASS", "Common date formats parsed correctly.")
    else:
        log(test_name, "WARN", f"Locale issues detected: {date_failures}")

    # TEST 2: Validating Scraper Output
    test_name = "TEST 2: Outlook Flagged Thread Reading"

    # We run the actual scraper but capture output to avoid spam
    # and we limit it or just check return values
    try:
        # We assume run_scraper("flagged") returns a list of threads
        # We need to suppress stdout for cleanliness or just print it?
        # The scraper prints a lot. Let's let it run but maybe catch errors.
        print("      Running Scraper (this may take a few seconds)...")
        # Ensure OUTPUT_DIR exists or scraper does it? Scraper does it.

        # We'll just run it. The user will see the scraper logs mixed in.
        threads = run_scraper(mode="flagged")

        if threads and len(threads) > 0:
            first_thread = threads[0]
            if len(first_thread) > 0:
                msg = first_thread[0]
                if msg.get("subject") and msg.get("content"):
                    log(
                        test_name,
                        "PASS",
                        f"Successfully read {len(threads)} threads. First subject: {msg.get('subject')}",
                    )
                else:
                    log(test_name, "FAIL", "Threads found but missing 'subject' or 'content'. Parsing broken?")
            else:
                log(test_name, "FAIL", "Thread structure found but empty?")
        else:
            # This is NOT a fail if they have no flagged emails, but a "WARN"
            log(test_name, "WARN", "No flagged threads returned. (This is normal if inbox is empty of flags)")

    except Exception as e:
        log(test_name, "FAIL", f"Scraper crashed: {e}")

    print("=" * 60)


if __name__ == "__main__":
    test_ingestion()
