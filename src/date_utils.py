import re
from datetime import datetime
try:
    from dateutil import parser
except ImportError:
    import dateutil.parser as parser

def parse_date_string(date_str):
    """
    Parses a single date string with cleaning for common Outlook/macOS oddities.
    Returns datetime object or datetime.min on failure.
    """
    if not date_str:
        return datetime.min
        
    # Clean narrow non-breaking spaces
    clean_str = date_str.replace('\u202F', ' ').strip()
    
    try:
        return parser.parse(clean_str)
    except:
        return datetime.min

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
        dates.append(parse_date_string(match.group(1)))

    for match in pattern2.finditer(text):
        dates.append(parse_date_string(match.group(1)))
            
    # Also check every line that starts with Date:
    for match in pattern4.finditer(text):
        dates.append(parse_date_string(match.group(1)))
                
    # Filter out min dates
    return [d for d in dates if d != datetime.min]

def get_latest_date(text):
    """
    Returns the latest datetime found in the text, or None if none found.
    """
    dates = extract_dates_from_text(text)
    if not dates:
        return None
    return max(dates)
