import json
import base64
import logging
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, File, UploadFile, WebSocket, WebSocketDisconnect, HTTPException, status
from backend.database import get_stats, get_setting
from backend.models import VoiceBotRequest, VoiceBotResponse
from backend.services.voice_service import process_voice_query, synthesize_speech, transcribe_audio

logger = logging.getLogger("reviewpilot.ai_chat")
router = APIRouter(prefix="/api/ai", tags=["AI Assistant & Voice Bot"])

class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    context: Optional[str] = None
    synthesize_voice: bool = Field(default=True, description="Whether to include neural speech audio in response")

class AIChatResponse(BaseModel):
    reply: str
    suggestions: List[str] = []
    audio_base64: Optional[str] = None
    mime_type: Optional[str] = "audio/mp3"

@router.post("/chat", response_model=AIChatResponse)
async def chat_with_assistant(payload: AIChatRequest):
    """
    Intelligent built-in AI assistant for small business owners.
    Provides advice on review management, tips on handling negative reviews,
    operational improvements, and guidance on using ReviewPilot features.
    Synthesizes neural speech audio for seamless voice-out responses.
    """
    msg = payload.message.lower().strip()
    biz_name = get_setting("business_name") or payload.context or "your business"
    biz_type = get_setting("business_type") or "local business"

    # Fetch stats if available to provide personalized context
    try:
        stats = get_stats()
        total = stats.total_reviews
        pos_pct = stats.positive_percentage
        neg_pct = stats.negative_percentage
        top_complaint = stats.most_common_complaint
    except Exception:
        total = 0
        pos_pct = 0.0
        neg_pct = 0.0
        top_complaint = None

    reply = ""
    suggestions = []

    # 1. Negative review handling
    if any(k in msg for k in ["negative", "bad review", "1 star", "angry customer", "complain", "handle"]):
        reply = (
            f"Here is the gold standard formula for handling negative reviews for {biz_name}:\n\n"
            "1. **Acknowledge & Validate Quickly:** Thank them for speaking up and apologize for falling short without assigning blame.\n"
            "2. **De-escalate & Move Offline:** Provide a direct leadership contact (e.g., manager email or phone) so other customers see you take ownership.\n"
            "3. **Highlight Operational Fixes:** Mention concrete steps taken (e.g., retraining staff or inspecting equipment).\n"
            "4. **Never Fight Back:** Future customers judge you by your calmness and maturity in public responses."
        )
        suggestions = [
            "How to respond to a fake review?",
            "What if a customer threatens legal action?",
            "How to turn an angry customer into a loyal one?"
        ]

    # 2. Improving overall reviews & ratings
    elif any(k in msg for k in ["improve", "boost rating", "more reviews", "5 star", "strategy"]):
        reply = (
            f"To boost ratings and build customer trust for {biz_name}:\n\n"
            "• **Ask at the 'Peak Moment':** Ask happy customers right when delivering their bill, finishing a service, or completing a job.\n"
            "• **QR Codes at Checkout:** Place a subtle tabletop card with a QR code leading straight to your Google review link.\n"
            "• **Speed Matters:** Responding within 24 hours shows prospective patrons that your business is attentive and active.\n"
            "• **Address Root Complaints:** Check your Analytics Dashboard regularly to fix recurring friction points like wait times or billing."
        )
        suggestions = [
            "How to respond to positive reviews?",
            "Review trends on my dashboard",
            "How does ReviewPilot analyze urgency?"
        ]

    # 3. Trends & Statistics analysis
    elif any(k in msg for k in ["trend", "dashboard", "stats", "insight", "analysis", "analytics"]):
        if total > 0:
            complaint_str = f" The top operational area mentioned is **{top_complaint}**." if top_complaint else ""
            reply = (
                f"📊 **Current Review Overview for {biz_name}:**\n\n"
                f"• Total Analyzed: **{total} reviews**\n"
                f"• Positive Customer Mood: **{pos_pct}%**\n"
                f"• Negative Sentiment: **{neg_pct}%**\n"
                f"{complaint_str}\n\n"
                "Tip: Focus on resolving root causes in your most common complaint category to turn those ratings into 5 stars!"
            )
        else:
            reply = (
                f"You haven't analyzed any reviews for {biz_name} yet! "
                "Head over to the **Review Analyzer** tab, paste a few customer reviews from Google or Yelp, "
                "and I will generate an instant breakdown of your sentiment, topics, and urgent alerts."
            )
        suggestions = [
            "How to handle negative reviews?",
            "Analyze reviews now",
            "How do notifications work?"
        ]

    # 4. How ReviewPilot AI works
    elif any(k in msg for k in ["how it works", "how ai works", "claude", "api key", "free"]):
        reply = (
            "🤖 **How ReviewPilot AI Works:**\n\n"
            "ReviewPilot comes with an **intelligent built-in AI engine** designed specifically for small businesses. "
            "It evaluates emotional sentiment, detects key topic categories, flags urgent health/safety hazards, "
            "and writes polite responses tailored to your business tone.\n\n"
            "It is completely **free to use** with zero API keys or monthly subscription fees required!"
        )
        suggestions = [
            "How do Telegram alerts work?",
            "Tips for handling bad reviews",
            "How to boost my ratings"
        ]

    # 5. Telegram & Notifications guidance
    elif any(k in msg for k in ["telegram", "notification", "email", "alert", "phone"]):
        reply = (
            "🔔 **How Notifications Work:**\n\n"
            "1. **Email Alerts:** We automatically notify the email address linked to your account when an urgent review arrives.\n"
            "2. **Telegram Alerts:** Enter your Telegram phone number under **Settings & Notifications**. "
            "Whenever a critical health, safety, or severe complaint is detected, ReviewPilot flags it immediately so you can act before it hurts your reputation!"
        )
        suggestions = [
            "What triggers an urgent alert?",
            "How to respond to negative reviews?",
            "Go to Settings"
        ]

    # 6. Urgent safety alerts
    elif any(k in msg for k in ["urgent", "food poison", "hazard", "safety", "threat"]):
        reply = (
            "🚨 **Urgent Alert Triggers:**\n\n"
            "ReviewPilot automatically marks a review as **Urgent** when it detects:\n"
            "• Food poisoning, illness, or health code hazards\n"
            "• Legal threats or law enforcement mentions\n"
            "• Harassment, discrimination, or safety concerns\n"
            "• Severe pest or hygiene violations\n\n"
            "When flagged, an alert is dispatched instantly to your phone and email."
        )
        suggestions = [
            "How to handle an urgent complaint?",
            "How to boost customer trust?",
            "How do Telegram alerts work?"
        ]

    # 7. Default welcoming assistant advice
    else:
        reply = (
            f"Hello! I am your AI assistant for {biz_name}. "
            "I'm here to help you understand customer feedback, handle tough reviews with grace, "
            "and suggest operational improvements. You can also tap the microphone button anytime to speak to me!"
        )
        suggestions = [
            "How to handle negative reviews?",
            "How can I improve customer ratings?",
            "Review trends on my dashboard",
            "How does the AI work?"
        ]

    # Optional speech synthesis for voice out
    audio_b64 = None
    mime_type = "audio/mp3"
    if payload.synthesize_voice:
        try:
            audio_bytes, mime = await synthesize_speech(reply)
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            mime_type = mime
        except Exception as e:
            logger.warning(f"Speech synthesis notice in /chat: {e}")

    return AIChatResponse(
        reply=reply,
        suggestions=suggestions,
        audio_base64=audio_b64,
        mime_type=mime_type
    )

# ==========================================
# Full Voice-In / Voice-Out Endpoint
# ==========================================

@router.post("/voice", response_model=VoiceBotResponse)
async def process_voice_interaction(
    payload: Optional[VoiceBotRequest] = None,
    audio_file: Optional[UploadFile] = File(None)
):
    """
    Robust Speech-to-Text (STT) and Text-to-Speech (TTS) Voice Bot Pipeline:
    1. STT: Transcribes incoming audio streams (WebM / WAV / MP3) using Whisper API or fallback.
    2. Conversational Engine: Formulates context-aware reply based on business reviews.
    3. TTS: Synthesizes high-fidelity speech using ElevenLabs or Neural Edge-TTS.
    4. Returns user transcript, assistant response, and zero-latency base64 audio payload.
    """
    audio_bytes: Optional[bytes] = None

    if audio_file:
        audio_bytes = await audio_file.read()
    elif payload and payload.audio_base64:
        try:
            audio_bytes = base64.b64decode(payload.audio_base64)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid base64 audio payload: {e}")

    text_msg = payload.text_message if payload else None
    biz_ctx = payload.context if payload else None
    voice_pref = payload.voice if payload else None

    result = await process_voice_query(
        audio_bytes=audio_bytes,
        text_message=text_msg,
        business_context=biz_ctx,
        voice_name=voice_pref
    )

    return VoiceBotResponse(
        user_transcript=result["user_transcript"],
        reply_text=result["reply_text"],
        audio_base64=result["audio_base64"],
        mime_type=result["mime_type"],
        suggestions=result.get("suggestions", [])
    )

# ==========================================
# Real-Time Streaming Audio WebSocket
# ==========================================

@router.websocket("/voice/ws")
@router.websocket("/ws/voice")
async def voice_websocket_stream(websocket: WebSocket):
    """
    Real-time bidirectional WebSocket stream for voice bot:
    - Accepts continuous audio frames or JSON messages.
    - Streams back STT transcriptions and TTS voice-out replies in real-time.
    """
    await websocket.accept()
    logger.info("Voice WebSocket client connected successfully.")

    try:
        while True:
            message = await websocket.receive()
            
            # Binary audio stream from browser MediaRecorder
            if "bytes" in message and message["bytes"]:
                raw_bytes = message["bytes"]
                res = await process_voice_query(audio_bytes=raw_bytes)
                await websocket.send_json({
                    "type": "voice_response",
                    "user_transcript": res["user_transcript"],
                    "reply_text": res["reply_text"],
                    "audio_base64": res["audio_base64"],
                    "mime_type": res["mime_type"],
                    "suggestions": res.get("suggestions", [])
                })

            # JSON message containing base64 audio or text query
            elif "text" in message and message["text"]:
                try:
                    payload = json.loads(message["text"])
                    b64_audio = payload.get("audio_base64")
                    raw_bytes = base64.b64decode(b64_audio) if b64_audio else None
                    text_msg = payload.get("text") or payload.get("message")
                    biz_ctx = payload.get("context")

                    res = await process_voice_query(
                        audio_bytes=raw_bytes,
                        text_message=text_msg,
                        business_context=biz_ctx
                    )
                    await websocket.send_json({
                        "type": "voice_response",
                        "user_transcript": res["user_transcript"],
                        "reply_text": res["reply_text"],
                        "audio_base64": res["audio_base64"],
                        "mime_type": res["mime_type"],
                        "suggestions": res.get("suggestions", [])
                    })
                except json.JSONDecodeError:
                    res = await process_voice_query(text_message=message["text"])
                    await websocket.send_json({
                        "type": "voice_response",
                        "user_transcript": res["user_transcript"],
                        "reply_text": res["reply_text"],
                        "audio_base64": res["audio_base64"],
                        "mime_type": res["mime_type"],
                        "suggestions": res.get("suggestions", [])
                    })
    except WebSocketDisconnect:
        logger.info("Voice WebSocket client disconnected.")
    except Exception as exc:
        logger.warning(f"Voice WebSocket stream notice: {exc}")
