"""Tests for the AI announcement monitor."""

from datetime import datetime, timezone

from shorting_intel.monitors.ai_announcements import (
    AI_SOURCES,
    _assess_urgency,
    _calculate_confidence,
    _classify_signal_type,
    _find_affected_categories,
    _parse_date,
)
from shorting_intel.models.signals import SignalType, Urgency


class TestSignalClassification:
    def test_model_release_detection(self):
        assert _classify_signal_type("Introducing Claude 4", "") == SignalType.NEW_MODEL_RELEASE
        assert _classify_signal_type("Launching GPT-5", "") == SignalType.NEW_MODEL_RELEASE
        assert _classify_signal_type("Release of Gemini 3", "") == SignalType.NEW_MODEL_RELEASE

    def test_agent_framework_detection(self):
        assert _classify_signal_type("New agent capabilities", "") == SignalType.AGENT_FRAMEWORK
        assert _classify_signal_type("Computer use for Claude", "") == SignalType.AGENT_FRAMEWORK

    def test_api_launch_detection(self):
        assert _classify_signal_type("New API for developers", "") == SignalType.API_LAUNCH
        assert _classify_signal_type("SDK update available", "") == SignalType.API_LAUNCH

    def test_pricing_change_detection(self):
        assert _classify_signal_type("Price reduction announcement", "") == SignalType.PRICING_CHANGE

    def test_capability_announcement_default(self):
        assert _classify_signal_type("Research on constitutional AI", "Safety improvements") == SignalType.CAPABILITY_ANNOUNCEMENT


class TestUrgencyAssessment:
    def test_launch_is_short_term(self):
        assert _assess_urgency("Product launch today", "Available now") == Urgency.SHORT_TERM

    def test_high_impact_is_short_term(self):
        assert _assess_urgency(
            "New model release with agent capabilities and code generation",
            "Launch today"
        ) == Urgency.SHORT_TERM

    def test_low_impact_is_long_term(self):
        assert _assess_urgency("Research paper published", "Theoretical analysis") == Urgency.LONG_TERM


class TestConfidenceCalculation:
    def test_high_keyword_density(self):
        score = _calculate_confidence(
            "Launching new model with agent capabilities for code generation",
            "Available today via API with pricing update"
        )
        assert score > 0.5

    def test_low_keyword_density(self):
        score = _calculate_confidence("Research paper", "Theoretical analysis of safety")
        assert score <= 0.5


class TestCategoryDetection:
    def test_education_detection(self):
        categories = _find_affected_categories("AI tutoring for students", "Learning platform")
        assert "education" in categories

    def test_coding_detection(self):
        categories = _find_affected_categories("Code generation breakthrough", "Software engineering")
        assert "coding" in categories

    def test_customer_service_detection(self):
        categories = _find_affected_categories("Customer service chatbot", "Call center automation")
        assert "customer_service" in categories

    def test_multiple_categories(self):
        categories = _find_affected_categories(
            "AI for customer service and content creation",
            "Coding and translation capabilities"
        )
        assert len(categories) >= 2


class TestDateParsing:
    def test_rfc822_format(self):
        dt = _parse_date("Mon, 01 Jan 2024 12:00:00 +0000")
        assert dt.year == 2024
        assert dt.month == 1

    def test_iso8601_format(self):
        dt = _parse_date("2024-06-15T10:30:00Z")
        assert dt.year == 2024
        assert dt.month == 6

    def test_simple_date(self):
        dt = _parse_date("2024-03-15")
        assert dt.year == 2024


class TestAISources:
    def test_all_sources_have_required_fields(self):
        for key, source in AI_SOURCES.items():
            assert "name" in source, f"Missing name for {key}"
            assert "signal_source" in source, f"Missing signal_source for {key}"
            assert "blog_rss" in source, f"Missing blog_rss for {key}"

    def test_three_sources_configured(self):
        assert "anthropic" in AI_SOURCES
        assert "openai" in AI_SOURCES
        assert "google" in AI_SOURCES
