import os
import re
from datetime import datetime
from config import OUTPUT_DIR, APPLESCRIPTS_DIR
from outlook_client import OutlookClient

def parse_raw_data(raw_data):
    """
    Parses the raw string from AppleScript into a list of message dicts.
    """
    messages = []
    # Split by message delimiter (added regex for robustness against newline variations)
    raw_msgs = raw_data.split("\n///END_OF_MESSAGE///\n")
    
    for raw_msg in raw_msgs:
        if not raw_msg.strip():
            continue
            
        msg = {}
        # Simple parsing logic
        
        lines = raw_msg.splitlines()
        content_lines = []
        in_body = False
        
        for line in lines:
            if line.strip() == "---BODY_START---":
                in_body = True
                continue
            if line.strip() == "---BODY_END---":
                in_body = False
                continue
                
            if in_body:
                content_lines.append(line)
            else:
                if line.startswith("ID: "):
                    msg['id'] = line[4:].strip()
                elif line.startswith("From: "):
                    msg['from'] = line[6:].strip()
                elif line.startswith("Date: "):
                    msg['date'] = line[6:].strip()
                elif line.startswith("Subject: "):
                    msg['subject'] = line[9:].strip()
        
        msg['content'] = "\n".join(content_lines)
        
        # Fallback for subject grouping if ID is missing or generic
        if not msg.get('id') or msg.get('id') == "NO_ID":
            # Normalize subject (remove Re:, Fwd:)
            subj = msg.get('subject', 'No Subject')
            norm_subj = re.sub(r'^(Re|Fwd|FW|RE):\s*', '', subj, flags=re.IGNORECASE).strip()
            msg['id'] = norm_subj
            
        messages.append(msg)
    return messages

def group_into_threads(messages):
    """
    Groups messages by their ID (conversation ID or Subject).
    Returns a list of threads (lists of messages).
    """
    threads_map = {}
    for msg in messages:
        t_id = msg.get('id')
        if t_id not in threads_map:
            threads_map[t_id] = []
        threads_map[t_id].append(msg)
        
    return list(threads_map.values())

def run_scraper():
    client = OutlookClient(APPLESCRIPTS_DIR)
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print("Fetching recent emails from Outlook...")
    # We call the new script manually here since it's not in the old client wrapper yet
    # Or we can just use the _run_script method.
    raw_data = client._run_script('get_recent_threads.scpt')
    
    if not raw_data:
        print("No data returned from Outlook.")
        return

    messages = parse_raw_data(raw_data)
    print(f"Parsed {len(messages)} messages.")
    
    threads = group_into_threads(messages)
    print(f"Identified {len(threads)} unique threads.")
    
    # Sort threads by most recent message in them?
    # For now, let's just take the first 10 encountered (since we scraped from newest)
    # Ideally we sort by the date of the newest message in the thread.
    
    # Limit to 10
    top_threads = threads[:10]
    
    for i, thread in enumerate(top_threads):
        # Determine filename from subject of the first message
        first_msg = thread[0]
        safe_subject = "".join([c for c in first_msg.get('subject', 'thread') if c.isalnum() or c in (' ', '-', '_')]).strip()[:50]
        filename = f"thread_{i+1}_{safe_subject}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for msg in thread:
                f.write(f"From: {msg.get('from')}\n")
                f.write(f"Date: {msg.get('date')}\n")
                f.write(f"Subject: {msg.get('subject')}\n")
                f.write("-" * 20 + "\n")
                f.write(msg.get('content') + "\n")
                f.write("=" * 80 + "\n\n")
        
    print(f"Successfully saved {len(top_threads)} threads to {OUTPUT_DIR}")
