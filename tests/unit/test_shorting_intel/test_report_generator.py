"""Tests for the report generation system."""

from datetime import datetime, timezone

from shorting_intel.analyzers.counter_intel import analyze_all_targets
from shorting_intel.analyzers.disruption_scorer import score_all_targets
from shorting_intel.models.signals import Signal, SignalSource, SignalType, ThreatAssessment, Urgency
from shorting_intel.models.targets import TARGET_COMPANIES
from shorting_intel.reports.generator import generate_json_report, generate_text_report


def _make_sample_signal() -> Signal:
    return Signal(
        signal_type=SignalType.NEW_MODEL_RELEASE,
        source=SignalSource.ANTHROPIC_BLOG,
        title="Test Signal",
        description="Test description",
        url="https://example.com",
        timestamp=datetime.now(timezone.utc),
        ai_company="anthropic",
    )


def _make_sample_assessment() -> ThreatAssessment:
    return ThreatAssessment(
        ticker="CHGG",
        company_name="Chegg",
        overall_threat_score=0.9,
        disruption_timeline="imminent",
        recommended_action="short_now",
        reasoning="Test reasoning",
    )


class TestTextReport:
    def test_generates_text(self):
        scores = score_all_targets()
        ci_reports = analyze_all_targets()
        assessments = [_make_sample_assessment()]
        signals = [_make_sample_signal()]

        report = generate_text_report(signals, [], scores, ci_reports, assessments)
        assert isinstance(report, str)
        assert len(report) > 100
        assert "SHORTING INTELLIGENCE BRIEFING" in report
        assert "EXECUTIVE SUMMARY" in report
        assert "TOP SHORTING OPPORTUNITIES" in report
        assert "COUNTER-INTELLIGENCE ANALYSIS" in report

    def test_contains_target_tickers(self):
        scores = score_all_targets()
        ci_reports = analyze_all_targets()
        report = generate_text_report([], [], scores, ci_reports, [])
        assert "CHGG" in report


class TestJsonReport:
    def test_generates_valid_json(self):
        scores = score_all_targets()
        ci_reports = analyze_all_targets()
        assessments = [_make_sample_assessment()]
        signals = [_make_sample_signal()]

        report = generate_json_report(signals, scores, ci_reports, assessments)
        assert isinstance(report, dict)
        assert "generated_at" in report
        assert "summary" in report
        assert "top_shorts" in report
        assert "counter_intel" in report
        assert "threat_assessments" in report

    def test_top_shorts_have_required_fields(self):
        scores = score_all_targets()
        ci_reports = analyze_all_targets()
        report = generate_json_report([], scores, ci_reports, [])

        for short in report["top_shorts"]:
            assert "ticker" in short
            assert "company" in short
            assert "final_score" in short
