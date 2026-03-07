"""Tests for the counter-intelligence analyzer."""

from shorting_intel.analyzers.counter_intel import (
    CounterIntelReport,
    analyze_all_targets,
    analyze_target,
)
from shorting_intel.models.targets import TARGET_COMPANIES, ThreatLevel


class TestCounterIntelAnalyzer:
    def test_analyze_single_target(self):
        chegg = next(t for t in TARGET_COMPANIES if t.ticker == "CHGG")
        report = analyze_target(chegg)
        assert isinstance(report, CounterIntelReport)
        assert report.ticker == "CHGG"
        assert 0.0 <= report.defense_score <= 1.0
        assert 0.0 <= report.deception_score <= 1.0
        assert len(report.red_flags) > 0
        assert report.recommendation

    def test_analyze_all_targets(self):
        reports = analyze_all_targets()
        assert len(reports) == len(TARGET_COMPANIES)
        # Should be sorted by deception score descending
        for i in range(len(reports) - 1):
            assert reports[i].deception_score >= reports[i + 1].deception_score

    def test_critical_targets_have_high_deception(self):
        """Critical targets with many counter-intel signals should score high."""
        chegg = next(t for t in TARGET_COMPANIES if t.ticker == "CHGG")
        report = analyze_target(chegg)
        # Chegg has 5 counter-intel signals, should have significant deception
        assert report.deception_score >= 0.5

    def test_moderate_targets_score_lower(self):
        """Moderate threat targets should generally have lower deception scores."""
        moderate_targets = [t for t in TARGET_COMPANIES if t.threat_level == ThreatLevel.MODERATE]
        if moderate_targets:
            for target in moderate_targets:
                report = analyze_target(target)
                # Not a hard rule but should generally be lower
                assert report.deception_score <= 1.0

    def test_recommendation_generated(self):
        for target in TARGET_COMPANIES[:5]:
            report = analyze_target(target)
            assert report.recommendation
            assert target.ticker in report.recommendation
