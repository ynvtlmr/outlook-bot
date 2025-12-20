import os
import csv
from datetime import datetime, timedelta
from config import DAYS_THRESHOLD, USERS_FILE, APPLESCRIPTS_DIR
from outlook_client import OutlookClient

from scraper import parse_raw_data

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

        # Parse emails to find the latest using unified parser
        messages = parse_raw_data(raw_data)
        last_date = None
        
        valid_dates = [m.get('timestamp') for m in messages if m.get('timestamp') and m.get('timestamp') != datetime.min]
        
        if valid_dates:
            last_date = max(valid_dates)
        
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
