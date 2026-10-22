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
    platform: Optional[str] = "manual"
    platform_review_id: Optional[str] = None
    platform_location_id: Optional[str] = None
    author_name: Optional[str] = None
    star_rating: Optional[float] = None
    published_at: Optional[str] = None

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
    telegram_phone: Optional[str] = None
    telegram_alerts_enabled: Optional[bool] = None
    email_notifications_enabled: Optional[bool] = None
    notification_email: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    business_timezone: Optional[str] = None

class SettingsResponse(BaseModel):
    has_anthropic_key: bool
    anthropic_model: str
    telegram_alerts_enabled: bool
    telegram_bot_configured: bool
    telegram_chat_id: Optional[str] = None
    telegram_phone: Optional[str] = None
    email_notifications_enabled: bool = True
    notification_email: Optional[str] = None
    business_name: str
    business_type: str
    business_timezone: str = "UTC"
    environment: str

class TelegramTestRequest(BaseModel):
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    message: Optional[str] = None

# Authentication & Account Security Models
class UserRegisterRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    full_name: str
    auth_provider: str = "email" # 'email', 'google', 'phone'

class UserLoginRequest(BaseModel):
    identifier: str # Email or Phone number
    password: str

class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    email: str
    full_name: str
    google_id: Optional[str] = None

class PhoneAuthRequest(BaseModel):
    phone: str
    otp: str # 6-digit OTP verification
    full_name: Optional[str] = None

class UserProfile(BaseModel):
    id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    full_name: str
    auth_provider: str
    subscription_plan: str
    subscription_status: str
    created_at: str

class AuthResponse(BaseModel):
    status: str
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

# Platform Connection & Automatic Sync Models
class PlatformLocation(BaseModel):
    id: str
    platform_location_id: str
    location_name: str
    address: Optional[str] = None
    is_selected: bool = False

class PlatformConnection(BaseModel):
    id: str
    platform: str # 'google', 'yelp', 'tripadvisor'
    account_id: Optional[str] = None
    account_name: Optional[str] = None
    location_id: Optional[str] = None
    location_name: Optional[str] = None
    status: str = "connected" # 'connected', 'expired', 'error', 'disconnected'
    last_synced_at: Optional[str] = None
    last_sync_count: int = 0
    error_message: Optional[str] = None
    created_at: str
    updated_at: str
    available_locations: List[PlatformLocation] = []

class SelectLocationRequest(BaseModel):
    location_id: str
    location_name: Optional[str] = None

class SyncReviewsRequest(BaseModel):
    period: str = Field(default="7d", description="Allowed: '2d', '7d', '14d', '30d', 'custom'")
    start_date: Optional[str] = Field(default=None, description="ISO date YYYY-MM-DD for custom range")
    end_date: Optional[str] = Field(default=None, description="ISO date YYYY-MM-DD for custom range")
    tone: ReplyTone = ReplyTone.FRIENDLY
    notify_telegram: bool = True

class SyncReviewsResponse(BaseModel):
    status: str
    platform: str
    location_id: Optional[str] = None
    period: str
    start_date: str
    end_date: str
    total_fetched: int
    new_analyzed: int
    already_existing: int
    urgent_count: int
    telegram_sent_count: int
    results: List[ReviewAnalysis]
    message: str

class ConnectApiKeyRequest(BaseModel):
    platform: str = Field(..., description="'yelp' or 'tripadvisor'")
    api_key: Optional[str] = Field(default=None, description="Platform API key if custom")
    business_id: str = Field(..., description="Yelp Business ID/Alias or TripAdvisor Location ID")
    business_name: Optional[str] = None

class GoogleAuthUrlResponse(BaseModel):
    auth_url: str
    state: str


# Timeframe Analysis & Natural Language Models
class TimeframeAnalysisRequest(BaseModel):
    timeframe: str = Field(default="past two days", description="Natural language timeframe e.g. 'past two days', 'last one week', 'past one month' or custom date range")
    start_date: Optional[str] = Field(default=None, description="Optional ISO start date YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="Optional ISO end date YYYY-MM-DD")
    platform: Optional[str] = Field(default=None, description="'google', 'apple_app_store', 'google_play', or null for all")
    business_name: Optional[str] = None
    business_type: Optional[str] = None

class ActionableCorrection(BaseModel):
    area: str
    issue: str
    action_plan: str
    priority: str = "High"

class TimeframeAnalysisResponse(BaseModel):
    timeframe_query: str
    start_date: str
    end_date: str
    total_reviews: int
    positive_count: int
    neutral_count: int
    negative_count: int
    urgent_count: int
    positive_percentage: float
    neutral_percentage: float
    negative_percentage: float
    negative_feedback_points: List[str] = []
    actionable_corrections: List[str] = []
    detailed_corrections: List[ActionableCorrection] = []
    recent_reviews: List[ReviewAnalysis] = []
    executive_summary: str

# App Store & Play Store Connection Models
class ConnectAppleAppStoreRequest(BaseModel):
    issuer_id: str = Field(..., description="App Store Connect Issuer ID")
    key_id: str = Field(..., description="App Store Connect Key ID")
    private_key: str = Field(..., description="ES256 Private Key content (.p8 string)")
    app_id: str = Field(..., description="Apple App Store App ID (numeric)")
    app_name: Optional[str] = None

class ConnectGooglePlayRequest(BaseModel):
    package_name: str = Field(..., description="Android application package name e.g. com.example.app")
    service_account_json: str = Field(..., description="Google Play Developer Service Account JSON string")
    app_name: Optional[str] = None

# Voice Bot STT/TTS Models
class VoiceBotRequest(BaseModel):
    audio_base64: Optional[str] = Field(default=None, description="Base64 encoded audio string (WebM/WAV/MP3)")
    text_message: Optional[str] = Field(default=None, description="Optional text query if text-in")
    context: Optional[str] = None
    voice: Optional[str] = None

class VoiceBotResponse(BaseModel):
    user_transcript: str
    reply_text: str
    audio_base64: Optional[str] = None
    mime_type: str = "audio/mp3"
    suggestions: List[str] = []
