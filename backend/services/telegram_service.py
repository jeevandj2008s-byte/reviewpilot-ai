import html
import logging
from typing import Optional, Tuple
import httpx
from backend.config import settings
from backend.database import get_setting

logger = logging.getLogger("reviewpilot.telegram")

def _redact_token(text: str, token: Optional[str]) -> str:
    """Safely scrubs Telegram bot token from URL representations and error logs."""
    if not text or not token:
        return text
    return text.replace(token, "[REDACTED_BOT_TOKEN]")

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

    # Format message with safe HTML entity escaping and length bounds (Telegram 4096 char limit)
    clean_biz = html.escape(business_name or "Your Business")
    clean_cat = html.escape(category or "General")
    raw_review = (review_text.strip() if review_text else "")
    if len(raw_review) > 1500:
        raw_review = raw_review[:1497] + "..."
    clean_text = html.escape(raw_review)

    raw_reply = (suggested_reply.strip() if suggested_reply else "")
    if len(raw_reply) > 1500:
        raw_reply = raw_reply[:1497] + "..."
    clean_reply = html.escape(raw_reply)
    clean_reason = html.escape(urgent_reason or "Requires immediate attention")

    message = (
        f"🚨 <b>URGENT CUSTOMER REVIEW ALERT</b>\n\n"
        f"🏢 <b>Business:</b> {clean_biz}\n"
        f"🏷️ <b>Category:</b> {clean_cat}\n"
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
                logger.info("Telegram alert dispatched successfully to configured chat [REDACTED]")
                return True, "Alert sent successfully to Telegram."
            else:
                desc = data.get("description", "Unknown Telegram error")
                logger.error(f"Telegram API error: {desc}")
                return False, f"Telegram API error: {desc}"
    except httpx.RequestError as exc:
        sanitized_err = _redact_token(str(exc), eff_token)
        logger.error(f"Network error sending Telegram alert: {sanitized_err}")
        return False, f"Network error contacting Telegram: {sanitized_err}"
    except Exception as exc:
        sanitized_err = _redact_token(str(exc), eff_token)
        logger.error(f"Unexpected error in send_telegram_alert: {sanitized_err}")
        return False, f"Failed to send alert: {sanitized_err}"

async def send_test_message(
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
    custom_message: Optional[str] = None
) -> Tuple[bool, str]:
    """Sends a verification test message to the configured Telegram chat."""
    eff_token, eff_chat_id, _ = get_effective_telegram_config(bot_token, chat_id)

    if not eff_token or not eff_chat_id:
        return False, "Please provide both Bot Token and Chat ID to send a test message."

    clean_token = eff_token.strip()
    clean_chat_id = eff_chat_id.strip()

    if ":" not in clean_token or not clean_token.split(":", 1)[0].isdigit():
        return False, "Invalid Telegram bot token format. Tokens should follow the format: 123456789:ABCdefGHIjk..."

    test_text = custom_message or (
        "🤖 <b>ReviewPilot Telegram Integration Test</b>\n\n"
        "✅ Your Telegram Bot integration is configured properly!\n"
        "You will receive instant alerts here whenever an urgent, health, or high-risk review is detected."
    )

    url = f"https://api.telegram.org/bot{clean_token}/sendMessage"
    payload = {
        "chat_id": clean_chat_id,
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
        sanitized_err = _redact_token(str(exc), clean_token)
        return False, f"Connection failed: {sanitized_err}"

