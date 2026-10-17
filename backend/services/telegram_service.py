import logging
from typing import Optional, Tuple
import httpx
from backend.config import settings
from backend.database import get_setting

logger = logging.getLogger("reviewpilot.telegram")

def get_effective_telegram_config(
    override_token: Optional[str] = None,
    override_chat_id: Optional[str] = None
) -> Tuple[Optional[str], Optional[str], bool]:
    """Retrieve Telegram credentials from database settings or fallback to config settings."""
    db_token = get_setting("telegram_bot_token")
    db_chat_id = get_setting("telegram_chat_id")
    db_enabled = get_setting("telegram_alerts_enabled")

    bot_token = override_token or db_token or settings.telegram_bot_token
    chat_id = override_chat_id or db_chat_id or settings.telegram_chat_id

    if db_enabled is not None:
        enabled = db_enabled.lower() in ("true", "1", "yes")
    else:
        enabled = settings.telegram_alerts_enabled

    return bot_token, chat_id, enabled

async def send_telegram_alert(
    review_text: str,
    category: str,
    urgent_reason: Optional[str],
    suggested_reply: str,
    business_name: str,
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Sends an urgent alert notification via Telegram Bot API.
    Returns (success: bool, message: str).
    """
    eff_token, eff_chat_id, enabled = get_effective_telegram_config(bot_token, chat_id)

    if not eff_token or not eff_chat_id:
        return False, "Telegram Bot Token or Chat ID is not configured."

    # Format message with HTML tags
    clean_text = review_text.strip().replace("<", "&lt;").replace(">", "&gt;")
    clean_reply = suggested_reply.strip().replace("<", "&lt;").replace(">", "&gt;")
    clean_reason = (urgent_reason or "Requires immediate attention").replace("<", "&lt;").replace(">", "&gt;")

    message = (
        f"🚨 <b>URGENT CUSTOMER REVIEW ALERT</b>\n\n"
        f"🏢 <b>Business:</b> {business_name}\n"
        f"🏷️ <b>Category:</b> {category}\n"
        f"⚠️ <b>Urgency Reason:</b> {clean_reason}\n\n"
        f"💬 <b>Review:</b>\n"
        f"<i>\"{clean_text}\"</i>\n\n"
        f"✍️ <b>Suggested Response:</b>\n"
        f"{clean_reply}\n\n"
        f"⚡ <i>Action recommended: Review and connect with the customer immediately.</i>"
    )

    url = f"https://api.telegram.org/bot{eff_token}/sendMessage"
    payload = {
        "chat_id": eff_chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            data = response.json()
            if response.status_code == 200 and data.get("ok"):
                logger.info(f"Telegram alert dispatched successfully to chat {eff_chat_id}")
                return True, "Alert sent successfully to Telegram."
            else:
                desc = data.get("description", "Unknown Telegram error")
                logger.error(f"Telegram API error: {desc}")
                return False, f"Telegram API error: {desc}"
    except httpx.RequestError as exc:
        logger.error(f"Network error sending Telegram alert: {exc}")
        return False, f"Network error contacting Telegram: {str(exc)}"
    except Exception as exc:
        logger.error(f"Unexpected error in send_telegram_alert: {exc}")
        return False, f"Failed to send alert: {str(exc)}"

async def send_test_message(
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
    custom_message: Optional[str] = None
) -> Tuple[bool, str]:
    """Sends a verification test message to the configured Telegram chat."""
    eff_token, eff_chat_id, _ = get_effective_telegram_config(bot_token, chat_id)

    if not eff_token or not eff_chat_id:
        return False, "Please provide both Bot Token and Chat ID to send a test message."

    test_text = custom_message or (
        "🤖 <b>ReviewPilot Telegram Integration Test</b>\n\n"
        "✅ Your Telegram Bot integration is configured properly!\n"
        "You will receive instant alerts here whenever an urgent, health, or high-risk review is detected."
    )

    url = f"https://api.telegram.org/bot{eff_token}/sendMessage"
    payload = {
        "chat_id": eff_chat_id,
        "text": test_text,
        "parse_mode": "HTML"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            data = response.json()
            if response.status_code == 200 and data.get("ok"):
                return True, "Test message delivered successfully to your Telegram chat!"
            else:
                desc = data.get("description", f"HTTP {response.status_code}")
                return False, f"Telegram test failed: {desc}"
    except Exception as exc:
        return False, f"Connection failed: {str(exc)}"

