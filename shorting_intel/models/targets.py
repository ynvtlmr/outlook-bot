"""
Target company definitions — the intelligence dossier.

Each target represents a public company vulnerable to AI disruption from
Anthropic, OpenAI, or Google Gemini. Organized by disruption category with
counter-intelligence signals: what corporate defense moves look like when
a company is *actually* losing vs. genuinely adapting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DisruptionCategory(Enum):
    """Primary disruption vector from AI developments."""

    EDUCATION_TUTORING = "education_tutoring"
    CUSTOMER_SERVICE_CALL_CENTER = "customer_service_call_center"
    CONTENT_CREATION_MEDIA = "content_creation_media"
    DATA_LABELING_ANNOTATION = "data_labeling_annotation"
    TRANSLATION_LOCALIZATION = "translation_localization"
    SOFTWARE_SERVICES_CONSULTING = "software_services_consulting"
    SEARCH_ADVERTISING = "search_advertising"
    LEGAL_DOCUMENT_REVIEW = "legal_document_review"
    FINANCIAL_SERVICES = "financial_services"
    SAAS_PLATFORM = "saas_platform"
    FREELANCE_MARKETPLACE = "freelance_marketplace"


class ThreatLevel(Enum):
    """How existential is the AI threat to this company."""

    CRITICAL = "critical"  # Business model directly replaced by AI
    HIGH = "high"  # Major revenue streams threatened
    MODERATE = "moderate"  # Significant competitive pressure
    WATCH = "watch"  # Early signals of disruption


class CounterIntelSignal(Enum):
    """Corporate defense patterns that indicate a company is losing ground.

    These are the 'tells' — when a company does these things, it often means
    the disruption is real and they're scrambling, not genuinely adapting.
    """

    DEFENSIVE_AI_PIVOT = "defensive_ai_pivot"  # Rushed AI product launch
    LAYOFF_RESTRUCTURING = "layoff_restructuring"  # Workforce cuts blamed on "efficiency"
    GUIDANCE_CUT = "guidance_cut"  # Lowered forward guidance
    CEO_DEPARTURE = "ceo_departure"  # Leadership change during disruption
    DELISTING_RISK = "delisting_risk"  # Stock below exchange minimum
    LAWSUIT_AGAINST_AI = "lawsuit_against_ai"  # Suing AI companies (desperation signal)
    BUZZWORD_OVERLOAD = "buzzword_overload"  # Earnings calls stuffed with "AI" mentions
    PARTNERSHIP_THEATER = "partnership_theater"  # Announced AI partnerships with no revenue
    BUYBACK_WHILE_DECLINING = "buyback_while_declining"  # Share buybacks masking decline
    REVENUE_RECLASS = "revenue_reclass"  # Reclassifying revenue to hide decline


@dataclass
class AIThreatVector:
    """Specific AI capability that threatens this company."""

    capability: str  # e.g. "code generation", "content creation", "agent workflows"
    ai_source: str  # "anthropic", "openai", "google"
    description: str
    impact_severity: float  # 0.0 to 1.0


@dataclass
class TargetCompany:
    """A public company identified as vulnerable to AI disruption."""

    ticker: str
    name: str
    category: DisruptionCategory
    threat_level: ThreatLevel
    exchange: str  # NYSE, NASDAQ, etc.
    disruption_thesis: str  # Why AI threatens this company
    threat_vectors: list[AIThreatVector] = field(default_factory=list)
    counter_intel_signals: list[CounterIntelSignal] = field(default_factory=list)
    key_metrics_to_watch: list[str] = field(default_factory=list)
    historical_decline_pct: float | None = None  # Already experienced decline
    notes: str = ""


# === THE INTELLIGENCE DOSSIER ===
# Research-backed list of companies vulnerable to AI disruption.

TARGET_COMPANIES: list[TargetCompany] = [
    # ─── EDUCATION & TUTORING ───────────────────────────────────────────
    TargetCompany(
        ticker="CHGG",
        name="Chegg",
        category=DisruptionCategory.EDUCATION_TUTORING,
        threat_level=ThreatLevel.CRITICAL,
        exchange="NYSE",
        disruption_thesis=(
            "Students use ChatGPT/Claude/Gemini for free instead of paying $20/mo for homework help. "
            "Market cap collapsed from $14B (2021) to ~$190M (2024). Lost 500K+ subscribers. "
            "Laid off 67% of workforce across 2025. At risk of NYSE delisting."
        ),
        threat_vectors=[
            AIThreatVector("homework solving", "openai", "ChatGPT solves problems students paid Chegg for", 0.95),
            AIThreatVector("tutoring", "anthropic", "Claude provides step-by-step explanations", 0.90),
            AIThreatVector("multimodal problem solving", "google", "Gemini reads photos of problems", 0.90),
        ],
        counter_intel_signals=[
            CounterIntelSignal.CEO_DEPARTURE,
            CounterIntelSignal.LAYOFF_RESTRUCTURING,
            CounterIntelSignal.DELISTING_RISK,
            CounterIntelSignal.LAWSUIT_AGAINST_AI,
            CounterIntelSignal.DEFENSIVE_AI_PIVOT,
        ],
        key_metrics_to_watch=["subscriber_count", "revenue_per_user", "search_traffic", "quarterly_revenue"],
        historical_decline_pct=-99.0,
        notes="CheggMate AI product failed. CEO admitted 'it was never a thing.' Sued Google over AI Overviews.",
    ),
    TargetCompany(
        ticker="COUR",
        name="Coursera",
        category=DisruptionCategory.EDUCATION_TUTORING,
        threat_level=ThreatLevel.HIGH,
        exchange="NYSE",
        disruption_thesis=(
            "AI can teach any subject interactively, threatening demand for structured online courses. "
            "Stock tanked >10% in April 2024 alongside Chegg on AI fears. Professional certificates "
            "lose value when AI can demonstrate skills directly."
        ),
        threat_vectors=[
            AIThreatVector("interactive tutoring", "openai", "ChatGPT replaces course content consumption", 0.75),
            AIThreatVector("skill demonstration", "anthropic", "AI agents demonstrate skills, reducing cert value", 0.60),
        ],
        counter_intel_signals=[
            CounterIntelSignal.GUIDANCE_CUT,
            CounterIntelSignal.BUZZWORD_OVERLOAD,
        ],
        key_metrics_to_watch=["paid_learner_count", "enterprise_revenue", "course_completion_rates"],
        historical_decline_pct=-70.0,
    ),
    TargetCompany(
        ticker="PRSO",
        name="Pearson",
        category=DisruptionCategory.EDUCATION_TUTORING,
        threat_level=ThreatLevel.HIGH,
        exchange="NYSE",
        disruption_thesis=(
            "Textbook and assessment publisher. AI generates educational content and personalized "
            "assessments on demand. Higher ed increasingly questioning textbook requirements when "
            "AI can explain concepts better."
        ),
        threat_vectors=[
            AIThreatVector("content generation", "openai", "GPT generates textbook-quality explanations", 0.70),
            AIThreatVector("assessment generation", "anthropic", "Claude creates personalized practice problems", 0.65),
        ],
        counter_intel_signals=[
            CounterIntelSignal.DEFENSIVE_AI_PIVOT,
            CounterIntelSignal.PARTNERSHIP_THEATER,
        ],
        key_metrics_to_watch=["courseware_revenue", "digital_adoption_rate", "enrollment_trends"],
    ),

    # ─── CUSTOMER SERVICE / CALL CENTERS ────────────────────────────────
    TargetCompany(
        ticker="FIVN",
        name="Five9",
        category=DisruptionCategory.CUSTOMER_SERVICE_CALL_CENTER,
        threat_level=ThreatLevel.HIGH,
        exchange="NASDAQ",
        disruption_thesis=(
            "Cloud contact center platform. AI agents from Anthropic/OpenAI can handle complex "
            "customer service conversations, reducing need for contact center seats. Klarna replaced "
            "700 customer service agents with AI in 2024."
        ),
        threat_vectors=[
            AIThreatVector("conversational AI agents", "anthropic", "Claude handles multi-turn customer service", 0.80),
            AIThreatVector("voice AI", "openai", "GPT-4o real-time voice replaces phone agents", 0.75),
            AIThreatVector("multimodal support", "google", "Gemini handles visual + text customer queries", 0.70),
        ],
        counter_intel_signals=[
            CounterIntelSignal.DEFENSIVE_AI_PIVOT,
            CounterIntelSignal.BUZZWORD_OVERLOAD,
        ],
        key_metrics_to_watch=["seat_count_growth", "revenue_per_seat", "churn_rate", "ai_attach_rate"],
    ),
    TargetCompany(
        ticker="LPSN",
        name="LivePerson",
        category=DisruptionCategory.CUSTOMER_SERVICE_CALL_CENTER,
        threat_level=ThreatLevel.CRITICAL,
        exchange="NASDAQ",
        disruption_thesis=(
            "Conversational AI platform for customer engagement. Directly competed against by "
            "foundation model providers. Stock collapsed >90% from 2021 highs. Revenue declining "
            "as enterprises build directly on LLM APIs instead of using middleware."
        ),
        threat_vectors=[
            AIThreatVector("direct API access", "openai", "Enterprises call OpenAI API directly, skip middleware", 0.90),
            AIThreatVector("agent frameworks", "anthropic", "Claude agent SDK replaces conversational platforms", 0.85),
        ],
        counter_intel_signals=[
            CounterIntelSignal.CEO_DEPARTURE,
            CounterIntelSignal.LAYOFF_RESTRUCTURING,
            CounterIntelSignal.REVENUE_RECLASS,
        ],
        key_metrics_to_watch=["revenue_growth", "enterprise_customer_count", "net_retention_rate"],
        historical_decline_pct=-95.0,
    ),
    TargetCompany(
        ticker="CNXC",
        name="Concentrix",
        category=DisruptionCategory.CUSTOMER_SERVICE_CALL_CENTER,
        threat_level=ThreatLevel.HIGH,
        exchange="NASDAQ",
        disruption_thesis=(
            "Business process outsourcing giant with 300K+ employees handling customer service. "
            "AI agents directly replace human agents. Klarna case study showed AI replacing 700 "
            "agents. If 20% of volume shifts to AI, massive margin pressure."
        ),
        threat_vectors=[
            AIThreatVector("agent automation", "anthropic", "Claude agents handle full customer interactions", 0.80),
            AIThreatVector("voice replacement", "openai", "Real-time voice API replaces phone agents", 0.75),
        ],
        counter_intel_signals=[
            CounterIntelSignal.BUZZWORD_OVERLOAD,
            CounterIntelSignal.DEFENSIVE_AI_PIVOT,
        ],
        key_metrics_to_watch=["headcount", "revenue_per_employee", "attrition_rate", "ai_revenue_pct"],
    ),
    TargetCompany(
        ticker="TTEC",
        name="TTEC Holdings",
        category=DisruptionCategory.CUSTOMER_SERVICE_CALL_CENTER,
        threat_level=ThreatLevel.HIGH,
        exchange="NASDAQ",
        disruption_thesis=(
            "Customer experience technology and services. Revenue declining as AI automates "
            "the customer service workflows TTEC manages. Smaller scale makes them more "
            "vulnerable than larger BPO competitors."
        ),
        threat_vectors=[
            AIThreatVector("workflow automation", "openai", "AI agents automate entire CX workflows", 0.80),
            AIThreatVector("conversational AI", "anthropic", "Claude replaces managed service agents", 0.75),
        ],
        counter_intel_signals=[
            CounterIntelSignal.GUIDANCE_CUT,
            CounterIntelSignal.LAYOFF_RESTRUCTURING,
        ],
        key_metrics_to_watch=["revenue_growth", "operating_margin", "client_retention"],
        historical_decline_pct=-85.0,
    ),

    # ─── CONTENT CREATION / MEDIA ──────────────────────────────────────
    TargetCompany(
        ticker="GETY",
        name="Getty Images",
        category=DisruptionCategory.CONTENT_CREATION_MEDIA,
        threat_level=ThreatLevel.HIGH,
        exchange="NYSE",
        disruption_thesis=(
            "Stock photo/video provider. AI image generation (DALL-E, Midjourney, Stable Diffusion) "
            "directly replaces need to license stock photos. Sued Stability AI but the market has "
            "moved on. Enterprise customers increasingly use AI-generated imagery."
        ),
        threat_vectors=[
            AIThreatVector("image generation", "openai", "DALL-E/GPT-4o generate custom images on demand", 0.85),
            AIThreatVector("image generation", "google", "Gemini/Imagen create custom visuals", 0.80),
        ],
        counter_intel_signals=[
            CounterIntelSignal.LAWSUIT_AGAINST_AI,
            CounterIntelSignal.DEFENSIVE_AI_PIVOT,
            CounterIntelSignal.PARTNERSHIP_THEATER,
        ],
        key_metrics_to_watch=["download_volume", "revenue_per_download", "enterprise_renewals", "subscriber_count"],
    ),
    TargetCompany(
        ticker="SSTK",
        name="Shutterstock",
        category=DisruptionCategory.CONTENT_CREATION_MEDIA,
        threat_level=ThreatLevel.HIGH,
        exchange="NYSE",
        disruption_thesis=(
            "Stock media marketplace. AI-generated images are cheaper and more customizable. "
            "Shutterstock partnered with OpenAI to license training data, but this accelerates "
            "the very technology that makes their library less essential."
        ),
        threat_vectors=[
            AIThreatVector("image generation", "openai", "Partnership funds the tech replacing their business", 0.80),
            AIThreatVector("video generation", "google", "Veo generates stock-quality video", 0.70),
        ],
        counter_intel_signals=[
            CounterIntelSignal.PARTNERSHIP_THEATER,
            CounterIntelSignal.REVENUE_RECLASS,
        ],
        key_metrics_to_watch=["subscriber_count", "content_downloads", "ai_revenue_contribution"],
    ),

    # ─── DATA LABELING / ANNOTATION ────────────────────────────────────
    TargetCompany(
        ticker="APX",
        name="Appen",
        category=DisruptionCategory.DATA_LABELING_ANNOTATION,
        threat_level=ThreatLevel.CRITICAL,
        exchange="ASX",
        disruption_thesis=(
            "Human data labeling company. AI models increasingly self-improve via RLHF with "
            "synthetic data, reducing need for human annotation. Appen's stock collapsed >95% "
            "from 2020 highs. Revenue in freefall as big tech cuts annotation budgets."
        ),
        threat_vectors=[
            AIThreatVector("synthetic data generation", "openai", "Models generate own training data", 0.90),
            AIThreatVector("self-improvement", "anthropic", "Constitutional AI reduces human labeling needs", 0.85),
            AIThreatVector("auto-labeling", "google", "Gemini auto-labels data at scale", 0.85),
        ],
        counter_intel_signals=[
            CounterIntelSignal.LAYOFF_RESTRUCTURING,
            CounterIntelSignal.CEO_DEPARTURE,
            CounterIntelSignal.GUIDANCE_CUT,
        ],
        key_metrics_to_watch=["revenue_growth", "project_count", "revenue_per_project", "customer_concentration"],
        historical_decline_pct=-95.0,
    ),
    TargetCompany(
        ticker="TIXT",
        name="TELUS International (TELUS Digital)",
        category=DisruptionCategory.DATA_LABELING_ANNOTATION,
        threat_level=ThreatLevel.HIGH,
        exchange="NYSE",
        disruption_thesis=(
            "Digital customer experience and AI data solutions. Their AI data annotation "
            "business faces same headwinds as Appen. Parent TELUS may need to absorb losses. "
            "Revenue declining as synthetic data reduces human annotation demand."
        ),
        threat_vectors=[
            AIThreatVector("synthetic data", "openai", "Synthetic data reduces annotation demand", 0.80),
            AIThreatVector("auto-evaluation", "anthropic", "AI self-evaluates without human raters", 0.75),
        ],
        counter_intel_signals=[
            CounterIntelSignal.GUIDANCE_CUT,
            CounterIntelSignal.LAYOFF_RESTRUCTURING,
        ],
        key_metrics_to_watch=["ai_data_solutions_revenue", "headcount", "margin_trends"],
        historical_decline_pct=-80.0,
    ),

    # ─── TRANSLATION / LOCALIZATION ────────────────────────────────────
    TargetCompany(
        ticker="RWS.L",
        name="RWS Holdings",
        category=DisruptionCategory.TRANSLATION_LOCALIZATION,
        threat_level=ThreatLevel.HIGH,
        exchange="LSE",
        disruption_thesis=(
            "World's largest language services provider. AI translation quality now rivals "
            "human translators for most commercial content. GPT-4/Claude produce near-human "
            "translations at 1/100th the cost. Enterprise clients shifting to AI+human review."
        ),
        threat_vectors=[
            AIThreatVector("machine translation", "openai", "GPT-4 produces publication-quality translations", 0.85),
            AIThreatVector("context-aware translation", "anthropic", "Claude handles nuanced technical translation", 0.80),
            AIThreatVector("multilingual models", "google", "Gemini natively supports 40+ languages", 0.85),
        ],
        counter_intel_signals=[
            CounterIntelSignal.DEFENSIVE_AI_PIVOT,
            CounterIntelSignal.LAYOFF_RESTRUCTURING,
        ],
        key_metrics_to_watch=["revenue_per_word", "translator_headcount", "ai_post_editing_volume"],
    ),

    # ─── SOFTWARE SERVICES / CONSULTING ────────────────────────────────
    TargetCompany(
        ticker="EPAM",
        name="EPAM Systems",
        category=DisruptionCategory.SOFTWARE_SERVICES_CONSULTING,
        threat_level=ThreatLevel.HIGH,
        exchange="NYSE",
        disruption_thesis=(
            "IT services and software engineering outsourcing. AI coding agents (Claude Code, "
            "GitHub Copilot, Cursor) dramatically increase developer productivity, reducing need "
            "to hire offshore engineering teams. Anthropic's agent SDK threatens consulting models."
        ),
        threat_vectors=[
            AIThreatVector("code generation", "anthropic", "Claude Code writes production-quality code autonomously", 0.85),
            AIThreatVector("code generation", "openai", "Codex/GPT-4 automates development tasks", 0.80),
            AIThreatVector("code generation", "google", "Gemini Code Assist rivals human developers", 0.75),
        ],
        counter_intel_signals=[
            CounterIntelSignal.BUZZWORD_OVERLOAD,
            CounterIntelSignal.GUIDANCE_CUT,
        ],
        key_metrics_to_watch=["headcount_growth", "revenue_per_employee", "utilization_rate", "deal_size_trends"],
    ),
    TargetCompany(
        ticker="GLOB",
        name="Globant",
        category=DisruptionCategory.SOFTWARE_SERVICES_CONSULTING,
        threat_level=ThreatLevel.HIGH,
        exchange="NYSE",
        disruption_thesis=(
            "Digital transformation consultancy. AI agents can now do the application development, "
            "UX design, and testing work that Globant charges premium rates for. "
            "Falling utilization rates signal reduced demand for human developers."
        ),
        threat_vectors=[
            AIThreatVector("full-stack development", "anthropic", "Claude agents build entire applications", 0.80),
            AIThreatVector("UI/UX generation", "openai", "GPT-4o generates and iterates on designs", 0.70),
        ],
        counter_intel_signals=[
            CounterIntelSignal.BUZZWORD_OVERLOAD,
            CounterIntelSignal.DEFENSIVE_AI_PIVOT,
        ],
        key_metrics_to_watch=["revenue_growth", "headcount", "margin_trends"],
    ),
    TargetCompany(
        ticker="WIT",
        name="Wipro",
        category=DisruptionCategory.SOFTWARE_SERVICES_CONSULTING,
        threat_level=ThreatLevel.MODERATE,
        exchange="NYSE",
        disruption_thesis=(
            "Indian IT services giant. AI reduces demand for low-complexity software maintenance "
            "and testing work that comprises a significant portion of revenue. Larger scale "
            "provides some buffer but margin pressure is real."
        ),
        threat_vectors=[
            AIThreatVector("code maintenance", "openai", "AI automates legacy code maintenance", 0.65),
            AIThreatVector("testing automation", "anthropic", "Claude agents automate QA workflows", 0.60),
        ],
        counter_intel_signals=[
            CounterIntelSignal.BUZZWORD_OVERLOAD,
        ],
        key_metrics_to_watch=["deal_pipeline", "headcount", "attrition_rate", "margin_trends"],
    ),

    # ─── SAAS PLATFORMS UNDER PRESSURE ─────────────────────────────────
    TargetCompany(
        ticker="U",
        name="Unity Software",
        category=DisruptionCategory.SAAS_PLATFORM,
        threat_level=ThreatLevel.HIGH,
        exchange="NYSE",
        disruption_thesis=(
            "Game engine / real-time 3D platform. AI lowers switching costs — developers can use "
            "AI to recreate and migrate assets across platforms. AI-generated 3D content reduces "
            "need for Unity's asset marketplace. Down 59% YTD in 2026."
        ),
        threat_vectors=[
            AIThreatVector("3D content generation", "openai", "AI generates 3D assets, reducing marketplace value", 0.75),
            AIThreatVector("code migration", "anthropic", "AI agents migrate codebases between engines", 0.70),
        ],
        counter_intel_signals=[
            CounterIntelSignal.CEO_DEPARTURE,
            CounterIntelSignal.LAYOFF_RESTRUCTURING,
            CounterIntelSignal.REVENUE_RECLASS,
        ],
        key_metrics_to_watch=["developer_count", "create_solutions_revenue", "grow_solutions_revenue"],
        historical_decline_pct=-59.0,
        notes="Down 59% YTD 2026. CEO departed. Runtime fee controversy damaged trust.",
    ),
    TargetCompany(
        ticker="MDB",
        name="MongoDB",
        category=DisruptionCategory.SAAS_PLATFORM,
        threat_level=ThreatLevel.MODERATE,
        exchange="NASDAQ",
        disruption_thesis=(
            "Database platform. AI coding tools weaken database lock-in — developers can more "
            "easily switch between databases when AI handles the migration complexity. "
            "Per-seat licensing model threatened by AI-driven consumption models."
        ),
        threat_vectors=[
            AIThreatVector("database migration", "anthropic", "AI agents migrate between databases trivially", 0.60),
            AIThreatVector("code generation", "openai", "AI-generated code is database-agnostic", 0.55),
        ],
        counter_intel_signals=[
            CounterIntelSignal.BUZZWORD_OVERLOAD,
        ],
        key_metrics_to_watch=["atlas_revenue_growth", "customer_count", "net_expansion_rate"],
    ),

    # ─── FREELANCE / GIG PLATFORMS ─────────────────────────────────────
    TargetCompany(
        ticker="FVRR",
        name="Fiverr",
        category=DisruptionCategory.FREELANCE_MARKETPLACE,
        threat_level=ThreatLevel.HIGH,
        exchange="NYSE",
        disruption_thesis=(
            "Freelance marketplace. AI directly replaces many gig categories: writing, "
            "graphic design, translation, basic coding, data entry. Businesses that used to "
            "hire freelancers now use AI tools directly."
        ),
        threat_vectors=[
            AIThreatVector("content writing", "openai", "GPT replaces freelance writers", 0.85),
            AIThreatVector("graphic design", "openai", "DALL-E replaces freelance designers", 0.75),
            AIThreatVector("coding tasks", "anthropic", "Claude Code replaces freelance developers", 0.80),
        ],
        counter_intel_signals=[
            CounterIntelSignal.DEFENSIVE_AI_PIVOT,
            CounterIntelSignal.BUZZWORD_OVERLOAD,
        ],
        key_metrics_to_watch=["active_buyers", "spend_per_buyer", "take_rate", "category_mix"],
        historical_decline_pct=-80.0,
    ),
    TargetCompany(
        ticker="UPWK",
        name="Upwork",
        category=DisruptionCategory.FREELANCE_MARKETPLACE,
        threat_level=ThreatLevel.HIGH,
        exchange="NASDAQ",
        disruption_thesis=(
            "Freelance talent marketplace. Same disruption as Fiverr — AI replaces entry-level "
            "freelance work in writing, design, translation, and coding. GSV reduced by companies "
            "bringing AI in-house instead of hiring freelancers."
        ),
        threat_vectors=[
            AIThreatVector("task automation", "openai", "GPT handles tasks previously outsourced", 0.80),
            AIThreatVector("coding automation", "anthropic", "Claude agents replace contract developers", 0.80),
        ],
        counter_intel_signals=[
            CounterIntelSignal.DEFENSIVE_AI_PIVOT,
            CounterIntelSignal.GUIDANCE_CUT,
        ],
        key_metrics_to_watch=["gsv_growth", "active_clients", "freelancer_earnings", "take_rate"],
        historical_decline_pct=-75.0,
    ),

    # ─── LEGAL / DOCUMENT REVIEW ───────────────────────────────────────
    TargetCompany(
        ticker="LEGN",
        name="Legend Biotech",
        category=DisruptionCategory.LEGAL_DOCUMENT_REVIEW,
        threat_level=ThreatLevel.WATCH,
        exchange="NASDAQ",
        disruption_thesis="Placeholder — primary legal tech companies are private. Watching sector.",
        notes="Most pure-play legal tech (Relativity, Everlaw) are private. Monitor for IPOs.",
    ),

    # ─── FINANCIAL SERVICES ────────────────────────────────────────────
    TargetCompany(
        ticker="SCHW",
        name="Charles Schwab",
        category=DisruptionCategory.FINANCIAL_SERVICES,
        threat_level=ThreatLevel.MODERATE,
        exchange="NYSE",
        disruption_thesis=(
            "Wealth management and brokerage. AI-driven financial advisors and tax tools "
            "threaten advisory fee models. AI can provide personalized financial planning "
            "that previously required human advisors."
        ),
        threat_vectors=[
            AIThreatVector("financial advisory", "openai", "AI provides personalized financial advice", 0.55),
            AIThreatVector("tax automation", "anthropic", "AI automates tax planning and preparation", 0.50),
        ],
        counter_intel_signals=[
            CounterIntelSignal.DEFENSIVE_AI_PIVOT,
        ],
        key_metrics_to_watch=["advisor_headcount", "advisory_fee_revenue", "digital_engagement"],
    ),
]


def get_targets_by_category(category: DisruptionCategory) -> list[TargetCompany]:
    return [t for t in TARGET_COMPANIES if t.category == category]


def get_targets_by_threat_level(level: ThreatLevel) -> list[TargetCompany]:
    return [t for t in TARGET_COMPANIES if t.threat_level == level]


def get_critical_targets() -> list[TargetCompany]:
    return get_targets_by_threat_level(ThreatLevel.CRITICAL)


def get_all_tickers() -> list[str]:
    return [t.ticker for t in TARGET_COMPANIES]
