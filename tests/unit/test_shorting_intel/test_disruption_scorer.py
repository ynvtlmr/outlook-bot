"""Tests for the disruption impact scoring engine."""

from shorting_intel.analyzers.disruption_scorer import (
    DisruptionScore,
    identify_catalysts,
    score_all_targets,
    score_target,
)
from shorting_intel.models.signals import Signal, SignalSource, SignalType, Urgency
from shorting_intel.models.targets import TARGET_COMPANIES, ThreatLevel

from datetime import datetime, timezone


class TestDisruptionScorer:
    def test_score_single_target(self):
        chegg = next(t for t in TARGET_COMPANIES if t.ticker == "CHGG")
        score = score_target(chegg)
        assert isinstance(score, DisruptionScore)
        assert score.ticker == "CHGG"
        assert 0.0 <= score.final_score <= 1.0
        assert score.final_score > 0.5  # Chegg should score high

    def test_score_all_targets(self):
        scores = score_all_targets()
        assert len(scores) == len(TARGET_COMPANIES)
        # Should be sorted by final_score descending
        for i in range(len(scores) - 1):
            assert scores[i].final_score >= scores[i + 1].final_score

    def test_critical_targets_score_higher(self):
        """Critical targets should generally score higher than moderate ones."""
        scores = score_all_targets()
        critical_scores = [s for s in scores
                          if next(t for t in TARGET_COMPANIES if t.ticker == s.ticker).threat_level == ThreatLevel.CRITICAL]
        moderate_scores = [s for s in scores
                          if next(t for t in TARGET_COMPANIES if t.ticker == s.ticker).threat_level == ThreatLevel.MODERATE]

        if critical_scores and moderate_scores:
            avg_critical = sum(s.final_score for s in critical_scores) / len(critical_scores)
            avg_moderate = sum(s.final_score for s in moderate_scores) / len(moderate_scores)
            assert avg_critical > avg_moderate

    def test_signal_boost(self):
        """Providing signals should boost the score."""
        target = next(t for t in TARGET_COMPANIES if t.ticker == "CHGG")
        score_no_signals = score_target(target)

        signals = [
            Signal(
                signal_type=SignalType.EARNINGS_MISS,
                source=SignalSource.NEWS_ARTICLE,
                title="Chegg misses earnings",
                description="Revenue declined 30% YoY",
                url="https://example.com",
                timestamp=datetime.now(timezone.utc),
                urgency=Urgency.SHORT_TERM,
                affected_tickers=["CHGG"],
                confidence=0.9,
            ),
        ]
        score_with_signals = score_target(target, signals)
        assert score_with_signals.signal_boost > 0
        assert score_with_signals.final_score >= score_no_signals.final_score

    def test_composite_score_calculation(self):
        """Verify composite score is weighted average of factors."""
        score = DisruptionScore(
            ticker="TEST",
            company_name="Test Co",
            capability_overlap=0.8,
            cost_disruption=0.7,
            switching_ease=0.6,
            deployment_speed=0.5,
            moat_erosion=0.4,
        )
        expected = (0.8 * 0.30 + 0.7 * 0.20 + 0.6 * 0.20 + 0.5 * 0.15 + 0.4 * 0.15)
        assert abs(score.composite_score - expected) < 0.001

    def test_identify_catalysts(self):
        signals = [
            Signal(
                signal_type=SignalType.NEW_MODEL_RELEASE,
                source=SignalSource.ANTHROPIC_BLOG,
                title="Anthropic launches new code generation model",
                description="Claude can now write production code autonomously",
                url="https://example.com",
                timestamp=datetime.now(timezone.utc),
                ai_company="anthropic",
                confidence=0.9,
            ),
        ]
        catalysts = identify_catalysts(signals)
        # Should find targets with code-related threat vectors from anthropic
        assert isinstance(catalysts, list)
