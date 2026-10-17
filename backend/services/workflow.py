import asyncio
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from backend.config import settings
from backend.database import init_db, save_reviews_batch, get_setting, update_review_telegram_status
from backend.models import ReviewAnalysis, ReplyTone, SentimentType, AnalyzeBatchResponse
from backend.services.ai_service import analyze_single_review
from backend.services.telegram_service import send_telegram_alert

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("reviewpilot.workflow")

# Concurrency semaphore for parallel review analysis
MAX_CONCURRENT_REQUESTS = 5

async def process_review_worker(
    review_text: str,
    tone: ReplyTone,
    business_name: str,
    business_type: str,
    batch_id: str,
    notify_telegram: bool,
    semaphore: asyncio.Semaphore
) -> Tuple[ReviewAnalysis, str]:
    """Analyzes a review respecting concurrency limits and handles Telegram alerting."""
    async with semaphore:
        analysis_dict, provider = await analyze_single_review(
            review_text=review_text,
            tone=tone,
            business_name=business_name,
            business_type=business_type
        )

        review_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat() + "Z"
        is_urgent = bool(analysis_dict.get("is_urgent", False))
        urgent_reason = analysis_dict.get("urgent_reason")
        sentiment_val = analysis_dict.get("sentiment", "Neutral")
        category_val = analysis_dict.get("category", "General Experience")
        reply_val = analysis_dict.get("reply", "")
        score_val = float(analysis_dict.get("sentiment_score", 0.85))

        telegram_sent = False
        if is_urgent and notify_telegram:
            success, msg = await send_telegram_alert(
                review_text=review_text,
                category=category_val,
                urgent_reason=urgent_reason,
                suggested_reply=reply_val,
                business_name=business_name
            )
            telegram_sent = success
            if success:
                logger.info(f"Telegram notification sent for urgent review {review_id}")
            else:
                logger.warning(f"Telegram notification skipped/failed: {msg}")

        item = ReviewAnalysis(
            id=review_id,
            batch_id=batch_id,
            review_text=review_text,
            sentiment=SentimentType(sentiment_val),
            sentiment_score=score_val,
            category=category_val,
            is_urgent=is_urgent,
            urgent_reason=urgent_reason,
            tone=tone,
            generated_reply=reply_val,
            telegram_sent=telegram_sent,
            created_at=created_at
        )

        return item, provider

async def orchestrate_batch_workflow(
    reviews: List[str],
    tone: ReplyTone,
    business_name: Optional[str] = None,
    business_type: Optional[str] = None,
    notify_telegram: bool = True
) -> AnalyzeBatchResponse:
    """
    Parallel review processing workflow orchestrator.
    Executes multiple reviews concurrently with concurrency throttling and aggregates results.
    """
    clean_reviews = [r.strip() for r in reviews if r and r.strip()]
    if not clean_reviews:
        raise ValueError("No valid reviews provided for batch analysis.")

    # Limit to maximum 20 reviews per batch
    clean_reviews = clean_reviews[:20]

    b_name = business_name or get_setting("business_name") or settings.business_name
    b_type = business_type or get_setting("business_type") or settings.business_type
    batch_id = str(uuid.uuid4())

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    tasks = [
        process_review_worker(
            review_text=rev,
            tone=tone,
            business_name=b_name,
            business_type=b_type,
            batch_id=batch_id,
            notify_telegram=notify_telegram,
            semaphore=semaphore
        )
        for rev in clean_reviews
    ]

    results_with_provider = await asyncio.gather(*tasks)

    results: List[ReviewAnalysis] = []
    providers = set()
    urgent_count = 0
    pos_count = 0
    neu_count = 0
    neg_count = 0

    for item, prov in results_with_provider:
        results.append(item)
        providers.add(prov)
        if item.is_urgent:
            urgent_count += 1
        if item.sentiment == SentimentType.POSITIVE:
            pos_count += 1
        elif item.sentiment == SentimentType.NEUTRAL:
            neu_count += 1
        elif item.sentiment == SentimentType.NEGATIVE:
            neg_count += 1

    # Persist the batch to SQLite
    save_reviews_batch(results)

    final_provider = "Anthropic Claude" if "Anthropic Claude" in providers else (
        list(providers)[0] if providers else "ReviewPilot Engine"
    )

    return AnalyzeBatchResponse(
        batch_id=batch_id,
        total_reviews=len(results),
        urgent_count=urgent_count,
        positive_count=pos_count,
        neutral_count=neu_count,
        negative_count=neg_count,
        results=results,
        ai_provider=final_provider
    )

async def run_worker_loop():
    """
    Background worker loop for Render Workflow service.
    Can listen on background message queues, execute scheduled maintenance, or poll batches.
    """
    init_db()
    logger.info("Render Workflow background worker started successfully. Listening for tasks...")
    while True:
        try:
            # Idle loop simulating heartbeat
            await asyncio.sleep(60)
            logger.info("Workflow worker heartbeat: healthy and operational.")
        except asyncio.CancelledError:
            logger.info("Worker loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Worker encountered error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(run_worker_loop())
    except KeyboardInterrupt:
        logger.info("Worker terminated by user.")
