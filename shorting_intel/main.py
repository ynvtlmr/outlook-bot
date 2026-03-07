"""
Shorting Intelligence Bot — Main Entry Point

Counter-intelligence framework for identifying shorting opportunities
in public markets based on AI developments from Anthropic, OpenAI,
and Google DeepMind/Gemini.

Usage:
    python -m shorting_intel                    # Full briefing
    python -m shorting_intel --signals-only     # Just fetch latest AI signals
    python -m shorting_intel --scores-only      # Just show disruption scores
    python -m shorting_intel --counter-intel    # Just counter-intelligence analysis
    python -m shorting_intel --json             # Output JSON format
    python -m shorting_intel --ticker CHGG      # Analyze specific ticker
    python -m shorting_intel --category education_tutoring  # Filter by category
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta, timezone

from shorting_intel.analyzers.counter_intel import (
    analyze_all_targets,
    analyze_target,
    generate_threat_assessments,
)
from shorting_intel.analyzers.disruption_scorer import score_all_targets, score_target
from shorting_intel.models.signals import Signal
from shorting_intel.models.targets import (
    TARGET_COMPANIES,
    DisruptionCategory,
    get_targets_by_category,
)
from shorting_intel.monitors.ai_announcements import fetch_ai_signals
from shorting_intel.monitors.news_monitor import scan_all_targets as scan_sec_filings
from shorting_intel.reports.generator import (
    generate_json_report,
    generate_text_report,
    save_report,
)

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def run_full_briefing(
    output_json: bool = False,
    save: bool = True,
    days_back: int = 30,
) -> str:
    """
    Run the full intelligence pipeline and generate a briefing.

    1. Collect AI signals (offensive intelligence)
    2. Collect SEC/news signals (counter-intelligence)
    3. Score disruption impact
    4. Run counter-intelligence analysis
    5. Generate threat assessments
    6. Produce briefing report
    """
    since = datetime.now(timezone.utc) - timedelta(days=days_back)

    # Phase 1: Collect offensive intelligence
    logger.info("Phase 1: Collecting AI signals (offensive intelligence)...")
    ai_signals = fetch_ai_signals(since=since)
    logger.info("Collected %d AI signals", len(ai_signals))

    # Phase 2: Collect counter-intelligence
    logger.info("Phase 2: Collecting counter-intelligence (SEC filings, news)...")
    counter_signals = scan_sec_filings()
    logger.info("Collected %d counter-intelligence signals", len(counter_signals))

    # Phase 3: Score disruption impact
    logger.info("Phase 3: Scoring disruption impact...")
    all_signals = ai_signals + counter_signals
    disruption_scores = score_all_targets(all_signals)

    # Phase 4: Counter-intelligence analysis
    logger.info("Phase 4: Running counter-intelligence analysis...")
    ci_reports = analyze_all_targets()

    # Phase 5: Generate threat assessments
    logger.info("Phase 5: Generating threat assessments...")
    assessments = generate_threat_assessments(TARGET_COMPANIES, ai_signals, counter_signals)

    # Phase 6: Generate report
    logger.info("Phase 6: Generating briefing report...")

    if output_json:
        json_report = generate_json_report(ai_signals, disruption_scores, ci_reports, assessments)
        report_text = json.dumps(json_report, indent=2, default=str)
    else:
        report_text = generate_text_report(
            ai_signals, counter_signals, disruption_scores, ci_reports, assessments,
        )

    if save:
        json_data = generate_json_report(ai_signals, disruption_scores, ci_reports, assessments)
        text_report = generate_text_report(
            ai_signals, counter_signals, disruption_scores, ci_reports, assessments,
        )
        save_report(text_report, json_data)

    return report_text


def run_signals_only(days_back: int = 30) -> str:
    """Just fetch and display latest AI signals."""
    since = datetime.now(timezone.utc) - timedelta(days=days_back)
    signals = fetch_ai_signals(since=since)

    lines = [">>> LATEST AI SIGNALS", "-" * 40, ""]
    for s in signals:
        lines.append(f"[{s.ai_company}] {s.title}")
        lines.append(f"  Type: {s.signal_type.value} | Urgency: {s.urgency.value}")
        lines.append(f"  Date: {s.timestamp.strftime('%Y-%m-%d')}")
        lines.append(f"  URL: {s.url}")
        lines.append("")

    if not signals:
        lines.append("  No signals found in the last {days_back} days.")

    return "\n".join(lines)


def run_scores_only() -> str:
    """Just show disruption scores for all targets."""
    scores = score_all_targets()

    lines = [
        ">>> DISRUPTION SCORES (All Targets)",
        "-" * 40,
        f"  {'Rank':<5} {'Ticker':<8} {'Company':<25} {'Score':<8} {'Overlap':<10} {'Cost':<8} {'Moat':<8}",
        f"  {'-'*5} {'-'*8} {'-'*25} {'-'*8} {'-'*10} {'-'*8} {'-'*8}",
    ]

    for i, s in enumerate(scores, 1):
        lines.append(
            f"  {i:<5} {s.ticker:<8} {s.company_name:<25} {s.final_score:<8.3f} "
            f"{s.capability_overlap:<10.2f} {s.cost_disruption:<8.2f} {s.moat_erosion:<8.2f}"
        )

    return "\n".join(lines)


def run_counter_intel_only() -> str:
    """Just run counter-intelligence analysis."""
    reports = analyze_all_targets()

    lines = [">>> COUNTER-INTELLIGENCE ANALYSIS", "-" * 40, ""]
    for r in reports:
        lines.append(f"{r.ticker:<8} {r.company_name}")
        lines.append(f"  Defense: {r.defense_score:.2f} | Deception: {r.deception_score:.2f}")
        for flag in r.red_flags:
            lines.append(f"  - {flag}")
        lines.append(f"  >> {r.recommendation}")
        lines.append("")

    return "\n".join(lines)


def run_single_ticker(ticker: str) -> str:
    """Deep-dive analysis of a single ticker."""
    target = next((t for t in TARGET_COMPANIES if t.ticker.upper() == ticker.upper()), None)
    if not target:
        return f"Ticker '{ticker}' not found in target database. Available: {', '.join(t.ticker for t in TARGET_COMPANIES)}"

    score = score_target(target)
    ci_report = analyze_target(target)

    lines = [
        f">>> DEEP DIVE: {target.name} ({target.ticker})",
        "=" * 60,
        "",
        f"Exchange:       {target.exchange}",
        f"Category:       {target.category.value}",
        f"Threat Level:   {target.threat_level.value}",
        "",
        "--- DISRUPTION THESIS ---",
        target.disruption_thesis,
        "",
        "--- DISRUPTION SCORE ---",
        f"  Final Score:        {score.final_score:.3f}",
        f"  Capability Overlap: {score.capability_overlap:.2f}",
        f"  Cost Disruption:    {score.cost_disruption:.2f}",
        f"  Switching Ease:     {score.switching_ease:.2f}",
        f"  Deployment Speed:   {score.deployment_speed:.2f}",
        f"  Moat Erosion:       {score.moat_erosion:.2f}",
        f"  Category Mult:      {score.category_multiplier:.1f}x",
        "",
        "--- THREAT VECTORS ---",
    ]

    for tv in target.threat_vectors:
        lines.append(f"  [{tv.ai_source}] {tv.capability}: {tv.description}")
        lines.append(f"    Impact Severity: {tv.impact_severity:.2f}")

    lines.extend([
        "",
        "--- COUNTER-INTELLIGENCE ---",
        f"  Defense Score:   {ci_report.defense_score:.2f}",
        f"  Deception Score: {ci_report.deception_score:.2f}",
        "",
        "  Red Flags:",
    ])

    for flag in ci_report.red_flags:
        lines.append(f"    - {flag}")

    if target.key_metrics_to_watch:
        lines.extend([
            "",
            "--- KEY METRICS TO MONITOR ---",
        ])
        for metric in target.key_metrics_to_watch:
            lines.append(f"  - {metric}")

    if target.historical_decline_pct:
        lines.extend([
            "",
            f"--- HISTORICAL DECLINE: {target.historical_decline_pct:.0f}% ---",
        ])

    if target.notes:
        lines.extend(["", f"--- NOTES ---", target.notes])

    lines.extend([
        "",
        "--- RECOMMENDATION ---",
        ci_report.recommendation,
    ])

    return "\n".join(lines)


def run_category_filter(category_name: str) -> str:
    """Show all targets in a specific disruption category."""
    try:
        category = DisruptionCategory(category_name)
    except ValueError:
        categories = [c.value for c in DisruptionCategory]
        return f"Unknown category '{category_name}'. Available: {', '.join(categories)}"

    targets = get_targets_by_category(category)
    if not targets:
        return f"No targets found in category '{category_name}'."

    scores = [score_target(t) for t in targets]
    scores.sort(key=lambda s: s.final_score, reverse=True)

    lines = [
        f">>> CATEGORY: {category.value.upper().replace('_', ' ')}",
        "-" * 40,
        f"  Targets: {len(targets)}",
        "",
    ]

    for score in scores:
        target = next(t for t in targets if t.ticker == score.ticker)
        lines.append(f"  {score.ticker:<8} {score.company_name:<25} Score: {score.final_score:.3f}  [{target.threat_level.value}]")
        lines.append(f"    {target.disruption_thesis[:100]}...")
        lines.append("")

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Shorting Intelligence Bot — AI Disruption Counter-Intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m shorting_intel                           Full briefing
  python -m shorting_intel --signals-only            Latest AI signals
  python -m shorting_intel --scores-only             Disruption scores
  python -m shorting_intel --counter-intel           Counter-intelligence analysis
  python -m shorting_intel --ticker CHGG             Deep dive on Chegg
  python -m shorting_intel --category education_tutoring  Filter by category
  python -m shorting_intel --json                    JSON output
  python -m shorting_intel --json --save             Save report to disk
        """,
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--signals-only", action="store_true", help="Only fetch AI signals")
    mode_group.add_argument("--scores-only", action="store_true", help="Only show disruption scores")
    mode_group.add_argument("--counter-intel", action="store_true", help="Only counter-intel analysis")
    mode_group.add_argument("--ticker", type=str, help="Deep dive on specific ticker")
    mode_group.add_argument("--category", type=str, help="Filter by disruption category")

    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--save", action="store_true", help="Save report to disk")
    parser.add_argument("--days", type=int, default=30, help="Days of history to analyze (default: 30)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--no-fetch", action="store_true", help="Skip fetching live data (use cached/static only)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    setup_logging(args.verbose)

    try:
        if args.signals_only:
            output = run_signals_only(args.days)
        elif args.scores_only:
            output = run_scores_only()
        elif args.counter_intel:
            output = run_counter_intel_only()
        elif args.ticker:
            output = run_single_ticker(args.ticker)
        elif args.category:
            output = run_category_filter(args.category)
        else:
            output = run_full_briefing(
                output_json=args.json,
                save=args.save,
                days_back=args.days,
            )

        print(output)
        return 0

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception:
        logger.exception("Fatal error in intelligence pipeline")
        return 1


if __name__ == "__main__":
    sys.exit(main())
