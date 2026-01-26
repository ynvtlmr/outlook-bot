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
    
    # Extract contact name for personalization
    contact_name = contact.get("Authorized Signatory", "") or contact.get("Account Name", "")
    
    # Combine system prompt with contact information
    enhanced_prompt = f"""{date_context}

{base_system_prompt}

{contact_info}

TASK: Write a personalized cold outreach email to this contact. Use the information provided above to craft a relevant, personalized message. The email should be:
- Short and to the point
- Friendly but professional
- Personalized based on the contact information provided
- Focused on building a relationship and introducing Gen II's services (Sensr Portal, Funded, Sensr Analytics, Databridge)
- Reference specific details from the contact information when relevant

Start the email with a greeting (e.g., "Hello [name]" or "Hello" if no name is available) and sign off with "Best, Itamar".

Write ONLY the email body content. Do not include subject line or headers.

Email:"""

    try:
        # For cold outreach, use the dedicated method
        email_content = llm_service.generate_cold_outreach_email(
            system_prompt=enhanced_prompt,
            preferred_model=preferred_model,
        )
        
        if email_content:
            # Clean up the response - remove any markdown formatting or extra text
            email_content = email_content.strip()
            
            # Remove common LLM artifacts and prefixes
            prefixes_to_remove = [
                "Email:",
                "Here's the email:",
                "Here is the email:",
                "Email body:",
                "Email content:",
                "Here's your email:",
            ]
            for prefix in prefixes_to_remove:
                if email_content.startswith(prefix):
                    email_content = email_content[len(prefix):].strip()
            
            # Remove markdown code blocks
            if email_content.startswith("```"):
                lines = email_content.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                email_content = '\n'.join(lines).strip()
            
            # Final cleanup - remove any remaining markdown or formatting
            email_content = email_content.strip()
            
            print(f"  -> Generated email content ({len(email_content)} chars): {email_content[:200]}...")
        else:
            print("  -> Warning: LLM returned empty content")
        
        return email_content
    except Exception as e:
        print(f"  -> Error generating email for contact: {e}")
        import traceback
        traceback.print_exc()
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
        # Validate inputs
        if not to_email or not to_email.strip():
            print(f"  -> Error: Invalid email address: {to_email}")
            return False
        
        if not content or not content.strip():
            print(f"  -> Error: Email content is empty")
            return False
        
        # Format content for AppleScript (convert newlines to <br>)
        # Ensure content is not empty
        if not content or len(content.strip()) == 0:
            print(f"  -> Error: Content is empty, cannot create draft")
            return False
        
        formatted_content = content.replace("\n", "<br>")
        
        # Debug: Print what we're sending to AppleScript
        print(f"  -> Debug: Sending to AppleScript - Content length: {len(formatted_content)} chars")
        print(f"  -> Debug: First 100 chars of formatted content: {formatted_content[:100]}")
        
        # Create draft using OutlookClient
        result = client.create_draft(
            to_email.strip(), subject, formatted_content, bcc_address=bcc_address if bcc_address else None
        )
        
        if result and "Error" not in result:
            print(f"  -> Draft created successfully for {to_email}")
            return True
        else:
            print(f"  -> Failed to create draft for {to_email}: {result}")
            return False
    except Exception as e:
        print(f"  -> Error creating draft: {e}")
        import traceback
        traceback.print_exc()
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
            
            print(f"\n[{idx}/{len(contacts_to_process)}] Processing: {account_name}")
            print(f"  -> Email address: {email}")
            results["processed"] += 1
            
            # Generate email
            print("  -> Generating email content...")
            email_content = generate_email_for_contact(
                contact, base_system_prompt, llm_service, preferred_model=preferred_model
            )
            
            if not email_content:
                results["failed"] += 1
                results["errors"].append(f"{account_name}: Failed to generate email")
                print(f"  -> Error: Failed to generate email")
                continue
            
            print(f"  -> Email content generated ({len(email_content)} characters)")
            print(f"  -> Preview: {email_content[:100]}...")
            
            # Create subject line - make it more meaningful
            opportunity_name = contact.get("Opportunity Name", "")
            account_name = contact.get("Account Name", "")
            tech_solution = contact.get("Technology Solution", "")
            
            # Build a meaningful subject
            if opportunity_name and opportunity_name != account_name:
                subject = f"Re: {opportunity_name}"
            elif account_name:
                if tech_solution:
                    subject = f"Re: {account_name} - {tech_solution}"
                else:
                    subject = f"Re: {account_name}"
            else:
                subject = "Outreach"
            
            # Validate email content before creating draft
            if not email_content or len(email_content.strip()) == 0:
                results["failed"] += 1
                results["errors"].append(f"{account_name}: Generated email content is empty")
                print(f"  -> Error: Generated email content is empty, skipping draft creation")
                continue
            
            # Create draft
            print(f"  -> Creating draft in Outlook...")
            print(f"  -> To: {email}")
            print(f"  -> Subject: {subject}")
            print(f"  -> Body length: {len(email_content)} characters")
            print(f"  -> Body preview: {email_content[:150]}...")
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
