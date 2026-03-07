"""Tests for core data models."""

from datetime import datetime, timedelta

from outlook_bot.core.models import Draft, Email, Lead, Thread, ThreadSummary


class TestEmail:
    def test_is_flagged_active(self):
        email = Email(id="1", flag_status="Active")
        assert email.is_flagged_active is True

        email2 = Email(id="2", flag_status="Completed")
        assert email2.is_flagged_active is False

    def test_has_valid_timestamp(self):
        email = Email(id="1", timestamp=datetime.now())
        assert email.has_valid_timestamp is True

        email2 = Email(id="2")
        assert email2.has_valid_timestamp is False

    def test_default_subject(self):
        email = Email(id="1")
        assert email.subject == "No Subject"


class TestThread:
    def test_subject_from_first_email(self):
        thread = Thread(
            emails=[
                Email(id="1", subject="Test Subject"),
                Email(id="1", subject="Re: Test Subject"),
            ]
        )
        assert thread.subject == "Test Subject"

    def test_empty_thread_subject(self):
        thread = Thread()
        assert thread.subject == "No Subject"

    def test_has_active_flag(self):
        thread = Thread(
            emails=[
                Email(id="1", flag_status="Completed"),
                Email(id="1", flag_status="Active"),
            ]
        )
        assert thread.has_active_flag is True

    def test_no_active_flag(self):
        thread = Thread(
            emails=[
                Email(id="1", flag_status="Completed"),
            ]
        )
        assert thread.has_active_flag is False

    def test_latest_timestamp(self):
        now = datetime.now()
        earlier = now - timedelta(days=5)
        thread = Thread(
            emails=[
                Email(id="1", timestamp=earlier),
                Email(id="1", timestamp=now),
            ]
        )
        assert thread.latest_timestamp == now

    def test_latest_timestamp_none(self):
        thread = Thread(emails=[Email(id="1")])
        assert thread.latest_timestamp is None

    def test_latest_email(self):
        now = datetime.now()
        earlier = now - timedelta(days=5)
        e1 = Email(id="1", timestamp=earlier, subject="Old")
        e2 = Email(id="1", timestamp=now, subject="New")
        thread = Thread(emails=[e1, e2])
        assert thread.latest_email == e2

    def test_sorted_chronologically(self):
        now = datetime.now()
        earlier = now - timedelta(days=5)
        e1 = Email(id="1", timestamp=now, subject="New")
        e2 = Email(id="1", timestamp=earlier, subject="Old")
        thread = Thread(emails=[e1, e2])
        sorted_emails = thread.sorted_chronologically()
        assert sorted_emails[0].subject == "Old"
        assert sorted_emails[1].subject == "New"


class TestLead:
    def test_is_generic(self):
        assert Lead(email="info@example.com").is_generic is True
        assert Lead(email="john@example.com").is_generic is False

    def test_products_display(self):
        lead = Lead(email="x@x.com", products=["Sensr Analytics", "Sensr Portal", "Funded"])
        assert lead.products_display == "Sensr Portal, Sensr Analytics, Funded"

    def test_products_display_empty(self):
        lead = Lead(email="x@x.com")
        assert lead.products_display == "Gen II Solutions"

    def test_lead_context(self):
        lead = Lead(email="test@example.com", account_name="Acme Corp")
        context = lead.lead_context
        assert "Acme Corp" in context
        assert "test@example.com" in context
        assert "### LEAD DATA" in context


class TestDraft:
    def test_creation(self):
        draft = Draft(to_address="to@example.com", subject="Test", content="Body")
        assert draft.to_address == "to@example.com"
        assert draft.bcc_address == ""


class TestThreadSummary:
    def test_creation(self):
        summary = ThreadSummary(subject="Test", client_name="Client", summary="Summary text")
        assert summary.sf_note == ""
        assert summary.thread is None
