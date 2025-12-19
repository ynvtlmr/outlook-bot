import sys
from client_detector import get_outlook_version
from scraper import run_scraper

from config import APPLESCRIPTS_DIR
from outlook_client import OutlookClient
import re
from datetime import datetime

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
                # User Requirement: One draft per active thread.
                # Must reply to the LATEST message in the thread, regardless of which one is flagged.
                
                # 1. Check if thread has ANY active flag
                has_active_flag = any(m.get('flag_status') == 'Active' for m in thread)
                
                if not has_active_flag:
                    continue
                    
                # 2. Sort messages by timestamp to find the latest
                # (Scraper adds 'timestamp' datetime object)
                sorted_thread = sorted(thread, key=lambda m: m.get('timestamp', datetime.min))
                
                # 3. Target the very last message
                target_msg = sorted_thread[-1]
                
                msg_id = target_msg.get('message_id')
                subject = target_msg.get('subject', 'No Subject')
                
                if not msg_id:
                    print(f"Skipping thread {i}: No Message ID found for target message.")
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
