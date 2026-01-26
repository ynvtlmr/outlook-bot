import csv
from datetime import datetime
from typing import Any, Dict, List, Optional

from date_utils import parse_date_string


def parse_csv_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses a CSV file and returns a list of contact dictionaries.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of dictionaries, each representing a contact/row from the CSV
    """
    contacts = []
    
    # Try multiple encodings in order of likelihood
    encodings_to_try = ['utf-8', 'latin-1', 'windows-1252', 'cp1252', 'iso-8859-1', 'utf-8-sig']
    
    last_error = None
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                for row in reader:
                    # Convert all values to strings and strip whitespace
                    # Filter out None keys (from empty columns or trailing delimiters)
                    contact = {}
                    for k, v in row.items():
                        if k is None:
                            continue  # Skip columns with no header (empty columns)
                        key = k.strip() if k else ""
                        value = v.strip() if v else ""
                        if key:  # Only add non-empty keys
                            contact[key] = value
                    contacts.append(contact)
                
                # Success! Return the contacts
                return contacts
                
        except UnicodeDecodeError as e:
            last_error = e
            continue  # Try next encoding
        except Exception as e:
            # Other errors (not encoding-related) - raise immediately
            raise Exception(f"Error parsing CSV file: {e}")
    
    # If we get here, all encodings failed
    raise Exception(f"Error parsing CSV file: Could not decode with any encoding. Last error: {last_error}")
    
    return contacts


def parse_last_activity_date(date_str: str) -> Optional[datetime]:
    """
    Parses the 'Last Activity' field from the CSV.
    Handles various date formats and empty values.
    
    Args:
        date_str: Date string from CSV (e.g., "5/6/2024", "12/23/25", etc.)
        
    Returns:
        datetime object or None if empty/invalid
    """
    if not date_str or date_str.strip() == "":
        return None
    
    try:
        # Try parsing with dateutil (handles many formats)
        return parse_date_string(date_str)
    except Exception:
        # If dateutil fails, try common formats manually
        date_str = date_str.strip()
        
        # Try MM/DD/YYYY or M/D/YYYY
        try:
            parts = date_str.split('/')
            if len(parts) == 3:
                month = int(parts[0])
                day = int(parts[1])
                year = int(parts[2])
                # Handle 2-digit years
                if year < 100:
                    year += 2000 if year < 50 else 1900
                return datetime(year, month, day)
        except (ValueError, IndexError):
            pass
        
        return None


def sort_contacts_by_last_activity(contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sorts contacts by 'Last Activity' field:
    - Contacts with no Last Activity (never contacted) come first
    - Then contacts sorted by oldest Last Activity first
    
    Args:
        contacts: List of contact dictionaries
        
    Returns:
        Sorted list of contacts
    """
    def sort_key(contact: Dict[str, Any]) -> tuple:
        """
        Returns a tuple for sorting:
        - (0, date) for contacts with no Last Activity (prioritized)
        - (1, date) for contacts with Last Activity (sorted by date, oldest first)
        """
        last_activity_str = contact.get('Last Activity', '').strip()
        
        if not last_activity_str:
            # No Last Activity - these should be first
            return (0, datetime.min)
        
        date = parse_last_activity_date(last_activity_str)
        if date is None:
            # Invalid date - treat as no activity
            return (0, datetime.min)
        
        # Has valid date - sort by date (oldest first)
        return (1, date)
    
    return sorted(contacts, key=sort_key)


def get_contact_email(contact: Dict[str, Any]) -> Optional[str]:
    """
    Extracts email address from contact dictionary.
    Tries multiple field names that might contain email.
    
    Args:
        contact: Contact dictionary
        
    Returns:
        Email address string or None
    """
    # Try common email field names
    email_fields = ['eMail', 'Email', 'email', 'Email Address', 'email_address', 'E-mail']
    
    for field in email_fields:
        email = contact.get(field, '').strip()
        if email and '@' in email:
            return email
    
    # Also check if any field contains an email pattern
    for key, value in contact.items():
        if isinstance(value, str) and '@' in value and '.' in value:
            # Simple email pattern check
            parts = value.split('@')
            if len(parts) == 2 and '.' in parts[1]:
                return value.strip()
    
    return None


def format_contact_info_for_prompt(contact: Dict[str, Any]) -> str:
    """
    Formats contact information as a string to be included in the system prompt.
    
    Args:
        contact: Contact dictionary
        
    Returns:
        Formatted string with contact information
    """
    lines = []
    lines.append("Contact Information:")
    
    # Include all fields, but format nicely
    for key, value in contact.items():
        if value and str(value).strip():
            # Skip empty values
            lines.append(f"  {key}: {value}")
    
    return "\n".join(lines)
