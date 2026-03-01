import csv
import os
from datetime import datetime
from typing import Any

import llm
from config import USER_DATA_DIR
from outlook_client import OutlookClient

GENERIC_PREFIXES = {"info", "news", "contact", "support", "admin"}


def is_generic_email(email: str) -> bool:
    """Returns True for generic email prefixes like info@, news@, etc."""
    local_part = email.split("@")[0].lower()
    return local_part in GENERIC_PREFIXES


def load_csv_leads(csv_path: str) -> list[dict[str, Any]]:
    """
    Parse a Salesforce CSV export of leads.
    Handles encoding issues, filters rows with no email, splits multi-email rows,
    and groups by email so one contact with multiple products gets a single entry.
    """
    rows = []
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            with open(csv_path, newline="", encoding=encoding) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            break
        except UnicodeDecodeError:
            continue

    if not rows:
        print("  -> CSV is empty or could not be read.")
        return []

    # Expand multi-email rows and collect per-email entries
    email_map: dict[str, dict[str, Any]] = {}

    for row in rows:
        raw_email = (row.get("eMail") or "").strip()
        if not raw_email:
            continue

        emails = [e.strip() for e in raw_email.split(",") if e.strip()]

        for email in emails:
            email_lower = email.lower()
            product = (row.get("Technology Solution") or "").strip()
            account = (row.get("Account Name") or "").strip()
            contact = (row.get("Authorized Signatory") or "").strip()
            latest_interaction = (row.get("Pipeline Comments/Next Steps") or "").strip()
            description = (row.get("Description") or "").strip()
            account_description = (row.get("Account Description") or "").strip()

            if email_lower in email_map:
                # Append product if not already listed
                existing = email_map[email_lower]
                if product and product not in existing["products"]:
                    existing["products"].append(product)
                # Merge latest interaction
                if latest_interaction and latest_interaction not in existing["latest_interaction"]:
                    existing["latest_interaction"] += f"; {latest_interaction}" if existing["latest_interaction"] else latest_interaction
                # Keep longest description
                if len(description) > len(existing["description"]):
                    existing["description"] = description
                if len(account_description) > len(existing["account_description"]):
                    existing["account_description"] = account_description
            else:
                email_map[email_lower] = {
                    "email": email_lower,
                    "account_name": account,
                    "contact_name": contact,
                    "products": [product] if product else [],
                    "latest_interaction": latest_interaction,
                    "description": description,
                    "account_description": account_description,
                }

    leads = list(email_map.values())
    print(f"  -> Parsed {len(leads)} unique leads from CSV.")
    return leads


def process_cold_outreach(
    client: OutlookClient,
    llm_service: llm.LLMService,
    cold_prompt: str,
    preferred_model: str | None,
    csv_path: str,
    daily_limit: int,
    salesforce_bcc: str,
) -> None:
    """
    Main cold outreach orchestration:
    1. Load CSV leads
    2. Sort personal emails first, generic last
    3. Check Sent Items for each lead
    4. Generate outreach drafts for un-contacted leads up to daily_limit
    """
    print("\n--- Cold Outreach ---")

    # Resolve relative paths against the project root (USER_DATA_DIR)
    if csv_path and not os.path.isabs(csv_path):
        csv_path = os.path.join(USER_DATA_DIR, csv_path)

    if not csv_path or not os.path.exists(csv_path):
        print(f"  -> CSV file not found: {csv_path}")
        return

    # 1. Load leads
    leads = load_csv_leads(csv_path)
    if not leads:
        return

    # 2. Sort: personal emails first, generic last
    leads.sort(key=lambda lead: is_generic_email(lead["email"]))

    # 3. Fetch all sent recipients in one batch call (much faster than per-lead)
    print("  -> Fetching sent recipients from Outlook...")
    sent_recipients = client.get_sent_recipients()
    print(f"  -> Found {len(sent_recipients)} unique sent recipients.")

    # 4. Check against sent recipients and collect un-contacted leads
    drafts_created = 0
    already_contacted = 0
    skipped_no_email = 0

    for lead in leads:
        if drafts_created >= daily_limit:
            print(f"  -> Daily limit of {daily_limit} drafts reached.")
            break

        email = lead["email"]
        if not email:
            skipped_no_email += 1
            continue

        print(f"\n  Checking: {email} ({lead['account_name']})")

        # Check if already emailed (fast in-memory set lookup)
        if email in sent_recipients:
            print(f"    -> Already contacted. Skipping.")
            already_contacted += 1
            continue

        # 4. Generate outreach email via LLM
        products_str = ", ".join(lead["products"]) if lead["products"] else "Gen II Solutions"
        lead_context = (
            f"Account: {lead['account_name']}\n"
            f"Contact: {lead['contact_name']}\n"
            f"Email: {email}\n"
            f"Products: {products_str}\n"
            f"Latest Interaction: {lead['latest_interaction']}\n"
            f"Opportunity History: {lead['description']}\n"
            f"Account Description: {lead['account_description']}"
        )

        print(f"    -> Generating outreach email...")
        reply = llm_service.generate_reply(
            lead_context,
            cold_prompt,
            preferred_model=preferred_model,
        )

        if not reply:
            print(f"    -> Failed to generate outreach email. Skipping.")
            continue

        # Generate a subject line from the reply or use a default
        subject = f"Gen II x {lead['account_name']} - {products_str}"

        # Create draft
        formatted_content = reply.replace("\n", "<br>")
        result = client.create_draft(email, subject, formatted_content, bcc_address=salesforce_bcc)
        print(f"    -> {result}")
        drafts_created += 1

        # Generate SF Note
        today = datetime.now()
        date_str = f"{today.month}/{today.day}/{str(today.year)[-2:]}"
        sf_note = llm_service.generate_reply(
            f"Outreach sent to {lead['account_name']} ({email}) about {products_str}.\n"
            f"Latest Interaction: {lead['latest_interaction']}\n"
            f"Opportunity History: {lead['description']}\n\n"
            f"Email content:\n{reply}",
            f"Write a one-sentence Salesforce note starting with {date_str}. "
            f"Written from Gen II's perspective using 'we'. "
            f"TL;DR style, punchy, straight to the point. Just the note, nothing else.",
            preferred_model=preferred_model,
        )
        if sf_note:
            print(f"\n    SF Note: {sf_note}")

    # Summary
    print(f"\n--- Cold Outreach Summary ---")
    print(f"  Total leads in CSV: {len(leads)}")
    print(f"  Already contacted: {already_contacted}")
    print(f"  Drafts created: {drafts_created}")
    print(f"  Daily limit: {daily_limit}")
