"""Tests for the target company intelligence dossier."""

from shorting_intel.models.targets import (
    TARGET_COMPANIES,
    DisruptionCategory,
    ThreatLevel,
    get_all_tickers,
    get_critical_targets,
    get_targets_by_category,
    get_targets_by_threat_level,
)


class TestTargetCompanies:
    def test_targets_not_empty(self):
        assert len(TARGET_COMPANIES) > 0

    def test_all_targets_have_required_fields(self):
        for target in TARGET_COMPANIES:
            assert target.ticker, f"Missing ticker for {target.name}"
            assert target.name, f"Missing name for ticker {target.ticker}"
            assert target.category is not None, f"Missing category for {target.ticker}"
            assert target.threat_level is not None, f"Missing threat_level for {target.ticker}"
            assert target.disruption_thesis, f"Missing disruption_thesis for {target.ticker}"

    def test_no_duplicate_tickers(self):
        tickers = get_all_tickers()
        assert len(tickers) == len(set(tickers)), "Duplicate tickers found"

    def test_critical_targets_exist(self):
        critical = get_critical_targets()
        assert len(critical) >= 1
        for target in critical:
            assert target.threat_level == ThreatLevel.CRITICAL

    def test_get_targets_by_category(self):
        edu_targets = get_targets_by_category(DisruptionCategory.EDUCATION_TUTORING)
        assert len(edu_targets) >= 1
        for target in edu_targets:
            assert target.category == DisruptionCategory.EDUCATION_TUTORING

    def test_chegg_is_critical(self):
        chegg = next((t for t in TARGET_COMPANIES if t.ticker == "CHGG"), None)
        assert chegg is not None
        assert chegg.threat_level == ThreatLevel.CRITICAL
        assert len(chegg.threat_vectors) > 0
        assert len(chegg.counter_intel_signals) > 0

    def test_all_threat_vectors_have_fields(self):
        for target in TARGET_COMPANIES:
            for tv in target.threat_vectors:
                assert tv.capability, f"Missing capability for {target.ticker}"
                assert tv.ai_source in ("anthropic", "openai", "google"), \
                    f"Invalid ai_source '{tv.ai_source}' for {target.ticker}"
                assert 0.0 <= tv.impact_severity <= 1.0, \
                    f"Invalid severity {tv.impact_severity} for {target.ticker}"
