"""
AI Announcement Monitor — Signals Intelligence Collection

Monitors Anthropic, OpenAI, and Google DeepMind for new announcements that
could create shorting opportunities. Uses RSS feeds, blog scraping, and API
endpoints to detect new model releases, capability announcements, and
pricing changes.

This is the "offensive intelligence" collector — tracking what the AI
companies are doing that threatens our target companies.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from shorting_intel.models.signals import Signal, SignalSource, SignalType, Urgency

logger = logging.getLogger(__name__)

# === INTELLIGENCE SOURCES ===
# These are the feeds and endpoints we monitor for AI company announcements.

AI_SOURCES: dict[str, dict] = {
    "anthropic": {
        "blog_rss": "https://www.anthropic.com/rss.xml",
        "blog_url": "https://www.anthropic.com/news",
        "research_url": "https://www.anthropic.com/research",
        "api_changelog": "https://docs.anthropic.com/en/docs/about-claude/models",
        "name": "Anthropic",
        "signal_source": SignalSource.ANTHROPIC_BLOG,
    },
    "openai": {
        "blog_rss": "https://openai.com/blog/rss.xml",
        "blog_url": "https://openai.com/blog",
        "research_url": "https://openai.com/research",
        "api_changelog": "https://platform.openai.com/docs/changelog",
        "name": "OpenAI",
        "signal_source": SignalSource.OPENAI_BLOG,
    },
    "google": {
        "blog_rss": "https://blog.google/technology/ai/rss/",
        "blog_url": "https://blog.google/technology/ai/",
        "deepmind_url": "https://deepmind.google/discover/blog/",
        "api_changelog": "https://ai.google.dev/gemini-api/docs/changelog",
        "name": "Google DeepMind / Gemini",
        "signal_source": SignalSource.GOOGLE_AI_BLOG,
    },
}

# Keywords that indicate a high-impact announcement
HIGH_IMPACT_KEYWORDS: list[str] = [
    "new model", "launch", "release", "announcing", "introducing",
    "agent", "agentic", "computer use", "tool use", "function calling",
    "code generation", "coding", "software engineer",
    "voice", "real-time", "multimodal", "vision", "video",
    "price", "pricing", "cost reduction", "free tier",
    "api", "sdk", "framework", "platform",
    "benchmark", "state-of-the-art", "sota", "surpass", "outperform",
    "enterprise", "business", "customer service", "support",
    "translation", "localization", "multilingual",
    "image generation", "text-to-image", "creative",
    "reasoning", "chain of thought", "planning",
]

# Keywords that indicate specific disruption categories
DISRUPTION_KEYWORDS: dict[str, list[str]] = {
    "education": ["education", "tutoring", "homework", "learning", "student", "course"],
    "customer_service": ["customer service", "support", "call center", "contact center", "chatbot", "conversational"],
    "content_creation": ["image generation", "content creation", "creative", "design", "stock photo", "media"],
    "data_labeling": ["annotation", "labeling", "training data", "synthetic data", "rlhf", "evaluation"],
    "translation": ["translation", "localization", "multilingual", "language"],
    "coding": ["code", "coding", "programming", "developer", "software engineering", "IDE"],
    "legal": ["legal", "contract", "document review", "compliance"],
    "financial": ["financial", "advisory", "wealth", "tax", "accounting"],
    "consulting": ["consulting", "services", "outsourcing", "implementation"],
    "search": ["search", "information retrieval", "knowledge"],
}


@dataclass
class FeedEntry:
    """A parsed entry from an RSS/Atom feed."""

    title: str
    url: str
    published: datetime
    summary: str
    source: str


def _parse_rss_feed(url: str, source_name: str) -> list[FeedEntry]:
    """Parse an RSS/Atom feed and return entries."""
    entries = []
    try:
        req = Request(url, headers={"User-Agent": "ShortingIntelBot/0.1"})
        with urlopen(req, timeout=15) as response:
            content = response.read()

        root = ElementTree.fromstring(content)

        # Handle both RSS and Atom feeds
        namespaces = {"atom": "http://www.w3.org/2005/Atom"}

        # Try RSS format first
        for item in root.iter("item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            description = item.findtext("description", "")

            published = _parse_date(pub_date) if pub_date else datetime.now(timezone.utc)

            entries.append(FeedEntry(
                title=title,
                url=link,
                published=published,
                summary=description[:500],
                source=source_name,
            ))

        # Try Atom format if no RSS items found
        if not entries:
            for entry in root.findall("atom:entry", namespaces):
                title = entry.findtext("atom:title", "", namespaces)
                link_elem = entry.find("atom:link", namespaces)
                link = link_elem.get("href", "") if link_elem is not None else ""
                updated = entry.findtext("atom:updated", "", namespaces)
                summary = entry.findtext("atom:summary", "", namespaces)

                published = _parse_date(updated) if updated else datetime.now(timezone.utc)

                entries.append(FeedEntry(
                    title=title,
                    url=link,
                    published=published,
                    summary=summary[:500] if summary else "",
                    source=source_name,
                ))

    except (URLError, ElementTree.ParseError, TimeoutError) as e:
        logger.warning("Failed to fetch feed %s: %s", url, e)

    return entries


def _parse_date(date_str: str) -> datetime:
    """Parse various date formats from feeds."""
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",  # RFC 822
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.now(timezone.utc)


def _classify_signal_type(title: str, summary: str) -> SignalType:
    """Classify an announcement into a signal type based on content."""
    text = f"{title} {summary}".lower()

    if any(kw in text for kw in ["new model", "launch", "release", "introducing", "announcing"]):
        return SignalType.NEW_MODEL_RELEASE
    if any(kw in text for kw in ["agent", "agentic", "computer use", "tool use"]):
        return SignalType.AGENT_FRAMEWORK
    if any(kw in text for kw in ["api", "sdk", "framework", "platform", "developer"]):
        return SignalType.API_LAUNCH
    if any(kw in text for kw in ["price", "pricing", "cost", "free"]):
        return SignalType.PRICING_CHANGE
    if any(kw in text for kw in ["benchmark", "sota", "state-of-the-art", "outperform"]):
        return SignalType.BENCHMARK_RESULT
    if any(kw in text for kw in ["partner", "collaboration", "integration"]):
        return SignalType.PARTNERSHIP
    return SignalType.CAPABILITY_ANNOUNCEMENT


def _assess_urgency(title: str, summary: str) -> Urgency:
    """Assess how urgently this signal should be acted upon."""
    text = f"{title} {summary}".lower()

    immediate_keywords = ["launch", "available now", "today", "releasing", "live"]
    if any(kw in text for kw in immediate_keywords):
        return Urgency.SHORT_TERM

    high_impact_count = sum(1 for kw in HIGH_IMPACT_KEYWORDS if kw in text)
    if high_impact_count >= 3:
        return Urgency.SHORT_TERM
    if high_impact_count >= 1:
        return Urgency.MEDIUM_TERM
    return Urgency.LONG_TERM


def _calculate_confidence(title: str, summary: str) -> float:
    """Calculate confidence score based on keyword density."""
    text = f"{title} {summary}".lower()
    hit_count = sum(1 for kw in HIGH_IMPACT_KEYWORDS if kw in text)
    return min(0.95, 0.3 + (hit_count * 0.1))


def _find_affected_categories(title: str, summary: str) -> list[str]:
    """Identify which disruption categories an announcement affects."""
    text = f"{title} {summary}".lower()
    affected = []
    for category, keywords in DISRUPTION_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            affected.append(category)
    return affected


def fetch_ai_signals(since: datetime | None = None) -> list[Signal]:
    """
    Fetch latest signals from all AI company sources.

    Args:
        since: Only return signals after this datetime. Defaults to last 7 days.

    Returns:
        List of Signal objects representing AI company announcements.
    """
    if since is None:
        since = datetime(2020, 1, 1, tzinfo=timezone.utc)  # Get everything on first run

    all_signals: list[Signal] = []

    for company_key, source_config in AI_SOURCES.items():
        rss_url = source_config.get("blog_rss")
        if not rss_url:
            continue

        logger.info("Fetching signals from %s...", source_config["name"])
        entries = _parse_rss_feed(rss_url, source_config["name"])

        for entry in entries:
            if entry.published < since:
                continue

            signal = Signal(
                signal_type=_classify_signal_type(entry.title, entry.summary),
                source=source_config["signal_source"],
                title=entry.title,
                description=entry.summary,
                url=entry.url,
                timestamp=entry.published,
                urgency=_assess_urgency(entry.title, entry.summary),
                ai_company=company_key,
                confidence=_calculate_confidence(entry.title, entry.summary),
                raw_content=entry.summary,
            )
            all_signals.append(signal)

    all_signals.sort(key=lambda s: s.timestamp, reverse=True)
    logger.info("Collected %d AI signals", len(all_signals))
    return all_signals


def fetch_signals_for_company(company: str, since: datetime | None = None) -> list[Signal]:
    """Fetch signals for a specific AI company."""
    if company not in AI_SOURCES:
        raise ValueError(f"Unknown AI company: {company}. Must be one of: {list(AI_SOURCES.keys())}")

    if since is None:
        since = datetime(2020, 1, 1, tzinfo=timezone.utc)

    source_config = AI_SOURCES[company]
    rss_url = source_config.get("blog_rss")
    if not rss_url:
        return []

    entries = _parse_rss_feed(rss_url, source_config["name"])
    signals = []

    for entry in entries:
        if entry.published < since:
            continue

        signal = Signal(
            signal_type=_classify_signal_type(entry.title, entry.summary),
            source=source_config["signal_source"],
            title=entry.title,
            description=entry.summary,
            url=entry.url,
            timestamp=entry.published,
            urgency=_assess_urgency(entry.title, entry.summary),
            ai_company=company,
            confidence=_calculate_confidence(entry.title, entry.summary),
        )
        signals.append(signal)

    return signals
