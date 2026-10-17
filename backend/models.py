from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SentimentType(str, Enum):
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"

class ReplyTone(str, Enum):
    FRIENDLY = "Friendly"
    PROFESSIONAL = "Professional"
    EMPATHETIC = "Empathetic"
    CONCISE = "Concise"

class ReviewAnalysis(BaseModel):
    id: str
    batch_id: Optional[str] = None
    review_text: str
    sentiment: SentimentType
    sentiment_score: float = Field(default=0.85, description="Confidence score 0.0 - 1.0")
    category: str = Field(default="General", description="Topic category (e.g. Food Quality, Customer Service, Cleanliness)")
    is_urgent: bool = Field(default=False, description="Flagged if high risk, safety hazard, severe escalation")
    urgent_reason: Optional[str] = None
    tone: ReplyTone = ReplyTone.FRIENDLY
    generated_reply: str
    telegram_sent: bool = False
    created_at: str

class AnalyzeBatchRequest(BaseModel):
    reviews: List[str] = Field(..., max_length=20, min_length=1, description="Up to 20 reviews, one per entry")
    tone: ReplyTone = ReplyTone.FRIENDLY
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    notify_telegram: bool = True

class AnalyzeBatchResponse(BaseModel):
    batch_id: str
    total_reviews: int
    urgent_count: int
    positive_count: int
    neutral_count: int
    negative_count: int
    results: List[ReviewAnalysis]
    ai_provider: str = "Anthropic Claude"

class UpdateReplyRequest(BaseModel):
    reply_text: str

class RegenerateReplyRequest(BaseModel):
    tone: ReplyTone
    business_name: Optional[str] = None
    business_type: Optional[str] = None

class DashboardStats(BaseModel):
    total_reviews: int
    positive_count: int
    neutral_count: int
    negative_count: int
    urgent_count: int
    positive_percentage: float
    neutral_percentage: float
    negative_percentage: float
    most_common_category: Optional[str] = None
    most_common_complaint: Optional[str] = None
    categories_breakdown: Dict[str, int] = {}
    sentiment_distribution: Dict[str, int] = {}
    recent_reviews: List[ReviewAnalysis] = []

class SettingsPayload(BaseModel):
    anthropic_api_key: Optional[str] = None
    anthropic_model: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_alerts_enabled: Optional[bool] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None

class SettingsResponse(BaseModel):
    has_anthropic_key: bool
    anthropic_model: str
    telegram_alerts_enabled: bool
    telegram_bot_configured: bool
    telegram_chat_id: Optional[str] = None
    business_name: str
    business_type: str
    environment: str

class TelegramTestRequest(BaseModel):
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    message: Optional[str] = None

