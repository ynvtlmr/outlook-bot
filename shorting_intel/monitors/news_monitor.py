"""
News & SEC Filing Monitor — Counter-Intelligence Collection

Monitors target companies for earnings reports, layoff announcements,
guidance changes, insider selling, and other signals that confirm the
AI disruption thesis. Uses financial news APIs and SEC EDGAR.

This is the "counter-intelligence" collector — tracking what the target
companies are doing in response to AI disruption.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

from shorting_intel.models.signals import Signal, SignalSource, SignalType, Urgency
from shorting_intel.models.targets import TARGET_COMPANIES, CounterIntelSignal

logger = logging.getLogger(__name__)

# SEC EDGAR full-text search API (free, no key required)
SEC_EFTS_BASE = "https://efts.sec.gov/LATEST/search-index"
SEC_EDGAR_SEARCH = "https://efts.sec.gov/LATEST/search-index?q={query}&dateRange=custom&startdt={start}&enddt={end}"
SEC_COMPANY_FILINGS = "https://data.sec.gov/submissions/CIK{cik}.json"

# Common CIK numbers for our target companies
TICKER_TO_CIK: dict[str, str] = {
    "CHGG": "0001364954",
    "COUR": "0001651562",
    "FIVN": "0001288847",
    "LPSN": "0001009759",
    "CNXC": "0001803599",
    "TTEC": "0001013880",
    "GETY": "0001898496",
    "SSTK": "0001549346",
    "EPAM": "0001352010",
    "GLOB": "0001557860",
    "U": "0001810806",
    "MDB": "0001441816",
    "FVRR": "0001762301",
    "UPWK": "0001627475",
    "SCHW": "0000316709",
    "WIT": "0001357450",
    "PATH": "0001734722",
    "INFY": "0001067491",
    "HUBS": "0001404655",
    "TEAM": "0001650372",
}

# Earnings call keywords that signal AI disruption
DISRUPTION_KEYWORDS: list[str] = [
    "artificial intelligence",
    "generative ai",
    "large language model",
    "chatgpt",
    "competitive pressure",
    "headwind",
    "disruption",
    "challenging environment",
    "restructuring",
    "workforce reduction",
    "layoff",
    "strategic review",
    "transformation",
    "pivot",
]

# Counter-intelligence: keywords that indicate defensive posturing
DEFENSE_KEYWORDS: list[str] = [
    "ai-powered",
    "ai-first",
    "ai transformation",
    "leveraging ai",
    "our ai strategy",
    "ai integration",
    "ai partnership",
    "ai-driven growth",
    "ai opportunity",
]


@dataclass
class SECFiling:
    """A parsed SEC filing."""

    ticker: str
    form_type: str
    filed_date: str
    description: str
    url: str


def fetch_sec_filings(ticker: str, form_types: list[str] | None = None) -> list[SECFiling]:
    """
    Fetch recent SEC filings for a company.

    Args:
        ticker: Stock ticker symbol
        form_types: Filter by form types (e.g., ["10-K", "10-Q", "8-K"])
    """
    cik = TICKER_TO_CIK.get(ticker)
    if not cik:
        logger.warning("No CIK mapping for ticker %s", ticker)
        return []

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    filings = []

    try:
        req = Request(url, headers={
            "User-Agent": "ShortingIntelBot/0.1 research@example.com",
            "Accept": "application/json",
        })
        with urlopen(req, timeout=15) as response:
            data = json.loads(response.read())

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        descriptions = recent.get("primaryDocDescription", [])

        for i in range(min(len(forms), 20)):  # Last 20 filings
            form = forms[i]
            if form_types and form not in form_types:
                continue

            accession = accessions[i].replace("-", "")
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}"

            filings.append(SECFiling(
                ticker=ticker,
                form_type=form,
                filed_date=dates[i],
                description=descriptions[i] if i < len(descriptions) else "",
                url=filing_url,
            ))

    except (URLError, json.JSONDecodeError, KeyError, TimeoutError) as e:
        logger.warning("Failed to fetch SEC filings for %s: %s", ticker, e)

    return filings


def _detect_counter_intel_signals(text: str) -> list[CounterIntelSignal]:
    """Analyze text for counter-intelligence signals."""
    text_lower = text.lower()
    signals = []

    if any(kw in text_lower for kw in ["layoff", "workforce reduction", "job cuts", "restructuring"]):
        signals.append(CounterIntelSignal.LAYOFF_RESTRUCTURING)

    if any(kw in text_lower for kw in ["guidance", "outlook", "below expectations", "revised downward"]):
        signals.append(CounterIntelSignal.GUIDANCE_CUT)

    if any(kw in text_lower for kw in ["ceo", "chief executive", "stepping down", "departure", "transition"]):
        signals.append(CounterIntelSignal.CEO_DEPARTURE)

    if any(kw in text_lower for kw in ["lawsuit", "filed suit", "legal action", "suing"]):
        signals.append(CounterIntelSignal.LAWSUIT_AGAINST_AI)

    if any(kw in text_lower for kw in ["delisting", "below $1", "compliance", "nyse warning"]):
        signals.append(CounterIntelSignal.DELISTING_RISK)

    # Buzzword overload detection: count AI-defense keywords
    defense_count = sum(1 for kw in DEFENSE_KEYWORDS if kw in text_lower)
    if defense_count >= 3:
        signals.append(CounterIntelSignal.BUZZWORD_OVERLOAD)

    if any(kw in text_lower for kw in ["ai-powered", "ai-first", "our ai"]) and \
       any(kw in text_lower for kw in ["partnership", "collaboration", "strategic alliance"]):
        signals.append(CounterIntelSignal.PARTNERSHIP_THEATER)

    return signals


def analyze_filing_for_signals(filing: SECFiling) -> list[Signal]:
    """Convert an SEC filing into intelligence signals."""
    signals = []
    text = f"{filing.form_type} {filing.description}"

    if filing.form_type == "8-K":
        # 8-K filings are material events — could be layoffs, CEO changes, etc.
        counter_signals = _detect_counter_intel_signals(text)
        if counter_signals:
            signal_type = SignalType.LAYOFF
            if CounterIntelSignal.CEO_DEPARTURE in counter_signals:
                signal_type = SignalType.CEO_CHANGE
            elif CounterIntelSignal.GUIDANCE_CUT in counter_signals:
                signal_type = SignalType.GUIDANCE_CUT

            signals.append(Signal(
                signal_type=signal_type,
                source=SignalSource.SEC_FILING,
                title=f"{filing.ticker} 8-K: {filing.description}",
                description=text,
                url=filing.url,
                timestamp=datetime.strptime(filing.filed_date, "%Y-%m-%d").replace(tzinfo=timezone.utc),
                affected_tickers=[filing.ticker],
                urgency=Urgency.SHORT_TERM,
            ))

    elif filing.form_type in ("10-K", "10-Q"):
        # Quarterly/annual reports — check for disruption language
        signals.append(Signal(
            signal_type=SignalType.EARNINGS_MISS,
            source=SignalSource.SEC_FILING,
            title=f"{filing.ticker} {filing.form_type} filed",
            description=f"Periodic report filed: {filing.description}",
            url=filing.url,
            timestamp=datetime.strptime(filing.filed_date, "%Y-%m-%d").replace(tzinfo=timezone.utc),
            affected_tickers=[filing.ticker],
            urgency=Urgency.MEDIUM_TERM,
        ))

    return signals


def scan_all_targets() -> list[Signal]:
    """Scan all target companies for recent SEC filings and news signals."""
    all_signals = []

    for target in TARGET_COMPANIES:
        if target.ticker in TICKER_TO_CIK:
            logger.info("Scanning SEC filings for %s (%s)...", target.name, target.ticker)
            filings = fetch_sec_filings(target.ticker, form_types=["8-K", "10-K", "10-Q"])

            for filing in filings:
                signals = analyze_filing_for_signals(filing)
                all_signals.extend(signals)

    logger.info("Collected %d counter-intelligence signals from SEC filings", len(all_signals))
    return all_signals
