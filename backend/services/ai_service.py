import json
import logging
import re
from typing import Dict, Any, Optional
import anthropic
from backend.config import settings
from backend.database import get_setting
from backend.models import SentimentType, ReplyTone

logger = logging.getLogger("reviewpilot.ai")

SYSTEM_PROMPT = """You are ReviewPilot AI, an expert customer feedback analyst and reputation management specialist for small businesses (cafes, restaurants, salons, gyms, local retail).

Your job is to analyze customer reviews and generate professional, context-aware responses tailored to the specified business and tone.

You MUST respond strictly with a valid JSON object with the following exact keys:
{
  "sentiment": "Positive" | "Neutral" | "Negative",
  "sentiment_score": float between 0.50 and 1.00,
  "category": "Customer Service" | "Food & Drink Quality" | "Cleanliness & Hygiene" | "Wait Times & Speed" | "Pricing & Value" | "Ambience & Atmosphere" | "Facilities & Equipment" | "Billing & Orders" | "Staff Conduct" | "General Experience",
  "is_urgent": boolean (true ONLY if there is food poisoning/illness, physical safety risk, harassment/discrimination, police/legal threat, severe hygiene infestation, or severe financial fraud),
  "urgent_reason": string explaining the urgency or null if is_urgent is false,
  "reply": string containing the personalized, polite response
}

Rules for response generation:
- Tone options:
  * Friendly: Warm, conversational, appreciative, welcoming.
  * Professional: Polished, respectful, calm, composed.
  * Empathetic: Deeply apologetic, validating the customer's feelings, proactive solution-oriented.
  * Concise: Brief, direct, under 2-3 sentences.
- Never use placeholder brackets like [Your Name] or [Manager]. Write a complete, ready-to-post response signed off by the team at {business_name}.
- For negative or urgent reviews: Validate the frustration, provide an apology without admission of severe legal liability, and invite them to connect privately via email or in person.
- For positive reviews: Express authentic gratitude, highlight specific mentions (e.g. food items, staff member), and invite them back.
"""

def get_effective_api_key() -> Optional[str]:
    db_key = get_setting("anthropic_api_key")
    return db_key or settings.anthropic_api_key

def get_effective_model() -> str:
    db_model = get_setting("anthropic_model")
    return db_model or settings.anthropic_model

async def analyze_with_claude(
    review_text: str,
    tone: ReplyTone,
    business_name: str,
    business_type: str,
    api_key: str,
    model: str
) -> Dict[str, Any]:
    """Calls Anthropic Claude API to analyze sentiment and generate reply."""
    client = anthropic.AsyncAnthropic(api_key=api_key)

    user_prompt = f"""Business Name: {business_name}
Business Type: {business_type}
Selected Response Tone: {tone.value}

Customer Review:
\"\"\"{review_text}\"\"\"

Analyze this review according to your system instructions and return ONLY the JSON object."""

    message = await client.messages.create(
        model=model,
        max_tokens=600,
        temperature=0.3,
        system=SYSTEM_PROMPT.format(business_name=business_name, tone=tone.value),
        messages=[{"role": "user", "content": user_prompt}]
    )

    response_text = message.content[0].text.strip()
    
    # Extract JSON if enclosed in markdown fences
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    parsed = json.loads(response_text)
    return parsed

def analyze_review_fallback(
    review_text: str,
    tone: ReplyTone,
    business_name: str,
    business_type: str
) -> Dict[str, Any]:
    """
    Intelligent rule-based fallback when Anthropic API key is not configured or unavailable.
    Provides realistic sentiment classification, urgent threat detection, and context-aware replies.
    """
    lower = review_text.lower()

    # 1. Urgent triggers detection
    urgent_reason = None
    is_urgent = False

    if any(k in lower for k in ["food poison", "food poisoning", "salmonella", "vomit", "threw up", "stomach ache", "got sick", "hospital", "urgent care"]):
        is_urgent = True
        urgent_reason = "Health & food safety risk (customer reported illness or food poisoning)"
    elif any(k in lower for k in ["lawyer", "attorney", "lawsuit", "sue", "legal action", "police", "called the cops"]):
        is_urgent = True
        urgent_reason = "Legal or law enforcement escalation threat"
    elif any(k in lower for k in ["racist", "racism", "harass", "assault", "discrimina", "unsafe", "threatened", "inappropriate touch"]):
        is_urgent = True
        urgent_reason = "Customer safety or harassment/discrimination allegation"
    elif any(k in lower for k in ["cockroach", "roach", "rat", "mouse", "mice", "maggot", "infestation", "moldy", "black mold"]):
        is_urgent = True
        urgent_reason = "Severe hygiene or pest infestation hazard"
    elif any(k in lower for k in ["stole", "theft", "unauthorized charge", "credit card fraud", "scam"]):
        is_urgent = True
        urgent_reason = "Financial dispute or potential fraud allegation"

    # 2. Topic Categorization
    category = "General Experience"
    if any(k in lower for k in ["wait", "slow", "hour", "minutes", "delayed", "line", "took forever", "speed"]):
        category = "Wait Times & Speed"
    elif any(k in lower for k in ["rude", "attitude", "friendly", "waiter", "waitress", "server", "manager", "staff", "bartender", "host", "front desk"]):
        category = "Customer Service"
    elif any(k in lower for k in ["taste", "delicious", "cold food", "flavor", "coffee", "bland", "fresh", "undercooked", "overcooked", "meal", "drink", "cocktail", "burger", "pizza", "pastry"]):
        category = "Food & Drink Quality"
    elif any(k in lower for k in ["clean", "dirty", "filthy", "restroom", "bathroom", "table", "hygiene", "smell", "dust"]):
        category = "Cleanliness & Hygiene"
    elif any(k in lower for k in ["price", "expensive", "overpriced", "cost", "bill", "rip off", "value", "worth it"]):
        category = "Pricing & Value"
    elif any(k in lower for k in ["loud", "music", "decor", "vibe", "atmosphere", "ambience", "lighting", "seating", "cozy"]):
        category = "Ambience & Atmosphere"
    elif any(k in lower for k in ["gym", "equipment", "towel", "machine", "locker", "haircut", "styling", "nails", "massage"]):
        category = "Facilities & Equipment"
    elif any(k in lower for k in ["receipt", "charged", "billing", "refund", "tip", "payment"]):
        category = "Billing & Orders"

    # 3. Sentiment detection
    positive_words = ["amazing", "great", "excellent", "love", "loved", "fantastic", "best", "delicious", "wonderful", "friendly", "awesome", "perfect", "superb", "fresh", "favorite", "recommend"]
    negative_words = ["terrible", "awful", "horrible", "bad", "worst", "rude", "cold", "dirty", "slow", "overpriced", "disappointed", "waste", "never again", "disgusting", "unacceptable", "poor", "ruined"]

    pos_score = sum(1 for w in positive_words if w in lower)
    neg_score = sum(1 for w in negative_words if w in lower)

    if is_urgent or neg_score > pos_score or (neg_score > 0 and pos_score == 0):
        sentiment = SentimentType.NEGATIVE
        sentiment_score = 0.92 if is_urgent else min(0.70 + (neg_score * 0.08), 0.98)
    elif pos_score > neg_score:
        sentiment = SentimentType.POSITIVE
        sentiment_score = min(0.75 + (pos_score * 0.07), 0.99)
    else:
        sentiment = SentimentType.NEUTRAL
        sentiment_score = 0.68

    # 4. Context-aware reply generation
    reply = generate_fallback_reply(
        sentiment=sentiment,
        tone=tone,
        business_name=business_name,
        category=category,
        is_urgent=is_urgent,
        urgent_reason=urgent_reason,
        review_text=review_text
    )

    return {
        "sentiment": sentiment.value,
        "sentiment_score": round(sentiment_score, 2),
        "category": category,
        "is_urgent": is_urgent,
        "urgent_reason": urgent_reason,
        "reply": reply
    }

def generate_fallback_reply(
    sentiment: SentimentType,
    tone: ReplyTone,
    business_name: str,
    category: str,
    is_urgent: bool,
    urgent_reason: Optional[str],
    review_text: str
) -> str:
    """Generates a realistic, tailored reply according to sentiment and selected tone."""

    if is_urgent:
        if tone == ReplyTone.EMPATHETIC:
            return (
                f"We are deeply concerned to read this and take your feedback with the utmost seriousness. "
                f"Your health, safety, and satisfaction are paramount to us at {business_name}. "
                f"Please contact our management team directly at management@{business_name.lower().replace(' ', '')}.com "
                f"or call us so we can investigate this immediately and make things right."
            )
        elif tone == ReplyTone.CONCISE:
            return (
                f"We take this matter very seriously. Please contact our leadership directly at "
                f"support@{business_name.lower().replace(' ', '')}.com so we can investigate immediately."
            )
        else: # Friendly or Professional
            return (
                f"Thank you for bringing this critical issue to our attention. At {business_name}, we maintain strict "
                f"standards and are distressed to hear about your experience. Please reach out to our general manager directly "
                f"at management@{business_name.lower().replace(' ', '')}.com so we can address this urgently."
            )

    if sentiment == SentimentType.NEGATIVE:
        if tone == ReplyTone.FRIENDLY:
            return (
                f"Thanks for taking the time to share your honest thoughts with us. We're truly sorry that your visit didn't "
                f"meet the high standards we strive for regarding {category.lower()}. We'd love the opportunity to make it up to you—"
                f"please feel free to mention this on your next visit or email us so we can personally welcome you back!"
            )
        elif tone == ReplyTone.PROFESSIONAL:
            return (
                f"Thank you for providing your feedback regarding {business_name}. We sincerely apologize for falling short "
                f"of your expectations in {category.lower()}. We have shared your comments with our operations team to prevent "
                f"similar occurrences. Please contact us at support@{business_name.lower().replace(' ', '')}.com if you wish to discuss further."
            )
        elif tone == ReplyTone.EMPATHETIC:
            return (
                f"We are truly sorry to hear about your disappointing experience with us. We understand how frustrating this must have "
                f"been, especially regarding {category.lower()}. Your feedback is invaluable, and our team is already reviewing this "
                f"internally. We hope you'll allow us another chance to provide you with the exceptional experience you deserve."
            )
        else: # CONCISE
            return (
                f"We apologize for falling short during your recent visit regarding {category.lower()}. "
                f"We're addressing this with our team and hope to welcome you back for a much better experience."
            )

    elif sentiment == SentimentType.NEUTRAL:
        if tone == ReplyTone.FRIENDLY:
            return (
                f"Thanks for checking out {business_name} and sharing your feedback! We're glad you stopped by, and we appreciate "
                f"your pointers on {category.lower()}. We're always working to improve and hope to give you a 5-star experience next time!"
            )
        elif tone == ReplyTone.PROFESSIONAL:
            return (
                f"Thank you for your review of {business_name}. We appreciate your balanced feedback regarding {category.lower()} "
                f"and will use your insights as we continuously refine our service. We look forward to serving you again in the future."
            )
        elif tone == ReplyTone.EMPATHETIC:
            return (
                f"Thank you for sharing your thoughts with us. We hear your feedback regarding {category.lower()} and appreciate you "
                f"helping us see where we can do better. We're committed to making your next visit even more seamless and enjoyable."
            )
        else: # CONCISE
            return (
                f"Thank you for your feedback regarding {category.lower()}. We appreciate your support and look forward to welcoming you back to {business_name}."
            )

    else: # POSITIVE
        if tone == ReplyTone.FRIENDLY:
            return (
                f"Thank you so much for the glowing review! The entire team at {business_name} is thrilled to hear how much you "
                f"enjoyed your experience. We can't wait to welcome you back again very soon!"
            )
        elif tone == ReplyTone.PROFESSIONAL:
            return (
                f"Thank you for taking the time to share your positive experience at {business_name}. We are pleased that our commitment to "
                f"quality and {category.lower()} resonated with you. We look forward to welcoming you back soon."
            )
        elif tone == ReplyTone.EMPATHETIC:
            return (
                f"Your kind words truly made our day! It means the world to our team at {business_name} to know you had such a wonderful visit. "
                f"Thank you for supporting us, and we are looking forward to greeting you again soon!"
            )
        else: # CONCISE
            return (
                f"Thank you for the wonderful review and your support of {business_name}! We look forward to seeing you again soon."
            )

async def analyze_single_review(
    review_text: str,
    tone: ReplyTone,
    business_name: str,
    business_type: str
) -> tuple[Dict[str, Any], str]:
    """
    Analyzes a single review.
    Tries Claude API if configured, otherwise falls back gracefully.
    Returns (analysis_dict, provider_name).
    """
    api_key = get_effective_api_key()
    model = get_effective_model()

    if api_key and api_key.strip() and not api_key.startswith("your_anthropic_api_key"):
        try:
            result = await analyze_with_claude(
                review_text=review_text,
                tone=tone,
                business_name=business_name,
                business_type=business_type,
                api_key=api_key.strip(),
                model=model
            )
            return result, "Anthropic Claude"
        except Exception as exc:
            logger.warning(f"Claude API analysis failed, falling back to local engine: {exc}")
            fallback = analyze_review_fallback(review_text, tone, business_name, business_type)
            return fallback, "Simulation Engine (Claude API fallback)"
    else:
        fallback = analyze_review_fallback(review_text, tone, business_name, business_type)
        return fallback, "ReviewPilot AI Engine"
