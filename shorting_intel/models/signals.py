"""
Signal models — intelligence events from AI companies and corporate responses.

Signals are the raw intelligence: an AI company made an announcement, a target
company filed earnings, a CEO departed, etc. The analyzers process these
signals into actionable assessments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SignalSource(Enum):
    """Where the intelligence signal originated."""

    ANTHROPIC_BLOG = "anthropic_blog"
    OPENAI_BLOG = "openai_blog"
    GOOGLE_AI_BLOG = "google_ai_blog"
    SEC_FILING = "sec_filing"
    EARNINGS_CALL = "earnings_call"
    NEWS_ARTICLE = "news_article"
    PRESS_RELEASE = "press_release"
    SOCIAL_MEDIA = "social_media"
    JOB_POSTINGS = "job_postings"
    PATENT_FILING = "patent_filing"


class SignalType(Enum):
    """Classification of the intelligence signal."""

    # AI Company Signals (offensive intelligence)
    NEW_MODEL_RELEASE = "new_model_release"
    CAPABILITY_ANNOUNCEMENT = "capability_announcement"
    API_LAUNCH = "api_launch"
    PRICING_CHANGE = "pricing_change"
    PARTNERSHIP = "partnership"
    AGENT_FRAMEWORK = "agent_framework"
    BENCHMARK_RESULT = "benchmark_result"

    # Target Company Signals (counter-intelligence)
    EARNINGS_MISS = "earnings_miss"
    GUIDANCE_CUT = "guidance_cut"
    LAYOFF = "layoff"
    CEO_CHANGE = "ceo_change"
    DEFENSIVE_PRODUCT_LAUNCH = "defensive_product_launch"
    LAWSUIT_FILED = "lawsuit_filed"
    ANALYST_DOWNGRADE = "analyst_downgrade"
    INSIDER_SELLING = "insider_selling"
    CUSTOMER_LOSS = "customer_loss"
    TRAFFIC_DECLINE = "traffic_decline"


class Urgency(Enum):
    """How quickly this signal should be acted upon."""

    IMMEDIATE = "immediate"  # Trade within hours
    SHORT_TERM = "short_term"  # Trade within days
    MEDIUM_TERM = "medium_term"  # Position within weeks
    LONG_TERM = "long_term"  # Thesis confirmation


@dataclass
class Signal:
    """A single intelligence signal."""

    signal_type: SignalType
    source: SignalSource
    title: str
    description: str
    url: str
    timestamp: datetime
    urgency: Urgency = Urgency.MEDIUM_TERM
    ai_company: str | None = None  # "anthropic", "openai", "google"
    affected_tickers: list[str] = field(default_factory=list)
    raw_content: str = ""
    confidence: float = 0.5  # 0.0 to 1.0 — how confident are we in this signal

    @property
    def is_ai_offensive(self) -> bool:
        """Is this an AI company announcement (offensive intelligence)?"""
        return self.signal_type in {
            SignalType.NEW_MODEL_RELEASE,
            SignalType.CAPABILITY_ANNOUNCEMENT,
            SignalType.API_LAUNCH,
            SignalType.PRICING_CHANGE,
            SignalType.PARTNERSHIP,
            SignalType.AGENT_FRAMEWORK,
            SignalType.BENCHMARK_RESULT,
        }

    @property
    def is_counter_intel(self) -> bool:
        """Is this a target company response (counter-intelligence)?"""
        return not self.is_ai_offensive


@dataclass
class ThreatAssessment:
    """Synthesized assessment combining multiple signals for a target."""

    ticker: str
    company_name: str
    overall_threat_score: float  # 0.0 to 1.0
    signals: list[Signal] = field(default_factory=list)
    disruption_timeline: str = ""  # "imminent", "6_months", "1_year", "2_years"
    recommended_action: str = ""  # "short_now", "watch", "avoid"
    counter_intel_flags: list[str] = field(default_factory=list)
    reasoning: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
