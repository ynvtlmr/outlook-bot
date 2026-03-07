"""Cold outreach workflow: load CSV leads, generate emails, create drafts."""

from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import TYPE_CHECKING, Any

from outlook_bot.core.models import Lead

if TYPE_CHECKING:
    from pathlib import Path

    from outlook_bot.email.client import EmailClient
    from outlook_bot.providers.registry import ProviderRegistry


def load_csv_leads(csv_path: str) -> list[Lead]:
    """Parse a Salesforce CSV export into Lead objects.

    Handles encoding issues, multi-email rows, and per-email deduplication.
    """
    rows: list[dict[str, Any]] = []
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

    email_map: dict[str, dict[str, Any]] = {}

    for row in rows:
        raw_email = (row.get("eMail") or "").strip()
        if not raw_email:
            continue

        for email in (e.strip() for e in raw_email.split(",") if e.strip()):
            email_lower = email.lower()
            product = (row.get("Technology Solution") or "").strip()
            opportunity = (row.get("Opportunity Name") or "").strip()
            opportunity_id = (row.get("Opportunity ID") or "").strip()
            account = (row.get("Account Name") or "").strip()
            contact = (row.get("Authorized Signatory") or "").strip()
            latest_interaction = (row.get("Pipeline Comments/Next Steps") or "").strip()
            description = (row.get("Description") or "").strip()
            account_description = (row.get("Account Description") or "").strip()

            if email_lower in email_map:
                existing = email_map[email_lower]
                if product and product not in existing["products"]:
                    existing["products"].append(product)
                if opportunity and opportunity not in existing["opportunities"]:
                    existing["opportunities"].append(opportunity)
                if opportunity_id and opportunity_id not in existing["opportunity_ids"]:
                    existing["opportunity_ids"].append(opportunity_id)
                if latest_interaction and latest_interaction not in existing["latest_interaction"]:
                    li = existing["latest_interaction"]
                    existing["latest_interaction"] = f"{li}; {latest_interaction}" if li else latest_interaction
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
                    "opportunities": [opportunity] if opportunity else [],
                    "opportunity_ids": [opportunity_id] if opportunity_id else [],
                    "latest_interaction": latest_interaction,
                    "description": description,
                    "account_description": account_description,
                }

    leads = [
        Lead(
            email=data["email"],
            account_name=data["account_name"],
            contact_name=data["contact_name"],
            products=data["products"],
            opportunities=data["opportunities"],
            opportunity_ids=data["opportunity_ids"],
            latest_interaction=data["latest_interaction"],
            description=data["description"],
            account_description=data["account_description"],
        )
        for data in email_map.values()
    ]

    print(f"  -> Parsed {len(leads)} unique leads from CSV.")
    return leads


def run_cold_outreach(
    client: EmailClient,
    registry: ProviderRegistry,
    cold_prompt: str,
    preferred_model: str | None,
    csv_path: str,
    daily_limit: int,
    salesforce_bcc: str,
    user_data_dir: str | Path = ".",
) -> None:
    """Execute the cold outreach pipeline."""
    print("\n--- Cold Outreach ---")

    if csv_path and not os.path.isabs(csv_path):
        csv_path = os.path.join(str(user_data_dir), csv_path)

    if not csv_path or not os.path.exists(csv_path):
        print(f"  -> CSV file not found: {csv_path}")
        return

    leads = load_csv_leads(csv_path)
    if not leads:
        return

    # Personal emails first, generic last
    leads.sort(key=lambda lead: lead.is_generic)

    print("  -> Fetching sent recipients from Outlook...")
    sent_recipients = client.get_sent_recipients()
    print(f"  -> Found {len(sent_recipients)} unique sent recipients.")

    drafts_created = 0
    already_contacted = 0

    for lead in leads:
        if drafts_created >= daily_limit:
            print(f"  -> Daily limit of {daily_limit} drafts reached.")
            break

        print(f"\n  Checking: {lead.email} ({lead.account_name})")

        if lead.email in sent_recipients:
            print("    -> Already contacted. Skipping.")
            already_contacted += 1
            continue

        print("    -> Generating outreach email...")
        reply = registry.generate_reply(lead.lead_context, cold_prompt, preferred_model=preferred_model)

        if not reply:
            print("    -> Failed to generate outreach email. Skipping.")
            continue

        subject = f"Gen II x {lead.account_name} - {lead.products_display}"
        formatted_content = reply.replace("\n", "<br>")
        result = client.create_draft(lead.email, subject, formatted_content, bcc_address=salesforce_bcc)
        print(f"    -> {result}")
        drafts_created += 1

        _generate_and_print_sf_note(registry, lead, reply, preferred_model)

    print("\n--- Cold Outreach Summary ---")
    print(f"  Total leads in CSV: {len(leads)}")
    print(f"  Already contacted: {already_contacted}")
    print(f"  Drafts created: {drafts_created}")
    print(f"  Daily limit: {daily_limit}")


def _generate_and_print_sf_note(
    registry: ProviderRegistry, lead: Lead, reply: str, preferred_model: str | None
) -> None:
    """Generate and print Salesforce note for a lead."""
    today = datetime.now()
    date_str = f"{today.month}/{today.day}/{str(today.year)[-2:]}"

    sf_note = registry.generate_reply(
        f"Outreach sent to {lead.account_name} ({lead.email}) about {lead.products_display}.\n"
        f"Latest Interaction: {lead.latest_interaction}\n"
        f"Opportunity History: {lead.description}\n\n"
        f"Email content:\n{reply}",
        f"Write a one-sentence Salesforce note starting with {date_str}. "
        f"TL;DR style, punchy, straight to the point. "
        f"Drop the subject pronoun - say 'reached out' not 'we reached out'. "
        f"Just the note, nothing else.",
        preferred_model=preferred_model,
    )

    if sf_note:
        opps = ", ".join(lead.opportunities) if lead.opportunities else lead.account_name
        for oid in lead.opportunity_ids:
            print(f"\n    https://gen2.lightning.force.com/lightning/r/Opportunity/{oid}/edit")
        print(f"    [{opps}] {sf_note}")
