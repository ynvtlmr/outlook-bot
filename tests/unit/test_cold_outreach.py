"""Tests for the cold outreach workflow."""

import csv

from outlook_bot.workflows.cold_outreach import load_csv_leads


class TestLoadCSVLeads:
    def test_loads_basic_csv(self, tmp_path):
        csv_file = tmp_path / "leads.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "eMail",
                    "Technology Solution",
                    "Opportunity Name",
                    "Opportunity ID",
                    "Account Name",
                    "Authorized Signatory",
                    "Pipeline Comments/Next Steps",
                    "Description",
                    "Account Description",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "eMail": "john@example.com",
                    "Technology Solution": "Sensr Portal",
                    "Opportunity Name": "Opp1",
                    "Opportunity ID": "OPP001",
                    "Account Name": "Acme Corp",
                    "Authorized Signatory": "John Doe",
                    "Pipeline Comments/Next Steps": "Follow up",
                    "Description": "Description",
                    "Account Description": "Account Desc",
                }
            )

        leads = load_csv_leads(str(csv_file))
        assert len(leads) == 1
        assert leads[0].email == "john@example.com"
        assert leads[0].account_name == "Acme Corp"
        assert "Sensr Portal" in leads[0].products

    def test_deduplicates_emails(self, tmp_path):
        csv_file = tmp_path / "leads.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "eMail",
                    "Technology Solution",
                    "Opportunity Name",
                    "Opportunity ID",
                    "Account Name",
                    "Authorized Signatory",
                    "Pipeline Comments/Next Steps",
                    "Description",
                    "Account Description",
                ],
            )
            writer.writeheader()
            for product in ["Sensr Portal", "Sensr Analytics"]:
                writer.writerow(
                    {
                        "eMail": "john@example.com",
                        "Technology Solution": product,
                        "Opportunity Name": f"Opp-{product}",
                        "Opportunity ID": f"ID-{product}",
                        "Account Name": "Acme Corp",
                        "Authorized Signatory": "John Doe",
                        "Pipeline Comments/Next Steps": "",
                        "Description": "",
                        "Account Description": "",
                    }
                )

        leads = load_csv_leads(str(csv_file))
        assert len(leads) == 1
        assert len(leads[0].products) == 2

    def test_handles_multi_email_field(self, tmp_path):
        csv_file = tmp_path / "leads.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "eMail",
                    "Technology Solution",
                    "Opportunity Name",
                    "Opportunity ID",
                    "Account Name",
                    "Authorized Signatory",
                    "Pipeline Comments/Next Steps",
                    "Description",
                    "Account Description",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "eMail": "a@example.com, b@example.com",
                    "Technology Solution": "Funded",
                    "Opportunity Name": "Opp1",
                    "Opportunity ID": "OPP001",
                    "Account Name": "Dual Corp",
                    "Authorized Signatory": "Jane",
                    "Pipeline Comments/Next Steps": "",
                    "Description": "",
                    "Account Description": "",
                }
            )

        leads = load_csv_leads(str(csv_file))
        assert len(leads) == 2

    def test_empty_csv(self, tmp_path):
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        leads = load_csv_leads(str(csv_file))
        assert leads == []
