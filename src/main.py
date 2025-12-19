import sys
from outlook_client import OutlookClient, get_outlook_version
from scraper import run_scraper

from config import APPLESCRIPTS_DIR, DAYS_THRESHOLD
from date_utils import get_latest_date

import re
from datetime import datetime, timedelta

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
                
                subject = thread[0].get('subject', 'No Subject')
                print(f"\nAnalyzing Thread {i+1}: {subject}")
                
                # 2. Find the TRULY latest activity date by looking at all message headers AND bodies
                all_dates = []
                for m in thread:
                    if m.get('timestamp') and m.get('timestamp') != datetime.min:
                        all_dates.append(m.get('timestamp'))
                    
                    # Search buried dates in content
                    buried_date = get_latest_date(m.get('content', ''))
                    if buried_date:
                        all_dates.append(buried_date)
                
                if not all_dates:
                    print(f"  -> Warning: Could not determine any activity date. Skipping.")
                    continue
                    
                latest_activity = max(all_dates)
                days_ago = (datetime.now() - latest_activity).days
                
                print(f"  -> Latest activity: {latest_activity.strftime('%Y-%m-%d %H:%M:%S')} ({days_ago} days ago)")
                
                # 3. Apply 7-day threshold
                if days_ago <= DAYS_THRESHOLD:
                    print(f"  -> Activity within {DAYS_THRESHOLD} days. No reply needed yet.")
                    continue
                
                print(f"  -> No activity for > {DAYS_THRESHOLD} days. Proceeding with draft.")

                # 4. Sort messages by timestamp to find the best target message for the reply
                sorted_thread = sorted(thread, key=lambda m: m.get('timestamp', datetime.min))
                target_msg = sorted_thread[-1]
                
                msg_id = target_msg.get('message_id')
                
                if not msg_id:
                    print(f"  -> Error: No Message ID found for target message.")
                    continue
                    
                try:
                    result = client.reply_to_message(msg_id)
                    print(f"  -> {result}")
                except Exception as e:
                    print(f"  -> Failed to create draft: {e}")
                            
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
