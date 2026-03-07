"""
Report Generator — Actionable Intelligence Briefings

Generates structured reports combining:
- AI offensive intelligence (new capabilities)
- Counter-intelligence analysis (corporate defense patterns)
- Disruption scores (quantitative impact assessment)
- Recommended positions (actionable trading signals)

Reports are designed to be immediately actionable for shorting decisions.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from shorting_intel.analyzers.counter_intel import (
    CounterIntelReport,
    analyze_all_targets,
    generate_threat_assessments,
)
from shorting_intel.analyzers.disruption_scorer import (
    DisruptionScore,
    identify_catalysts,
    score_all_targets,
)
from shorting_intel.models.signals import Signal, ThreatAssessment
from shorting_intel.models.targets import TARGET_COMPANIES, ThreatLevel

logger = logging.getLogger(__name__)


def _threat_level_icon(level: ThreatLevel) -> str:
    return {
        ThreatLevel.CRITICAL: "[CRITICAL]",
        ThreatLevel.HIGH: "[HIGH]",
        ThreatLevel.MODERATE: "[MODERATE]",
        ThreatLevel.WATCH: "[WATCH]",
    }[level]


def generate_text_report(
    ai_signals: list[Signal],
    counter_signals: list[Signal],
    disruption_scores: list[DisruptionScore],
    counter_intel_reports: list[CounterIntelReport],
    threat_assessments: list[ThreatAssessment],
) -> str:
    """Generate a full text intelligence briefing."""
    now = datetime.now(timezone.utc)
    lines: list[str] = []

    lines.append("=" * 80)
    lines.append("  SHORTING INTELLIGENCE BRIEFING")
    lines.append("  Counter-Intelligence Framework for AI Disruption Analysis")
    lines.append(f"  Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("=" * 80)
    lines.append("")

    # === EXECUTIVE SUMMARY ===
    lines.append(">>> EXECUTIVE SUMMARY")
    lines.append("-" * 40)

    critical_count = sum(1 for t in TARGET_COMPANIES if t.threat_level == ThreatLevel.CRITICAL)
    high_count = sum(1 for t in TARGET_COMPANIES if t.threat_level == ThreatLevel.HIGH)
    short_now = [a for a in threat_assessments if a.recommended_action == "short_now"]
    prepare_short = [a for a in threat_assessments if a.recommended_action == "prepare_short"]

    lines.append(f"  Targets Monitored:     {len(TARGET_COMPANIES)}")
    lines.append(f"  Critical Threats:      {critical_count}")
    lines.append(f"  High Threats:          {high_count}")
    lines.append(f"  AI Signals Collected:  {len(ai_signals)}")
    lines.append(f"  Counter-Intel Signals: {len(counter_signals)}")
    lines.append(f"  SHORT NOW:             {len(short_now)}")
    lines.append(f"  PREPARE SHORT:         {len(prepare_short)}")
    lines.append("")

    # === TOP SHORTING OPPORTUNITIES ===
    lines.append(">>> TOP SHORTING OPPORTUNITIES (Ranked by Disruption Score)")
    lines.append("-" * 40)

    for i, score in enumerate(disruption_scores[:10], 1):
        target = next((t for t in TARGET_COMPANIES if t.ticker == score.ticker), None)
        level_str = _threat_level_icon(target.threat_level) if target else ""

        lines.append(f"  {i}. {score.ticker:<8} {score.company_name:<25} Score: {score.final_score:.3f}  {level_str}")
        lines.append(f"     Capability Overlap: {score.capability_overlap:.2f}  |  Cost Disruption: {score.cost_disruption:.2f}")
        lines.append(f"     Switching Ease: {score.switching_ease:.2f}     |  Moat Erosion: {score.moat_erosion:.2f}")

        if target and target.historical_decline_pct:
            lines.append(f"     Historical Decline: {target.historical_decline_pct:.0f}%")

        lines.append("")

    # === COUNTER-INTELLIGENCE ANALYSIS ===
    lines.append(">>> COUNTER-INTELLIGENCE ANALYSIS")
    lines.append("    (Companies sorted by deception score — higher = more theater, less substance)")
    lines.append("-" * 40)

    for report in counter_intel_reports[:10]:
        lines.append(f"  {report.ticker:<8} {report.company_name}")
        lines.append(f"     Defense Score:   {report.defense_score:.2f}  (lower = weaker defense)")
        lines.append(f"     Deception Score: {report.deception_score:.2f}  (higher = more theater)")

        if report.red_flags:
            lines.append("     Red Flags:")
            for flag in report.red_flags[:3]:
                lines.append(f"       - {flag}")

        lines.append(f"     >> {report.recommendation}")
        lines.append("")

    # === RECENT AI SIGNALS ===
    if ai_signals:
        lines.append(">>> RECENT AI SIGNALS (Offensive Intelligence)")
        lines.append("-" * 40)

        for signal in ai_signals[:15]:
            lines.append(f"  [{signal.ai_company or 'unknown'}] {signal.title}")
            lines.append(f"     Type: {signal.signal_type.value}  |  Urgency: {signal.urgency.value}")
            lines.append(f"     URL: {signal.url}")
            lines.append("")

    # === THREAT ASSESSMENTS ===
    lines.append(">>> THREAT ASSESSMENTS (Cross-Referenced Intelligence)")
    lines.append("-" * 40)

    for assessment in threat_assessments[:10]:
        action_str = assessment.recommended_action.upper().replace("_", " ")
        lines.append(f"  {assessment.ticker:<8} {assessment.company_name:<25} [{action_str}]")
        lines.append(f"     Threat Score: {assessment.overall_threat_score:.2f}  |  Timeline: {assessment.disruption_timeline}")

        if assessment.counter_intel_flags:
            lines.append("     Counter-Intel Flags:")
            for flag in assessment.counter_intel_flags[:2]:
                lines.append(f"       - {flag}")
        lines.append("")

    # === CATALYSTS ===
    catalysts = identify_catalysts(ai_signals)
    if catalysts:
        lines.append(">>> POTENTIAL CATALYSTS")
        lines.append("    (AI announcements that could trigger target company declines)")
        lines.append("-" * 40)

        for catalyst in catalysts[:5]:
            sig = catalyst["signal"]
            lines.append(f"  Signal: {sig.title}")
            lines.append(f"  Source: {sig.ai_company}  |  Strength: {catalyst['catalyst_strength']:.2f}")
            lines.append("  Affected Targets:")
            for affected in catalyst["affected_targets"]:
                lines.append(f"    - {affected['ticker']} ({affected['name']}): {affected['threat_vector']}")
            lines.append("")

    # === WATCHLIST ===
    lines.append(">>> FULL WATCHLIST")
    lines.append("-" * 40)
    lines.append(f"  {'Ticker':<8} {'Company':<25} {'Category':<35} {'Threat':<10}")
    lines.append(f"  {'-'*8} {'-'*25} {'-'*35} {'-'*10}")

    for target in TARGET_COMPANIES:
        lines.append(
            f"  {target.ticker:<8} {target.name:<25} "
            f"{target.category.value:<35} {target.threat_level.value:<10}"
        )
    lines.append("")

    # === KEY METRICS TO MONITOR ===
    lines.append(">>> KEY METRICS TO MONITOR PER TARGET")
    lines.append("-" * 40)

    for target in TARGET_COMPANIES:
        if target.key_metrics_to_watch:
            metrics = ", ".join(target.key_metrics_to_watch)
            lines.append(f"  {target.ticker:<8}: {metrics}")
    lines.append("")

    lines.append("=" * 80)
    lines.append("  END OF BRIEFING")
    lines.append("  DISCLAIMER: This is research analysis, not financial advice.")
    lines.append("  Always conduct your own due diligence before trading.")
    lines.append("=" * 80)

    return "\n".join(lines)


def generate_json_report(
    ai_signals: list[Signal],
    disruption_scores: list[DisruptionScore],
    counter_intel_reports: list[CounterIntelReport],
    threat_assessments: list[ThreatAssessment],
) -> dict:
    """Generate a machine-readable JSON report for downstream consumption."""
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.0",
        "summary": {
            "total_targets": len(TARGET_COMPANIES),
            "short_now_count": sum(1 for a in threat_assessments if a.recommended_action == "short_now"),
            "prepare_short_count": sum(1 for a in threat_assessments if a.recommended_action == "prepare_short"),
            "ai_signals_count": len(ai_signals),
        },
        "top_shorts": [
            {
                "ticker": score.ticker,
                "company": score.company_name,
                "final_score": round(score.final_score, 4),
                "capability_overlap": round(score.capability_overlap, 3),
                "cost_disruption": round(score.cost_disruption, 3),
                "moat_erosion": round(score.moat_erosion, 3),
            }
            for score in disruption_scores[:10]
        ],
        "counter_intel": [
            {
                "ticker": report.ticker,
                "company": report.company_name,
                "defense_score": round(report.defense_score, 3),
                "deception_score": round(report.deception_score, 3),
                "red_flags": report.red_flags,
                "recommendation": report.recommendation,
            }
            for report in counter_intel_reports[:10]
        ],
        "threat_assessments": [
            {
                "ticker": a.ticker,
                "company": a.company_name,
                "threat_score": round(a.overall_threat_score, 3),
                "timeline": a.disruption_timeline,
                "action": a.recommended_action,
            }
            for a in threat_assessments
        ],
        "ai_signals": [
            {
                "title": s.title,
                "source": s.ai_company,
                "type": s.signal_type.value,
                "urgency": s.urgency.value,
                "url": s.url,
                "timestamp": s.timestamp.isoformat(),
            }
            for s in ai_signals[:20]
        ],
    }


def save_report(
    report_text: str,
    report_json: dict,
    output_dir: str | Path = "shorting_intel/data",
) -> tuple[Path, Path]:
    """Save both text and JSON reports to disk."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")

    text_path = output_path / f"briefing_{timestamp}.txt"
    json_path = output_path / f"briefing_{timestamp}.json"

    text_path.write_text(report_text)
    json_path.write_text(json.dumps(report_json, indent=2, default=str))

    logger.info("Reports saved to %s and %s", text_path, json_path)
    return text_path, json_path
