import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

def get_default_db_path() -> str:
    """Uses /tmp in serverless environments like Vercel/AWS Lambda where root is read-only."""
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return "/tmp/reviewpilot.db"
    return "reviewpilot.db"

class Settings(BaseSettings):
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022", alias="ANTHROPIC_MODEL")
    telegram_bot_token: Optional[str] = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(default=None, alias="TELEGRAM_CHAT_ID")
    telegram_alerts_enabled: bool = Field(default=False, alias="TELEGRAM_ALERTS_ENABLED")
    business_name: str = Field(default="Urban Bistro & Cafe", alias="BUSINESS_NAME")
    business_type: str = Field(default="Restaurant / Cafe", alias="BUSINESS_TYPE")
    business_timezone: str = Field(default="UTC", alias="BUSINESS_TIMEZONE")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    port: int = Field(default=8000, alias="PORT")
    host: str = Field(default="0.0.0.0", alias="HOST")
    database_path: str = Field(default_factory=get_default_db_path, alias="DATABASE_PATH")
    allowed_origins: str = Field(default="", alias="ALLOWED_ORIGINS")
    jwt_secret_key: str = Field(default="reviewpilot_super_secret_jwt_signing_key_2026_dev_prod", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=1440, alias="JWT_EXPIRE_MINUTES") # 24 hours

    # Review Platform Integrations
    google_client_id: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: Optional[str] = Field(default=None, alias="GOOGLE_REDIRECT_URI")
    yelp_api_key: Optional[str] = Field(default=None, alias="YELP_API_KEY")
    tripadvisor_api_key: Optional[str] = Field(default=None, alias="TRIPADVISOR_API_KEY")
    token_encryption_key: Optional[str] = Field(default=None, alias="TOKEN_ENCRYPTION_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Critical Environment Variable Startup Check
if not settings.database_path:
    raise RuntimeError("CRITICAL CONFIGURATION ERROR: 'DATABASE_PATH' environment variable must be set.")
