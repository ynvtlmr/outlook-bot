import re
from datetime import datetime
try:
    from dateutil import parser
except ImportError:
    # We should probably handle this more gracefully if we can't install it,
    # but for now we expect it to be there as it was used in previous scripts.
    import dateutil.parser as parser

def extract_dates_from_text(text):
    """
    Finds all date-like strings in the text, especially those following 'Date:' or 'On ...'.
    Returns a list of datetime objects.
    """
    dates = []
    
    # Pattern 1: Outlook verbose format: "Date: Thursday, December 18, 2025 at 12:45:49 PM"
    pattern1 = re.compile(r'Date:\s+([A-Za-z]+,\s+[A-Za-z]+\s+\d+,\s+\d+\s+at\s+\d+:\d+:\d+\s+[APM]+)', re.IGNORECASE)
    
    # Pattern 2: Standard Outlook reply header: "On Dec 18, 2025, at 12:45 PM"
    pattern2 = re.compile(r'On\s+([A-Za-z]+\s+\d+,\s+\d+,\s+at\s+\d+:\d+\s+[APM]+)', re.IGNORECASE)

    # Pattern 3: Simple "Date: ..." line
    pattern3 = re.compile(r'Date:\s+([A-Za-z]+,\s+[A-Za-z]+\s+\d+,\s+\d+\s+.*)', re.IGNORECASE)
    
    # Pattern 4: Generic Date: line
    pattern4 = re.compile(r'^Date:\s+(.*)$', re.MULTILINE | re.IGNORECASE)

    # Try specific patterns first
    for match in pattern1.finditer(text):
        try:
            date_str = match.group(1).replace('\u202F', ' ')
            dates.append(parser.parse(date_str, fuzzy=True))
        except:
            pass

    for match in pattern2.finditer(text):
        try:
            date_str = match.group(1).replace('\u202F', ' ')
            dates.append(parser.parse(date_str, fuzzy=True))
        except:
            pass
            
    # Also check every line that starts with Date:
    for match in pattern4.finditer(text):
        try:
            date_str = match.group(1).strip()
            dates.append(parser.parse(date_str, fuzzy=True))
        except:
            pass
                
    return dates

def get_latest_date(text):
    """
    Returns the latest datetime found in the text, or None if none found.
    """
    dates = extract_dates_from_text(text)
    if not dates:
        return None
    return max(dates)
