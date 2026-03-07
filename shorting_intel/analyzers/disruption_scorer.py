"""
Disruption Impact Scorer — Quantitative Threat Assessment

Takes AI capability announcements and scores their impact on each target
company. Uses a multi-factor model:

1. CAPABILITY OVERLAP: How directly does the AI capability replace
   the company's core offering?

2. COST DISRUPTION: How much cheaper is the AI alternative?

3. SWITCHING COST: How easy is it for customers to switch to AI?

4. TIMELINE: How quickly can the AI capability be deployed at scale?

5. MOAT EROSION: Does the AI capability undermine the company's
   competitive advantage (data, network effects, brand, etc.)?
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from shorting_intel.models.signals import Signal, SignalType
from shorting_intel.models.targets import (
    TARGET_COMPANIES,
    DisruptionCategory,
    TargetCompany,
    ThreatLevel,
)

logger = logging.getLogger(__name__)


@dataclass
class DisruptionScore:
    """Quantitative disruption score for a target company."""

    ticker: str
    company_name: str
    capability_overlap: float  # 0-1: how directly AI replaces their offering
    cost_disruption: float  # 0-1: how much cheaper the AI alternative is
    switching_ease: float  # 0-1: how easy for customers to switch
    deployment_speed: float  # 0-1: how quickly AI can be deployed
    moat_erosion: float  # 0-1: how much AI undermines competitive advantage
    composite_score: float = 0.0  # Weighted average
    category_multiplier: float = 1.0  # Category-specific adjustment
    signal_boost: float = 0.0  # Recent signals adjustment
    final_score: float = 0.0

    def __post_init__(self):
        self.composite_score = (
            self.capability_overlap * 0.30
            + self.cost_disruption * 0.20
            + self.switching_ease * 0.20
            + self.deployment_speed * 0.15
            + self.moat_erosion * 0.15
        )
        self.final_score = min(1.0, self.composite_score * self.category_multiplier + self.signal_boost)


# Category-level disruption multipliers
# Some categories are inherently more vulnerable to AI disruption
CATEGORY_MULTIPLIERS: dict[DisruptionCategory, float] = {
    DisruptionCategory.EDUCATION_TUTORING: 1.3,  # Direct replacement
    DisruptionCategory.CUSTOMER_SERVICE_CALL_CENTER: 1.2,  # AI agents replacing humans
    DisruptionCategory.CONTENT_CREATION_MEDIA: 1.2,  # AI generates content
    DisruptionCategory.DATA_LABELING_ANNOTATION: 1.3,  # Synthetic data replacing human labeling
    DisruptionCategory.TRANSLATION_LOCALIZATION: 1.2,  # AI translation near human quality
    DisruptionCategory.SOFTWARE_SERVICES_CONSULTING: 1.1,  # AI coding reduces headcount need
    DisruptionCategory.FREELANCE_MARKETPLACE: 1.2,  # AI replaces freelancer categories
    DisruptionCategory.SAAS_PLATFORM: 0.9,  # Some SaaS can integrate AI
    DisruptionCategory.SEARCH_ADVERTISING: 0.8,  # Complex dynamics
    DisruptionCategory.LEGAL_DOCUMENT_REVIEW: 1.0,  # Slower adoption in legal
    DisruptionCategory.FINANCIAL_SERVICES: 0.8,  # Regulatory barriers slow disruption
}

# Signal type impact on disruption score
SIGNAL_IMPACT: dict[SignalType, float] = {
    SignalType.NEW_MODEL_RELEASE: 0.05,
    SignalType.CAPABILITY_ANNOUNCEMENT: 0.04,
    SignalType.API_LAUNCH: 0.04,
    SignalType.PRICING_CHANGE: 0.06,  # Price drops are very impactful
    SignalType.AGENT_FRAMEWORK: 0.05,
    SignalType.BENCHMARK_RESULT: 0.03,
    SignalType.PARTNERSHIP: 0.02,
    SignalType.EARNINGS_MISS: 0.06,
    SignalType.GUIDANCE_CUT: 0.07,
    SignalType.LAYOFF: 0.05,
    SignalType.CEO_CHANGE: 0.04,
    SignalType.ANALYST_DOWNGRADE: 0.04,
    SignalType.INSIDER_SELLING: 0.03,
    SignalType.CUSTOMER_LOSS: 0.06,
    SignalType.TRAFFIC_DECLINE: 0.05,
}


def _base_scores_for_target(target: TargetCompany) -> dict[str, float]:
    """Calculate base disruption scores from the target's threat vectors."""
    if not target.threat_vectors:
        # Use threat level as a proxy
        base = {
            ThreatLevel.CRITICAL: 0.85,
            ThreatLevel.HIGH: 0.70,
            ThreatLevel.MODERATE: 0.50,
            ThreatLevel.WATCH: 0.30,
        }[target.threat_level]
        return {
            "capability_overlap": base,
            "cost_disruption": base * 0.9,
            "switching_ease": base * 0.8,
            "deployment_speed": base * 0.85,
            "moat_erosion": base * 0.75,
        }

    # Average severity across threat vectors
    avg_severity = sum(tv.impact_severity for tv in target.threat_vectors) / len(target.threat_vectors)
    max_severity = max(tv.impact_severity for tv in target.threat_vectors)

    return {
        "capability_overlap": max_severity,
        "cost_disruption": avg_severity * 0.95,  # AI is almost always cheaper
        "switching_ease": avg_severity * 0.85,
        "deployment_speed": avg_severity * 0.90,
        "moat_erosion": avg_severity * 0.80,
    }


def score_target(target: TargetCompany, recent_signals: list[Signal] | None = None) -> DisruptionScore:
    """
    Calculate the full disruption score for a target company.

    Args:
        target: The target company to score
        recent_signals: Recent signals that may boost the score
    """
    base = _base_scores_for_target(target)
    category_mult = CATEGORY_MULTIPLIERS.get(target.category, 1.0)

    # Calculate signal boost from recent signals
    signal_boost = 0.0
    if recent_signals:
        for signal in recent_signals:
            impact = SIGNAL_IMPACT.get(signal.signal_type, 0.02)
            signal_boost += impact * signal.confidence

    signal_boost = min(0.15, signal_boost)  # Cap at 0.15

    return DisruptionScore(
        ticker=target.ticker,
        company_name=target.name,
        capability_overlap=base["capability_overlap"],
        cost_disruption=base["cost_disruption"],
        switching_ease=base["switching_ease"],
        deployment_speed=base["deployment_speed"],
        moat_erosion=base["moat_erosion"],
        category_multiplier=category_mult,
        signal_boost=signal_boost,
    )


def score_all_targets(recent_signals: list[Signal] | None = None) -> list[DisruptionScore]:
    """Score all target companies and return sorted by final score."""
    scores = []
    for target in TARGET_COMPANIES:
        # Filter signals relevant to this target
        target_signals = []
        if recent_signals:
            target_signals = [
                s for s in recent_signals
                if target.ticker in s.affected_tickers or s.is_ai_offensive
            ]

        score = score_target(target, target_signals)
        scores.append(score)
        logger.info(
            "%s (%s): composite=%.3f, category_mult=%.1f, signal_boost=%.3f, final=%.3f",
            target.name, target.ticker, score.composite_score,
            score.category_multiplier, score.signal_boost, score.final_score,
        )

    scores.sort(key=lambda s: s.final_score, reverse=True)
    return scores


def identify_catalysts(signals: list[Signal]) -> list[dict]:
    """
    Identify specific AI announcements that could serve as
    catalysts for shorting target companies.
    """
    catalysts = []

    for signal in signals:
        if not signal.is_ai_offensive:
            continue

        affected_targets = []
        for target in TARGET_COMPANIES:
            for tv in target.threat_vectors:
                if tv.ai_source == signal.ai_company:
                    # Check if the signal's content relates to this threat vector
                    signal_text = f"{signal.title} {signal.description}".lower()
                    capability_keywords = tv.capability.lower().split()
                    if any(kw in signal_text for kw in capability_keywords):
                        affected_targets.append({
                            "ticker": target.ticker,
                            "name": target.name,
                            "threat_vector": tv.capability,
                            "impact_severity": tv.impact_severity,
                        })

        if affected_targets:
            catalysts.append({
                "signal": signal,
                "affected_targets": affected_targets,
                "catalyst_strength": max(t["impact_severity"] for t in affected_targets),
            })

    catalysts.sort(key=lambda c: c["catalyst_strength"], reverse=True)
    return catalysts
