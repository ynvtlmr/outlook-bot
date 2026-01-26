"""
Module for handling CSV-based outreach email generation.
"""
import os
from typing import Any, Dict, List, Optional

import llm
from config import APPLESCRIPTS_DIR, CONFIG_PATH, SYSTEM_PROMPT_PATH
from csv_parser import (
    format_contact_info_for_prompt,
    get_contact_email,
    parse_csv_file,
    sort_contacts_by_last_activity,
)
from date_utils import get_current_date_context
from outlook_client import OutlookClient
import yaml


def load_system_prompt() -> str:
    """Loads text from system_prompt.txt or returns default."""
    try:
        with open(SYSTEM_PROMPT_PATH, "r") as f:
            return f.read()
    except Exception as e:
        print(f"  -> Warning: Could not read system prompt: {e}")
        return "You are a helpful assistant."


def generate_email_for_contact(
    contact: Dict[str, Any],
    base_system_prompt: str,
    llm_service: llm.LLMService,
    preferred_model: Optional[str] = None,
) -> Optional[str]:
    """
    Generates an email for a specific contact using the LLM service.
    
    Args:
        contact: Contact dictionary with all CSV fields
        base_system_prompt: Base system prompt from system_prompt.txt
        llm_service: Initialized LLM service
        preferred_model: Optional preferred model ID
        
    Returns:
        Generated email content or None if generation fails
    """
    # Format contact information
    contact_info = format_contact_info_for_prompt(contact)
    
    # Get date context
    date_context = get_current_date_context()
    
    # Combine system prompt with contact information
    enhanced_prompt = f"""{date_context}

{base_system_prompt}

{contact_info}

TASK: Write a personalized cold outreach email to this contact. Use the information provided above to craft a relevant, personalized message. The email should be:
- Short and to the point
- Friendly but professional
- Personalized based on the contact information
- Focused on building a relationship and introducing Gen II's services

Start the email with a greeting (e.g., "Hello [name]") and sign off with "Best, Itamar".

Email:"""

    try:
        # Generate email using LLM
        email_content = llm_service.generate_reply(
            email_body="",  # No existing thread for cold outreach
            system_prompt=enhanced_prompt,
            preferred_model=preferred_model,
        )
        
        return email_content
    except Exception as e:
        print(f"  -> Error generating email for contact: {e}")
        return None


def create_email_draft(
    client: OutlookClient,
    to_email: str,
    subject: str,
    content: str,
    bcc_address: str = "",
) -> bool:
    """
    Creates an email draft in Outlook.
    
    Args:
        client: OutlookClient instance
        to_email: Recipient email address
        subject: Email subject line
        content: Email body content
        bcc_address: Optional BCC address (e.g., Salesforce)
        
    Returns:
        True if draft was created successfully, False otherwise
    """
    try:
        # Format content for AppleScript (convert newlines to <br>)
        formatted_content = content.replace("\n", "<br>")
        
        # Create draft using OutlookClient
        result = client.create_draft(
            to_email, subject, formatted_content, bcc_address=bcc_address if bcc_address else None
        )
        
        if result and "Error" not in result:
            print(f"  -> Draft created for {to_email}")
            return True
        else:
            print(f"  -> Failed to create draft for {to_email}: {result}")
            return False
    except Exception as e:
        print(f"  -> Error creating draft: {e}")
        return False


def process_csv_outreach(
    csv_path: str,
    num_contacts: int,
    llm_service: llm.LLMService,
    outlook_client: OutlookClient,
    preferred_model: Optional[str] = None,
    salesforce_bcc: str = "",
) -> Dict[str, Any]:
    """
    Main function to process CSV file and generate emails for contacts.
    
    Args:
        csv_path: Path to CSV file
        num_contacts: Number of contacts to process
        llm_service: Initialized LLM service
        outlook_client: Initialized Outlook client
        preferred_model: Optional preferred model ID
        salesforce_bcc: Optional Salesforce BCC address
        
    Returns:
        Dictionary with processing results
    """
    results = {
        "total_contacts": 0,
        "processed": 0,
        "successful": 0,
        "failed": 0,
        "errors": [],
    }
    
    try:
        # Parse CSV
        print(f"\n[Info] Parsing CSV file: {csv_path}")
        contacts = parse_csv_file(csv_path)
        results["total_contacts"] = len(contacts)
        print(f"[Info] Found {len(contacts)} contacts in CSV")
        
        # Sort by Last Activity (uncontacted first, then oldest first)
        print("[Info] Sorting contacts by Last Activity...")
        sorted_contacts = sort_contacts_by_last_activity(contacts)
        
        # Filter contacts with valid email addresses
        valid_contacts = []
        for contact in sorted_contacts:
            email = get_contact_email(contact)
            if email:
                valid_contacts.append(contact)
            else:
                print(f"  -> Warning: Skipping contact (no email): {contact.get('Account Name', 'Unknown')}")
        
        print(f"[Info] Found {len(valid_contacts)} contacts with valid email addresses")
        
        # Limit to num_contacts
        contacts_to_process = valid_contacts[:num_contacts]
        print(f"[Info] Processing {len(contacts_to_process)} contacts")
        
        # Load system prompt
        base_system_prompt = load_system_prompt()
        date_context = get_current_date_context()
        
        # Process each contact
        for idx, contact in enumerate(contacts_to_process, 1):
            account_name = contact.get("Account Name", "Unknown")
            email = get_contact_email(contact)
            
            if not email:
                results["failed"] += 1
                results["errors"].append(f"{account_name}: No email address")
                continue
            
            print(f"\n[{idx}/{len(contacts_to_process)}] Processing: {account_name} ({email})")
            results["processed"] += 1
            
            # Generate email
            print("  -> Generating email...")
            email_content = generate_email_for_contact(
                contact, base_system_prompt, llm_service, preferred_model=preferred_model
            )
            
            if not email_content:
                results["failed"] += 1
                results["errors"].append(f"{account_name}: Failed to generate email")
                print(f"  -> Error: Failed to generate email")
                continue
            
            # Create subject line (use Opportunity Name or Account Name)
            subject = contact.get("Opportunity Name", contact.get("Account Name", "Outreach"))
            if not subject:
                subject = "Outreach"
            
            # Create draft
            print("  -> Creating draft in Outlook...")
            success = create_email_draft(
                outlook_client,
                email,
                subject,
                email_content,
                bcc_address=salesforce_bcc,
            )
            
            if success:
                results["successful"] += 1
                print(f"  -> ✓ Successfully created draft for {account_name}")
            else:
                results["failed"] += 1
                results["errors"].append(f"{account_name}: Failed to create draft")
                print(f"  -> ✗ Failed to create draft")
        
        print(f"\n[Summary] Processed: {results['processed']}, Successful: {results['successful']}, Failed: {results['failed']}")
        
    except Exception as e:
        error_msg = f"Error processing CSV outreach: {e}"
        print(f"[Error] {error_msg}")
        results["errors"].append(error_msg)
        import traceback
        traceback.print_exc()
    
    return results
