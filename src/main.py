import sys
from client_detector import get_outlook_version
from scraper import run_scraper

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
        run_scraper()
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
