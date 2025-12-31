"""
Automatic Email Signature Detection and Removal

This module provides comprehensive signature stripping using multiple heuristics:
- Pattern-based detection (legal disclaimers, office locations, social media)
- Repetition detection (text appearing in multiple messages)
- Position-based heuristics (text near end of messages)
- Length-based filtering (long repetitive blocks)
"""
import re
from typing import Optional


def strip_signatures(content: str, thread_context: Optional[list[dict]] = None) -> str:
    """
    Automatically detects and removes signatures from email content.
    
    Args:
        content: Single message content string
        thread_context: Optional list of all messages in thread for repetition detection
        
    Returns:
        Content with signatures removed
    """
    if not content or not content.strip():
        return content
    
    cleaned = content
    
    # Apply detection strategies in order
    # 1. Legal disclaimer patterns
    cleaned = _strip_legal_disclaimers(cleaned)
    
    # 2. Office location patterns
    cleaned = _strip_office_locations(cleaned)
    
    # 3. Social media patterns
    cleaned = _strip_social_media(cleaned)
    
    # 4. Common footer markers
    cleaned = _strip_common_footers(cleaned)
    
    # 5. Repetition detection (if thread context available)
    if thread_context:
        cleaned = _strip_repetitive_content(cleaned, thread_context)
    
    # 6. Position-based removal (text near end that matches signature patterns)
    cleaned = _strip_position_based_signatures(cleaned)
    
    return cleaned.strip()


def _strip_legal_disclaimers(content: str) -> str:
    """Remove common legal disclaimers and confidentiality notices."""
    patterns = [
        # Gen II style notice
        r'NOTICE:\s*Unless otherwise stated.*?(?:which can be found here|privacy policy|privacy notice).*?',
        # Confidential/legally privileged notices
        r'(?:CONFIDENTIAL|LEGALLY PRIVILEGED|PRIVILEGED AND CONFIDENTIAL).*?'
        r'(?:delete.*?material|return.*?immediately|notify.*?immediately).*?',
        # Virus warnings
        r'Although.*?virus.*?free.*?no responsibility.*?accepted.*?',
        # Privacy policy references
        r'Please note.*?personal data.*?privacy (?:notice|policy).*?',
        # General legal disclaimer patterns
        r'This (?:email|message|communication).*?confidential.*?intended recipient.*?',
        r'If you are not the intended recipient.*?strictly prohibited.*?',
        r'This information is only for the use of.*?intended recipient.*?',
    ]
    
    cleaned = content
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    
    return cleaned


def _strip_office_locations(content: str) -> str:
    """Remove office location lists (e.g., "City | City | City" or "City, State | City, State")."""
    # Pattern for location lists with pipes or commas
    # Matches: "New York | Boston | Stamford" or "New York, NY | Boston, MA"
    location_pattern = r'^[A-Z][a-zA-Z\s,]+(?:\s*\|\s*[A-Z][a-zA-Z\s,]+){2,}.*?$'
    
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        # Check if line matches location pattern
        if re.match(location_pattern, line_stripped):
            # Also check for common location indicators
            if '|' in line_stripped or (',' in line_stripped and any(
                word in line_stripped.lower() for word in ['new york', 'boston', 'san francisco', 'dallas', 'denver', 'london', 'luxembourg']
            )):
                continue  # Skip this line
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def _strip_social_media(content: str) -> str:
    """Remove social media links and mentions."""
    # Pattern for social media mentions with links
    # Matches: "Instagram | LinkedIn | Twitter | Facebook" with optional links
    social_patterns = [
        r'(?:Instagram|LinkedIn|Twitter|Facebook|X|YouTube)\s*[<\[].*?[>\]]',
        r'(?:Instagram|LinkedIn|Twitter|Facebook|X|YouTube)\s*:\s*https?://[^\s]+',
        # Pattern for multiple social media in one line
        r'(?:Instagram|LinkedIn|Twitter|Facebook|X|YouTube)(?:\s*[<\[].*?[>\]]|\s*\|)*',
    ]
    
    cleaned = content
    for pattern in social_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Also remove lines that are primarily social media links
    lines = cleaned.split('\n')
    cleaned_lines = []
    for line in lines:
        line_lower = line.lower()
        # If line contains multiple social media mentions, likely a signature line
        social_count = sum(1 for platform in ['instagram', 'linkedin', 'twitter', 'facebook', 'youtube'] 
                          if platform in line_lower)
        if social_count >= 2:
            continue  # Skip this line
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def _strip_common_footers(content: str) -> str:
    """Remove common footer text and taglines."""
    footer_patterns = [
        r'Well-run funds.*?powered by.*?',
        r'Powered by.*?',
        r'This email was sent.*?',
        r'You are receiving this email.*?',
        r'To unsubscribe.*?',
    ]
    
    cleaned = content
    for pattern in footer_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove lines that are common taglines
    taglines = [
        'well-run funds powered by',
        'powered by gen ii',
    ]
    
    lines = cleaned.split('\n')
    cleaned_lines = []
    for line in lines:
        line_lower = line.strip().lower()
        if any(tagline in line_lower for tagline in taglines):
            continue
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def _strip_repetitive_content(content: str, thread_context: list[dict]) -> str:
    """
    Remove text blocks that appear in multiple messages (likely signatures).
    Compares normalized text blocks across messages.
    """
    if not thread_context or len(thread_context) < 2:
        return content
    
    # Extract all message contents
    all_contents = [msg.get('content', '') for msg in thread_context if msg.get('content')]
    
    if len(all_contents) < 2:
        return content
    
    # Normalize content for comparison (lowercase, normalize whitespace)
    def normalize_text(text: str) -> str:
        return re.sub(r'\s+', ' ', text.lower().strip())
    
    # Find common blocks (signatures) by comparing consecutive messages
    # Look for blocks at the end of messages that are similar
    content_normalized = normalize_text(content)
    
    # Check if end portion of this content appears in other messages
    # Take last 30% of content and see if it's repeated
    content_length = len(content)
    if content_length < 100:  # Too short to have meaningful signature
        return content
    
    # Check last portion against other messages
    last_portion_start = int(content_length * 0.7)
    last_portion = normalize_text(content[last_portion_start:])
    
    # If this last portion appears in multiple other messages, it's likely a signature
    matches = 0
    for other_content in all_contents:
        if other_content == content:  # Skip self
            continue
        other_normalized = normalize_text(other_content)
        if last_portion and len(last_portion) > 50:  # Only check substantial blocks
            if last_portion in other_normalized:
                matches += 1
    
    # If the last portion appears in 2+ other messages, remove it
    if matches >= 2:
        return content[:last_portion_start].rstrip()
    
    return content


def _strip_position_based_signatures(content: str) -> str:
    """
    Remove signature-like content near the end of messages based on position and patterns.
    """
    if not content or len(content) < 100:
        return content
    
    lines = content.split('\n')
    if len(lines) < 3:
        return content
    
    # Look at the last 30-40% of lines
    start_check = max(0, int(len(lines) * 0.6))
    lines_to_check = lines[start_check:]
    
    # Patterns that indicate signature blocks
    signature_indicators = [
        r'^[-_=]{3,}',  # Separator lines
        r'^NOTICE:',  # Legal notices
        r'^CONFIDENTIAL',  # Confidential markers
        r'^\w+\s*\|\s*\w+',  # Pipe-separated items (locations, social)
        r'Instagram|LinkedIn|Twitter|Facebook',  # Social media
        r'Well-run funds|Powered by',  # Taglines
    ]
    
    # Find where signature likely starts
    signature_start_idx = None
    for i, line in enumerate(lines_to_check):
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Check if line matches signature patterns
        for pattern in signature_indicators:
            if re.match(pattern, line_stripped, re.IGNORECASE):
                signature_start_idx = start_check + i
                break
        
        if signature_start_idx is not None:
            break
    
    # If we found a signature start, remove everything from there
    if signature_start_idx is not None:
        # Also check a few lines before for separators
        for i in range(max(0, signature_start_idx - 3), signature_start_idx):
            if re.match(r'^[-_=]{2,}', lines[i].strip()):
                return '\n'.join(lines[:i]).rstrip()
        return '\n'.join(lines[:signature_start_idx]).rstrip()
    
    # Fallback: remove very long blocks of text at the end that look like legal disclaimers
    # (more than 200 chars in last 30% with lots of legal-sounding words)
    last_portion = content[int(len(content) * 0.7):]
    legal_words = ['confidential', 'privileged', 'notice', 'disclosure', 'prohibited', 
                   'intended recipient', 'virus', 'responsibility', 'privacy']
    legal_word_count = sum(1 for word in legal_words if word in last_portion.lower())
    
    if len(last_portion) > 200 and legal_word_count >= 3:
        return content[:int(len(content) * 0.7)].rstrip()
    
    return content
