from fastapi import APIRouter, HTTPException, status
from backend.models import SettingsPayload, SettingsResponse, TelegramTestRequest
from backend.database import get_setting, set_setting
from backend.config import settings
from backend.services.telegram_service import send_test_message, get_effective_telegram_config

router = APIRouter(prefix="/api", tags=["Settings"])

@router.get("/settings", response_model=SettingsResponse)
async def fetch_settings():
    """Retrieves current application settings with masked secrets."""
    db_key = get_setting("anthropic_api_key")
    db_token = get_setting("telegram_bot_token")
    db_chat_id = get_setting("telegram_chat_id")
    db_alerts = get_setting("telegram_alerts_enabled")
    db_b_name = get_setting("business_name")
    db_b_type = get_setting("business_type")
    db_model = get_setting("anthropic_model")

    eff_key = db_key or settings.anthropic_api_key
    eff_token = db_token or settings.telegram_bot_token
    eff_chat_id = db_chat_id or settings.telegram_chat_id
    eff_alerts = (db_alerts.lower() in ("true", "1", "yes")) if db_alerts is not None else settings.telegram_alerts_enabled

    return SettingsResponse(
        has_anthropic_key=bool(eff_key and not eff_key.startswith("your_anthropic_api_key")),
        anthropic_model=db_model or settings.anthropic_model,
        telegram_alerts_enabled=eff_alerts,
        telegram_bot_configured=bool(eff_token),
        telegram_chat_id=eff_chat_id,
        business_name=db_b_name or settings.business_name,
        business_type=db_b_type or settings.business_type,
        environment=settings.environment
    )

@router.post("/settings")
async def update_settings(payload: SettingsPayload):
    """Updates runtime settings and stores them in the persistent database."""
    if payload.anthropic_api_key is not None:
        set_setting("anthropic_api_key", payload.anthropic_api_key.strip())
    if payload.anthropic_model is not None:
        set_setting("anthropic_model", payload.anthropic_model.strip())
    if payload.telegram_bot_token is not None:
        set_setting("telegram_bot_token", payload.telegram_bot_token.strip())
    if payload.telegram_chat_id is not None:
        set_setting("telegram_chat_id", payload.telegram_chat_id.strip())
    if payload.telegram_alerts_enabled is not None:
        set_setting("telegram_alerts_enabled", "true" if payload.telegram_alerts_enabled else "false")
    if payload.business_name is not None:
        set_setting("business_name", payload.business_name.strip())
    if payload.business_type is not None:
        set_setting("business_type", payload.business_type.strip())

    return {"status": "success", "message": "Settings updated successfully."}

@router.post("/telegram/test")
async def test_telegram_connection(payload: TelegramTestRequest):
    """Verifies Telegram credentials by dispatching a test message."""
    success, message = await send_test_message(
        bot_token=payload.bot_token,
        chat_id=payload.chat_id,
        custom_message=payload.message
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {"status": "success", "message": message}
