import json
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple

import anthropic

from backend.config import settings
from backend.database import get_reviews_by_timeframe, get_setting
from backend.models import (
    TimeframeAnalysisRequest,
    TimeframeAnalysisResponse,
    ActionableCorrection,
    ReviewAnalysis,
    SentimentType
)

logger = logging.getLogger("reviewpilot.timeframe")

WORD_TO_NUMBER = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "fourteen": 14,
    "thirty": 30,
    "sixty": 60,
    "ninety": 90
}

def parse_natural_timeframe(
    query: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Tuple[datetime, datetime, str]:
    """
    Parses natural language timeframe queries or ISO dates into UTC datetime bounds.
    Examples:
    - 'past two days' -> (now - 2d, now, 'past two days')
    - 'last one week' -> (now - 7d, now, 'last one week')
    - 'past one month' -> (now - 30d, now, 'past one month')
    - 'today' -> (start of today UTC, now, 'today')
    - 'yesterday' -> (start of yesterday UTC, end of yesterday UTC, 'yesterday')
    """
    now_utc = datetime.now(timezone.utc)

    # 1. Handle explicit ISO start_date and end_date if provided
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.strip()).replace(tzinfo=timezone.utc)
            if end_date:
                end_dt = datetime.fromisoformat(end_date.strip()).replace(
                    hour=23, minute=59, second=59, tzinfo=timezone.utc
                )
            else:
                end_dt = now_utc
            return start_dt, end_dt, f"from {start_date} to {end_date or 'now'}"
        except Exception as e:
            logger.warning(f"Error parsing explicit start_date '{start_date}': {e}")

    raw_query = (query or "").lower().strip()
    if not raw_query:
        raw_query = "past 7 days"

    # 2. Known colloquial phrases
    if "today" in raw_query:
        start_dt = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        return start_dt, now_utc, "today"

    if "yesterday" in raw_query:
        start_dt = (now_utc - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = start_dt.replace(hour=23, minute=59, second=59)
        return start_dt, end_dt, "yesterday"

    # Replace written number words with digits (e.g. 'two days' -> '2 days')
    normalized_query = raw_query
    for word, num in WORD_TO_NUMBER.items():
        pattern = rf"\b{word}\b"
        normalized_query = re.sub(pattern, str(num), normalized_query)

    # 3. Match quantities and units
    # Matches patterns like: 'past 2 days', 'last 1 week', '30 days', 'last 48 hours'
    match = re.search(r"(\d+)\s*(hour|day|week|month|year)s?", normalized_query)
    if match:
        quantity = int(match.group(1))
        unit = match.group(2)

        if unit == "hour":
            start_dt = now_utc - timedelta(hours=quantity)
        elif unit == "day":
            start_dt = now_utc - timedelta(days=quantity)
        elif unit == "week":
            start_dt = now_utc - timedelta(weeks=quantity)
        elif unit == "month":
            start_dt = now_utc - timedelta(days=quantity * 30)
        elif unit == "year":
            start_dt = now_utc - timedelta(days=quantity * 365)
        else:
            start_dt = now_utc - timedelta(days=7)

        return start_dt, now_utc, raw_query

    # 4. Standard shortcuts
    if "week" in raw_query:
        return now_utc - timedelta(days=7), now_utc, "past 7 days"
    if "month" in raw_query:
        return now_utc - timedelta(days=30), now_utc, "past 30 days"
    if "quarter" in raw_query:
        return now_utc - timedelta(days=90), now_utc, "past 90 days"
    if "year" in raw_query:
        return now_utc - timedelta(days=365), now_utc, "past 365 days"

    # Default fallback: past 7 days
    return now_utc - timedelta(days=7), now_utc, "past 7 days"


async def analyze_timeframe_reviews(
    request: TimeframeAnalysisRequest
) -> TimeframeAnalysisResponse:
    """
    Core dynamic time-based filtering and analysis workflow:
    1. Parses natural language timeframe or ISO dates into UTC window.
    2. Fetches only reviews from that specific period.
    3. Calculates total, positive %, neutral %, negative %, and urgent counts.
    4. Analyzes negative and urgent reviews to extract specific complaints.
    5. Formulates actionable operational corrections and executive summary.
    """
    start_dt, end_dt, clean_label = parse_natural_timeframe(
        query=request.timeframe,
        start_date=request.start_date,
        end_date=request.end_date
    )

    start_iso = start_dt.isoformat()
    end_iso = end_dt.isoformat()

    # Query reviews from database within this specific timeframe
    reviews = get_reviews_by_timeframe(
        start_iso=start_iso,
        end_iso=end_iso,
        platform=request.platform
    )

    total_reviews = len(reviews)
    positive_count = sum(1 for r in reviews if r.sentiment == SentimentType.POSITIVE)
    neutral_count = sum(1 for r in reviews if r.sentiment == SentimentType.NEUTRAL)
    negative_count = sum(1 for r in reviews if r.sentiment == SentimentType.NEGATIVE)
    urgent_count = sum(1 for r in reviews if r.is_urgent)

    if total_reviews > 0:
        pos_pct = round((positive_count / total_reviews) * 100, 1)
        neu_pct = round((neutral_count / total_reviews) * 100, 1)
        neg_pct = round((negative_count / total_reviews) * 100, 1)
    else:
        pos_pct = 0.0
        neu_pct = 0.0
        neg_pct = 0.0

    # Extract all reviews that contain negative sentiment, low star ratings, or urgent alerts
    negative_reviews = [
        r for r in reviews
        if r.sentiment == SentimentType.NEGATIVE or r.is_urgent or (r.star_rating is not None and r.star_rating <= 2.0)
    ]

    biz_name = request.business_name or get_setting("business_name") or settings.business_name or "Your Business"
    biz_type = request.business_type or get_setting("business_type") or settings.business_type or "Business"

    # Generate negative feedback points, actionable corrections, and executive summary
    points, corrections, detailed, summary = await synthesize_corrections_and_summary(
        negative_reviews=negative_reviews,
        total_reviews=total_reviews,
        positive_count=positive_count,
        negative_count=negative_count,
        urgent_count=urgent_count,
        pos_pct=pos_pct,
        neg_pct=neg_pct,
        timeframe_label=clean_label,
        business_name=biz_name,
        business_type=biz_type
    )

    return TimeframeAnalysisResponse(
        timeframe_query=request.timeframe,
        start_date=start_iso,
        end_date=end_iso,
        total_reviews=total_reviews,
        positive_count=positive_count,
        neutral_count=neutral_count,
        negative_count=negative_count,
        urgent_count=urgent_count,
        positive_percentage=pos_pct,
        neutral_percentage=neu_pct,
        negative_percentage=neg_pct,
        negative_feedback_points=points,
        actionable_corrections=corrections,
        detailed_corrections=detailed,
        recent_reviews=reviews[:15],
        executive_summary=summary
    )


async def synthesize_corrections_and_summary(
    negative_reviews: List[ReviewAnalysis],
    total_reviews: int,
    positive_count: int,
    negative_count: int,
    urgent_count: int,
    pos_pct: float,
    neg_pct: float,
    timeframe_label: str,
    business_name: str,
    business_type: str
) -> Tuple[List[str], List[str], List[ActionableCorrection], str]:
    """
    Passes filtered reviews to AI engine (Claude if API key available, or intelligent rule-based synthesizer)
    to calculate specific negative feedback points and actionable corrections.
    """
    if total_reviews == 0:
        return (
            [],
            [],
            [],
            f"No reviews were recorded for {business_name} during the selected period ({timeframe_label}). Ensure your review platforms are actively connected to collect upcoming customer feedback."
        )

    if not negative_reviews:
        summary = (
            f"Outstanding performance for {business_name} during the {timeframe_label}! "
            f"All {total_reviews} reviews analyzed were positive or neutral ({pos_pct}% positive satisfaction rate) "
            f"with zero negative complaints or urgent incidents reported."
        )
        corrections = [
            "Maintain current staff recognition programs to reinforce high customer satisfaction.",
            "Capitalize on high sentiment by sharing positive testimonials on social channels.",
            "Encourage satisfied customers to post direct 5-star ratings on Google and App Stores."
        ]
        detailed = [
            ActionableCorrection(
                area="Customer Retention",
                issue="High customer satisfaction but opportunity to amplify advocacy",
                action_plan="Prompt top reviewers with a personalized thank-you message and invite them to loyalty programs.",
                priority="Low"
            )
        ]
        return ([], corrections, detailed, summary)

    # Attempt LLM-based analysis if Anthropic Claude API key is configured
    claude_key = get_setting("anthropic_api_key") or settings.anthropic_api_key
    if claude_key and not claude_key.startswith("your_"):
        try:
            model = get_setting("anthropic_model") or settings.anthropic_model
            client = anthropic.AsyncAnthropic(api_key=claude_key)

            review_samples = "\n---\n".join([
                f"Review {i+1} [Rating: {r.star_rating or 'N/A'}, Category: {r.category}, Urgent: {r.is_urgent}]: \"{r.review_text}\""
                for i, r in enumerate(negative_reviews[:12])
            ])

            prompt = f"""You are ReviewPilot AI, a senior reputation and operations analyst for {business_name} ({business_type}).
During the timeframe ({timeframe_label}), the business received {total_reviews} total reviews:
- Positive: {positive_count} ({pos_pct}%)
- Negative: {negative_count} ({neg_pct}%)
- Urgent safety/legal incidents: {urgent_count}

Here are the customer complaints and negative feedback from this period:
{review_samples}

Analyze this customer feedback and provide a structured JSON response with:
1. "negative_feedback_points": A list of specific, concise bullet points detailing exact customer pain points (e.g. "Wait times at checkout exceeded 20 minutes", "Staff member was inattentive", "App crashed upon selecting payment method").
2. "actionable_corrections": A list of clear, concrete operational corrections the business owner must implement immediately to solve these root problems.
3. "detailed_corrections": A list of structured objects each with:
   - "area": Operational area (e.g. "Staff Training", "Quality Assurance", "App Performance", "Cleanliness", "Billing")
   - "issue": Brief diagnosis of the problem
   - "action_plan": Specific step-by-step remedy
   - "priority": "High" or "Medium"
4. "executive_summary": A professional 2-3 sentence executive briefing for the business owner highlighting overall health, critical risks, and priority next steps.

Respond strictly with valid JSON."""

            resp = await client.messages.create(
                model=model,
                max_tokens=1000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            resp_text = resp.content[0].text.strip()
            if "```json" in resp_text:
                resp_text = resp_text.split("```json")[1].split("```")[0].strip()
            elif "```" in resp_text:
                resp_text = resp_text.split("```")[1].split("```")[0].strip()

            parsed = json.loads(resp_text)
            detailed_objs = [
                ActionableCorrection(
                    area=d.get("area", "Operations"),
                    issue=d.get("issue", "Customer Friction"),
                    action_plan=d.get("action_plan", ""),
                    priority=d.get("priority", "High")
                )
                for d in parsed.get("detailed_corrections", [])
            ]

            return (
                parsed.get("negative_feedback_points", []),
                parsed.get("actionable_corrections", []),
                detailed_objs,
                parsed.get("executive_summary", "")
            )
        except Exception as e:
            logger.warning(f"Claude timeframe synthesis failed, falling back to rule synthesizer: {e}")

    # Fallback Rule-Based Operational Synthesizer
    return synthesize_rule_based_corrections(
        negative_reviews=negative_reviews,
        total_reviews=total_reviews,
        positive_count=positive_count,
        negative_count=negative_count,
        urgent_count=urgent_count,
        pos_pct=pos_pct,
        neg_pct=neg_pct,
        timeframe_label=timeframe_label,
        business_name=business_name
    )


def synthesize_rule_based_corrections(
    negative_reviews: List[ReviewAnalysis],
    total_reviews: int,
    positive_count: int,
    negative_count: int,
    urgent_count: int,
    pos_pct: float,
    neg_pct: float,
    timeframe_label: str,
    business_name: str
) -> Tuple[List[str], List[str], List[ActionableCorrection], str]:
    """
    Intelligent deterministic operational synthesizer that categorizes complaints,
    extracts quotes, and creates actionable operational solutions without third-party LLMs.
    """
    feedback_points: List[str] = []
    corrections: List[str] = []
    detailed: List[ActionableCorrection] = []

    # Cluster complaints by topic
    category_counts: Dict[str, int] = {}
    urgent_notes: List[str] = []

    for r in negative_reviews:
        cat = r.category or "General Experience"
        category_counts[cat] = category_counts.get(cat, 0) + 1
        if r.is_urgent and r.urgent_reason:
            urgent_notes.append(r.urgent_reason)

        # Extract quote snippets
        clean_text = r.review_text.strip()
        first_sentence = clean_text.split(".")[0].strip()
        if len(first_sentence) > 15 and len(feedback_points) < 6:
            feedback_points.append(f"\"{first_sentence}\" ({cat})")

    # If feedback points empty, add default category summaries
    if not feedback_points:
        for cat, cnt in category_counts.items():
            feedback_points.append(f"{cnt} customer complaint(s) regarding {cat}.")

    # Generate targeted operational corrections based on categories identified
    if any("Service" in k or "Staff" in k for k in category_counts):
        corrections.append("Conduct an immediate team huddle to review customer greeting standards and conflict resolution.")
        detailed.append(ActionableCorrection(
            area="Staff Conduct & Service",
            issue="Customers reported inattentive or unprofessional customer service.",
            action_plan="Implement daily 10-minute pre-shift briefings on active listening, welcoming greetings, and de-escalation protocols.",
            priority="High"
        ))

    if any("Wait" in k or "Speed" in k for k in category_counts):
        corrections.append("Reorganize peak-hour staffing and streamline order fulfillment workflows to reduce wait times.")
        detailed.append(ActionableCorrection(
            area="Speed of Service",
            issue="Bottlenecks causing customer delays during peak service hours.",
            action_plan="Audit queue times, cross-train floor staff to support prep during rushes, and set a 5-minute initial contact benchmark.",
            priority="High"
        ))

    if any("Food" in k or "Drink" in k or "Quality" in k for k in category_counts):
        corrections.append("Audit food prep temperature logs, ingredient freshness checks, and kitchen ticket timing.")
        detailed.append(ActionableCorrection(
            area="Product Quality & Kitchen",
            issue="Inconsistent food quality or presentation discrepancies.",
            action_plan="Enforce strict line checks before each shift and calibrate holding temperatures for all hot and cold items.",
            priority="High"
        ))

    if any("Clean" in k or "Hygiene" in k for k in category_counts):
        corrections.append("Introduce hourly restroom and floor sanitation checklists signed off by the shift supervisor.")
        detailed.append(ActionableCorrection(
            area="Cleanliness & Facility Hygiene",
            issue="Customer dissatisfaction regarding dining area or restroom cleanliness.",
            action_plan="Establish visible digital/physical sanitation logs checked at 45-minute intervals throughout opening hours.",
            priority="High"
        ))

    if any("App" in k or "Tech" in k or "Crash" in k for k in category_counts) or any("crash" in r.review_text.lower() for r in negative_reviews):
        corrections.append("Review error logs and patch crashes occurring during user onboarding and mobile checkout.")
        detailed.append(ActionableCorrection(
            area="App Performance & Stability",
            issue="App crashes or loading errors reported on mobile platforms.",
            action_plan="Deploy hotfix addressing memory leaks and inspect payment gateway timeout errors on iOS and Android builds.",
            priority="High"
        ))

    if any("Price" in k or "Billing" in k or "Order" in k for k in category_counts):
        corrections.append("Verify POS receipt itemization and clarify pricing tiers on visible signage and menus.")
        detailed.append(ActionableCorrection(
            area="Billing Transparency",
            issue="Unclear pricing, surprise surcharges, or billing discrepancies.",
            action_plan="Verify POS register pricing sync, audit receipt line items, and train cashiers to explain optional fees before payment.",
            priority="Medium"
        ))

    # General fallback correction if no specific category matched
    if not corrections:
        corrections.append("Reach out directly to unhappy customers to offer private resolution and demonstrate leadership ownership.")
        detailed.append(ActionableCorrection(
            area="Reputation Management",
            issue="Customer sentiment decline in recent timeframe.",
            action_plan="Reply to all reviews within 24 hours offering manager contact info to resolve concerns offline.",
            priority="Medium"
        ))

    # Add urgent safety protocol if urgent reviews detected
    if urgent_count > 0:
        urgent_text = f"🚨 URGENT: {urgent_count} critical incident(s) flagged ({', '.join(urgent_notes[:2]) or 'Safety/Compliance issue'})."
        feedback_points.insert(0, urgent_text)
        detailed.insert(0, ActionableCorrection(
            area="Risk & Safety Compliance",
            issue=f"{urgent_count} critical health, safety, or legal allegation(s) detected.",
            action_plan="Immediately contact the customer privately, conduct internal incident investigation, and notify management.",
            priority="High"
        ))

    # Executive Summary Briefing
    urgent_warning = f" Immediate intervention required for {urgent_count} urgent incident(s)." if urgent_count > 0 else ""
    summary = (
        f"Analysis for {business_name} during the {timeframe_label}: "
        f"{total_reviews} reviews were evaluated, recording {pos_pct}% positive and {neg_pct}% negative sentiment.{urgent_warning} "
        f"The primary focus area for leadership is {detailed[0].area if detailed else 'Customer Experience'}, "
        f"where targeted operational improvements will directly recover lost ratings."
    )

    return (feedback_points, corrections, detailed, summary)

