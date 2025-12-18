import os
import csv
from datetime import datetime, timedelta
from config import DAYS_THRESHOLD, USERS_FILE, APPLESCRIPTS_DIR
from outlook_client import OutlookClient

# We need a way to parse the dates from the scraped content or re-fetch.
# Since we already have outlook_client methods, we can re-use the parsing logic or abstract it.
# Ideally, we should have a shared utility to parse the email string.

def parse_date(date_str):
    # Outlook AppleScript usually returns date in a locale-dependent format or a standard one.
    # Common format: "Friday, December 18, 2025 at 2:00:00 PM" or similar.
    # This is tricky. Let's assume for now we can rely on standard python date parsing or string comparison
    # If the AppleScript returns a date object, it converts to string.
    # We might need to adjust the AppleScript to return ISO 8601 to be safe.
    # For this MVP, let's try a fuzzy parser or standard formats.
    # Actually, let's update get_emails.scpt to return ISO format if possible, but AppleScript is notoriously bad at that.
    # We'll try dateutil if available, otherwise strict format.
    try:
        from dateutil import parser
        return parser.parse(date_str)
    except ImportError:
        # Fallback: simple exact match if we knew the format, or just return current time (debug)
        print(f"Warning: dateutil not installed. Cannot parse date: {date_str}")
        return datetime.now() 

def check_and_respond():
    client = OutlookClient(APPLESCRIPTS_DIR)
    
    # Load users
    users = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'email' in row:
                    users.append(row)

    print(f"Checking response status for {len(users)} users...")

    for user in users:
        email = user['email']
        name = user.get('name', 'there')
        
        print(f"Processing {email}...")
        raw_data = client.get_emails(email)
        
        if not raw_data:
            print(f"No emails found via AppleScript for {email}. Skipping.")
            continue

        # Parse emails to find the latest
        messages = raw_data.split("///END_OF_EMAIL///")
        last_date = None
        
        for msg in messages:
            if not msg.strip():
                continue
            parts = msg.split("|||")
            if len(parts) >= 3:
                date_str = parts[2].strip()
                # We need to parse this date
                dt = parse_date(date_str)
                if last_date is None or dt > last_date:
                    last_date = dt
        
        if last_date:
            days_diff = (datetime.now() - last_date).days
            print(f"Last contact with {email} was {days_diff} days ago.")
            
            if days_diff > DAYS_THRESHOLD:
                print(f"Threshold ({DAYS_THRESHOLD} days) exceeded. Creating draft.")
                subject = "Catching up"
                content = f"Hi {name},\n\nIt's been a while since we last spoke. I wanted to check in and see how things are going.\n\nBest,\n[Your Name]"
                result = client.create_draft(email, subject, content)
                print(f"Result: {result}")
            else:
                print("No response needed.")
        else:
            print(f"Could not determine last date for {email}.")

if __name__ == "__main__":
    check_and_respond()
