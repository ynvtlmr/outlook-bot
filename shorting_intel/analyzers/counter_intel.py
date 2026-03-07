"""
Counter-Intelligence Analyzer — Detecting Corporate Defense Patterns

The key insight: companies under existential AI threat exhibit predictable
behavioral patterns. This analyzer detects these patterns and distinguishes
between genuine adaptation and defensive posturing.

COUNTER-INTELLIGENCE FRAMEWORK:

1. DEFENSIVE AI PIVOT: Company rushes out an "AI-powered" product that's
   really just a wrapper around OpenAI/Anthropic APIs. This signals they
   have no proprietary AI capability and are vulnerable.

2. BUZZWORD OVERLOAD: Earnings calls suddenly stuffed with AI mentions
   when the company has no AI DNA. Frequency increase of >300% is a
   strong sell signal.

3. PARTNERSHIP THEATER: Announced "strategic AI partnerships" that
   generate press releases but no revenue. Common among desperate companies.

4. LAWSUIT AS LAST RESORT: Suing AI companies (like Chegg suing Google)
   signals the company has no competitive response and is trying to use
   courts to slow inevitable disruption.

5. CEO DEPARTURE UNDER FIRE: Leadership change during disruption usually
   means the board has lost confidence in the current strategy.

6. LAYOFF PATTERN ANALYSIS: Companies that announce layoffs while
   simultaneously claiming "AI transformation" are usually cutting costs
   because revenue is declining, not because they're becoming more efficient.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from shorting_intel.models.signals import Signal, SignalType, ThreatAssessment
from shorting_intel.models.targets import (
    TARGET_COMPANIES,
    CounterIntelSignal,
    TargetCompany,
    ThreatLevel,
)

logger = logging.getLogger(__name__)


@dataclass
class CounterIntelReport:
    """Analysis of a company's defensive posture against AI disruption."""

    ticker: str
    company_name: str
    defense_score: float  # 0.0 = no defense, 1.0 = strong defense (lower is worse for the company)
    deception_score: float  # 0.0 = genuine, 1.0 = all theater (higher means short opportunity)
    detected_patterns: list[str] = field(default_factory=list)
    genuine_adaptations: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    recommendation: str = ""


# === PATTERN WEIGHTS ===
# How much each counter-intelligence signal contributes to the deception score.
# Higher weight = stronger indicator that the company is losing, not adapting.

SIGNAL_DECEPTION_WEIGHTS: dict[CounterIntelSignal, float] = {
    CounterIntelSignal.LAWSUIT_AGAINST_AI: 0.25,  # Strongest desperation signal
    CounterIntelSignal.DELISTING_RISK: 0.25,  # Company is in death spiral
    CounterIntelSignal.CEO_DEPARTURE: 0.20,  # Leadership has no answer
    CounterIntelSignal.LAYOFF_RESTRUCTURING: 0.15,  # Cutting costs, not investing
    CounterIntelSignal.BUZZWORD_OVERLOAD: 0.15,  # All talk, no substance
    CounterIntelSignal.PARTNERSHIP_THEATER: 0.15,  # Press releases, no revenue
    CounterIntelSignal.GUIDANCE_CUT: 0.20,  # Business is actually declining
    CounterIntelSignal.DEFENSIVE_AI_PIVOT: 0.10,  # Rushed product, unlikely to succeed
    CounterIntelSignal.BUYBACK_WHILE_DECLINING: 0.10,  # Propping up stock price
    CounterIntelSignal.REVENUE_RECLASS: 0.15,  # Hiding the decline
}


def _analyze_defense_posture(target: TargetCompany) -> tuple[float, list[str]]:
    """
    Analyze how well the company is actually defending against AI disruption.

    Returns:
        Tuple of (defense_score, list of genuine adaptations found)
    """
    defense_score = 0.5  # Start neutral
    genuine_adaptations = []

    # Companies with existing AI/ML teams have better defense
    if target.threat_level == ThreatLevel.MODERATE:
        defense_score += 0.15
        genuine_adaptations.append("Moderate threat level suggests some competitive buffers")

    # Companies that have already declined >80% may be priced in
    if target.historical_decline_pct and target.historical_decline_pct < -80:
        defense_score -= 0.1
        # But note: already-crashed stocks have less shorting upside

    # Check for the worst combination of signals
    worst_signals = {
        CounterIntelSignal.LAYOFF_RESTRUCTURING,
        CounterIntelSignal.GUIDANCE_CUT,
        CounterIntelSignal.CEO_DEPARTURE,
    }
    has_worst = worst_signals.intersection(set(target.counter_intel_signals))
    if len(has_worst) >= 2:
        defense_score -= 0.2
        genuine_adaptations.append("ALERT: Multiple crisis signals detected simultaneously")

    return max(0.0, min(1.0, defense_score)), genuine_adaptations


def _calculate_deception_score(target: TargetCompany) -> tuple[float, list[str]]:
    """
    Calculate how much of the company's AI response is theater vs. genuine.

    Higher score = more deception = better shorting opportunity.

    Returns:
        Tuple of (deception_score, list of red flags)
    """
    deception_score = 0.0
    red_flags = []

    for signal in target.counter_intel_signals:
        weight = SIGNAL_DECEPTION_WEIGHTS.get(signal, 0.05)
        deception_score += weight

        # Generate specific red flag descriptions
        if signal == CounterIntelSignal.LAWSUIT_AGAINST_AI:
            red_flags.append(
                f"DESPERATION: {target.name} is suing AI companies — this is a last-resort "
                "move that signals they have no competitive response"
            )
        elif signal == CounterIntelSignal.DELISTING_RISK:
            red_flags.append(
                f"TERMINAL: {target.name} faces delisting risk — stock has declined to "
                "exchange minimum threshold"
            )
        elif signal == CounterIntelSignal.CEO_DEPARTURE:
            red_flags.append(
                f"LEADERSHIP VACUUM: {target.name} CEO departed during AI disruption — "
                "board has lost confidence in current strategy"
            )
        elif signal == CounterIntelSignal.LAYOFF_RESTRUCTURING:
            red_flags.append(
                f"COST CUTTING: {target.name} cutting workforce — presented as 'transformation' "
                "but actually revenue decline forcing headcount reduction"
            )
        elif signal == CounterIntelSignal.BUZZWORD_OVERLOAD:
            red_flags.append(
                f"THEATER: {target.name} earnings calls overloaded with AI buzzwords — "
                "no proprietary AI capability, just marketing spin"
            )
        elif signal == CounterIntelSignal.PARTNERSHIP_THEATER:
            red_flags.append(
                f"THEATER: {target.name} announcing 'AI partnerships' that generate "
                "press releases but no revenue"
            )
        elif signal == CounterIntelSignal.GUIDANCE_CUT:
            red_flags.append(
                f"DECLINE: {target.name} cut forward guidance — business fundamentals "
                "deteriorating as AI captures their market"
            )
        elif signal == CounterIntelSignal.DEFENSIVE_AI_PIVOT:
            red_flags.append(
                f"RUSHED: {target.name} launched defensive AI product — likely a thin "
                "wrapper around third-party APIs, not a durable competitive advantage"
            )
        elif signal == CounterIntelSignal.REVENUE_RECLASS:
            red_flags.append(
                f"HIDING: {target.name} reclassifying revenue categories — obscuring "
                "the true rate of decline in core business"
            )
        elif signal == CounterIntelSignal.BUYBACK_WHILE_DECLINING:
            red_flags.append(
                f"PROPPING: {target.name} buying back shares while revenue declines — "
                "artificially supporting stock price"
            )

    return min(1.0, deception_score), red_flags


def analyze_target(target: TargetCompany) -> CounterIntelReport:
    """
    Run full counter-intelligence analysis on a target company.

    This is the core analytical function that synthesizes all signals
    into an actionable report.
    """
    defense_score, genuine_adaptations = _analyze_defense_posture(target)
    deception_score, red_flags = _calculate_deception_score(target)

    detected_patterns = []
    for signal in target.counter_intel_signals:
        detected_patterns.append(f"{signal.value}: detected")

    # Generate recommendation
    if deception_score >= 0.6 and defense_score <= 0.3:
        recommendation = (
            f"STRONG SHORT CANDIDATE: {target.name} ({target.ticker}) shows high deception "
            f"score ({deception_score:.2f}) with weak defenses ({defense_score:.2f}). "
            "Multiple counter-intelligence patterns detected. The company's public AI narrative "
            "does not match its competitive reality."
        )
    elif deception_score >= 0.4:
        recommendation = (
            f"MODERATE SHORT CANDIDATE: {target.name} ({target.ticker}) shows meaningful "
            f"deception patterns ({deception_score:.2f}). Monitor for additional confirmation "
            "signals before establishing position."
        )
    elif target.threat_level == ThreatLevel.CRITICAL:
        recommendation = (
            f"WATCH — CRITICAL THREAT: {target.name} ({target.ticker}) faces existential "
            "AI threat but deception signals are limited. May be genuinely adapting or "
            "may be too early in the disruption cycle."
        )
    else:
        recommendation = (
            f"MONITOR: {target.name} ({target.ticker}) has moderate AI exposure. "
            "Continue monitoring for escalation signals."
        )

    return CounterIntelReport(
        ticker=target.ticker,
        company_name=target.name,
        defense_score=defense_score,
        deception_score=deception_score,
        detected_patterns=detected_patterns,
        genuine_adaptations=genuine_adaptations,
        red_flags=red_flags,
        recommendation=recommendation,
    )


def analyze_all_targets() -> list[CounterIntelReport]:
    """Run counter-intelligence analysis on all target companies."""
    reports = []
    for target in TARGET_COMPANIES:
        report = analyze_target(target)
        reports.append(report)
        logger.info(
            "%s (%s): defense=%.2f, deception=%.2f",
            target.name, target.ticker, report.defense_score, report.deception_score,
        )

    # Sort by deception score (highest = best short candidates)
    reports.sort(key=lambda r: r.deception_score, reverse=True)
    return reports


def generate_threat_assessments(
    targets: list[TargetCompany],
    ai_signals: list[Signal],
    counter_signals: list[Signal],
) -> list[ThreatAssessment]:
    """
    Generate threat assessments by cross-referencing AI signals with
    counter-intelligence from target companies.
    """
    assessments = []

    for target in targets:
        # Find relevant AI signals (offensive intel)
        relevant_ai = [s for s in ai_signals if s.is_ai_offensive]

        # Find relevant counter-intel signals for this ticker
        relevant_counter = [
            s for s in counter_signals
            if target.ticker in s.affected_tickers
        ]

        # Calculate overall threat score
        base_threat = {
            ThreatLevel.CRITICAL: 0.85,
            ThreatLevel.HIGH: 0.65,
            ThreatLevel.MODERATE: 0.45,
            ThreatLevel.WATCH: 0.25,
        }[target.threat_level]

        # Boost threat based on recent signals
        signal_boost = min(0.15, len(relevant_counter) * 0.05)
        ai_boost = min(0.10, len(relevant_ai) * 0.02)
        overall_threat = min(0.99, base_threat + signal_boost + ai_boost)

        # Determine timeline
        if target.historical_decline_pct and target.historical_decline_pct < -80:
            timeline = "already_disrupted"
        elif target.threat_level == ThreatLevel.CRITICAL:
            timeline = "imminent"
        elif target.threat_level == ThreatLevel.HIGH:
            timeline = "6_months"
        else:
            timeline = "1_year"

        # Determine action
        if overall_threat >= 0.75:
            action = "short_now"
        elif overall_threat >= 0.55:
            action = "prepare_short"
        else:
            action = "watch"

        # Counter-intel flags
        ci_report = analyze_target(target)
        flags = ci_report.red_flags

        assessment = ThreatAssessment(
            ticker=target.ticker,
            company_name=target.name,
            overall_threat_score=overall_threat,
            signals=relevant_ai + relevant_counter,
            disruption_timeline=timeline,
            recommended_action=action,
            counter_intel_flags=flags,
            reasoning=ci_report.recommendation,
        )
        assessments.append(assessment)

    assessments.sort(key=lambda a: a.overall_threat_score, reverse=True)
    return assessments
