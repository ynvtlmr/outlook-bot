import sys
from client_detector import get_outlook_version
from scraper import run_scraper

from config import APPLESCRIPTS_DIR
from outlook_client import OutlookClient
import re

def main():
    print("--- Outlook Bot Generic Scraper ---")
    
    # 1. Detect Client
    version = get_outlook_version()
    if version:
        print(f"Target Client: Microsoft Outlook {version}")
    else:
        print("Warning: Could not detect Outlook version. Is it running?")
    
    print("-" * 30)
    
    # 2. Scrape Threads
    try:
        # Run both modes to cover all bases
        # run_scraper(mode='recent')
        print("\n" + "="*30 + "\n")
        
        # Scrape flagged and get results
        flagged_threads = run_scraper(mode='flagged')
        
        # 3. Auto-Response Logic
        if flagged_threads:
            print("\n--- Processing Active Flags ---")
            client = OutlookClient(APPLESCRIPTS_DIR)
            
            for i, thread in enumerate(flagged_threads):
                # Deduplication: Find the LATEST message with 'Active' flag
                # Threads are typically chronological or reverse chronological depending on Outlook. 
                # Let's assume we want to reply to the *latest* message in the conversation that is flagged,
                # OR the *latest* message in the conversation period, using the context of the flag?
                # User Requirement: "one draft per flagged active email thread"
                
                active_msgs = [m for m in thread if m.get('flag_status') == 'Active']
                
                if not active_msgs:
                    continue
                    
                # If multiple active flags, pick the one with most recent date?
                # Parser date format is tricky. Let's rely on position if sorted? 
                # Actually, scraper preserves order. Let's pick the last one in the list (assuming chronological) 
                # or first (assuming reverse).
                # Scraper output appends messages. `get_flagged_threads` loops folders. Order is not guaranteed absolute time.
                # However, usually we want to reply to the specific message that IS flagged. 
                # If multiple are flagged, we process the latest one found.
                
                target_msg = active_msgs[-1] # Pick the last one found
                
                msg_id = target_msg.get('message_id')
                subject = target_msg.get('subject', 'No Subject')
                
                if not msg_id:
                    print(f"Skipping thread {i}: No Message ID found for active flag.")
                    continue
                    
                print(f"Drafting reply for Thread {i+1}: {subject} (ID: {msg_id})")
                
                draft_body = (
                    f"Hi,\n\n"
                    f"I am following up on your email regarding '{subject}'.\n\n"
                    f"Best,\n[Your Name]"
                )
                
                try:
                    result = client.reply_to_message(msg_id, draft_body)
                    print(f"  -> {result}")
                except Exception as e:
                    print(f"  -> Failed to create draft: {e}")
                            
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
