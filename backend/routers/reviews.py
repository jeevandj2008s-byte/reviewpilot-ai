from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, status
from backend.models import (
    AnalyzeBatchRequest,
    AnalyzeBatchResponse,
    ReviewAnalysis,
    DashboardStats,
    UpdateReplyRequest,
    RegenerateReplyRequest,
    ReplyTone
)
from backend.database import (
    get_reviews,
    get_review_by_id,
    update_review_reply,
    delete_review,
    clear_all_reviews,
    get_stats,
    get_setting
)
from backend.services.workflow import orchestrate_batch_workflow
from backend.services.ai_service import analyze_single_review
from backend.config import settings
from backend.services.timeframe_service import analyze_timeframe_reviews
from backend.models import TimeframeAnalysisRequest, TimeframeAnalysisResponse

router = APIRouter(prefix="/api", tags=["Reviews"])

@router.post("/analyze", response_model=AnalyzeBatchResponse, status_code=status.HTTP_200_OK)
async def analyze_reviews_batch(payload: AnalyzeBatchRequest):
    """
    Analyzes up to 20 customer reviews in parallel.
    Classifies sentiment, tags topic category, assesses urgency, generates tailored reply,
    and dispatches Telegram alerts if urgent and configured.
    """
    cleaned_reviews = [r.strip() for r in payload.reviews if r and r.strip()]
    if not cleaned_reviews:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide at least one non-empty review."
        )

    if len(cleaned_reviews) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exceeded maximum batch limit of 20 reviews. Received {len(cleaned_reviews)} reviews."
        )

    try:
        response = await orchestrate_batch_workflow(
            reviews=cleaned_reviews,
            tone=payload.tone,
            business_name=payload.business_name,
            business_type=payload.business_type,
            notify_telegram=payload.notify_telegram
        )
        return response
    except Exception as exc:
        import uuid, logging
        correlation_id = str(uuid.uuid4())
        logging.getLogger("reviewpilot.reviews").error(f"Analysis workflow error [{correlation_id}]: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis request could not be processed. Please try again. (Correlation ID: {correlation_id})"
        )

@router.get("/reviews", response_model=List[ReviewAnalysis])
async def list_reviews(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    sentiment: Optional[str] = Query(default=None, description="Positive, Neutral, or Negative"),
    urgent_only: Optional[bool] = Query(default=None, description="Filter only urgent reviews"),
    search: Optional[str] = Query(default=None, description="Search review text or category")
):
    """Retrieves stored reviews with optional sentiment, urgency, or keyword filters."""
    return get_reviews(
        limit=limit,
        offset=offset,
        sentiment=sentiment,
        urgent_only=urgent_only,
        search=search
    )

@router.get("/reviews/{review_id}", response_model=ReviewAnalysis)
async def get_single_review(review_id: str):
    """Retrieves a single review analysis by its ID."""
    review = get_review_by_id(review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
    return review

@router.patch("/reviews/{review_id}/reply")
async def update_reply(review_id: str, payload: UpdateReplyRequest):
    """Allows user to edit and save custom changes to a generated review reply."""
    if not payload.reply_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reply text cannot be empty.")
        
    updated = update_review_reply(review_id, payload.reply_text.strip())
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
    return {"status": "success", "message": "Reply updated successfully."}

@router.post("/reviews/{review_id}/regenerate")
async def regenerate_single_reply(review_id: str, payload: RegenerateReplyRequest):
    """Regenerates an AI response for an existing review with a new tone."""
    review = get_review_by_id(review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")

    b_name = payload.business_name or get_setting("business_name") or settings.business_name
    b_type = payload.business_type or get_setting("business_type") or settings.business_type

    analysis_dict, provider = await analyze_single_review(
        review_text=review.review_text,
        tone=payload.tone,
        business_name=b_name,
        business_type=b_type
    )

    new_reply = analysis_dict.get("reply", "")
    update_review_reply(review_id, new_reply)

    return {
        "status": "success",
        "generated_reply": new_reply,
        "tone": payload.tone.value,
        "ai_provider": provider
    }

@router.delete("/reviews/{review_id}")
async def remove_review(review_id: str):
    """Deletes a single review record."""
    deleted = delete_review(review_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
    return {"status": "success", "message": "Review deleted successfully."}

@router.delete("/reviews")
async def clear_reviews():
    """Deletes all stored reviews (resets dashboard to zero state)."""
    count = clear_all_reviews()
    return {"status": "success", "message": f"Deleted {count} reviews."}

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Fetches real-time dashboard analytics, sentiment ratios, and top complaints."""
    return get_stats()
@router.post("/reviews/timeframe-analysis", response_model=TimeframeAnalysisResponse)
async def analyze_timeframe(payload: TimeframeAnalysisRequest):
    """
    Dynamic Time-Based Filtering and Analysis:
    - Accepts natural language timeframes ('past two days', 'last one week', 'past one month')
      or explicit start_date and end_date.
    - Fetches only the reviews from that specific period.
    - Computes total reviews, positive/neutral/negative sentiment ratios.
    - Returns summarized list of specific negative complaints and actionable operational corrections.
    """
    try:
        return await analyze_timeframe_reviews(payload)
    except Exception as exc:
        import logging
        logging.getLogger("reviewpilot.reviews").error(f"Timeframe analysis failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Timeframe analysis failed: {str(exc)}"
        )

@router.get("/reviews/timeframe-analysis", response_model=TimeframeAnalysisResponse)
async def get_timeframe_analysis(
    timeframe: str = Query(default="past two days", description="Natural language timeframe e.g. 'past two days', 'last one week', 'past one month'"),
    platform: Optional[str] = Query(default=None, description="Optional platform filter"),
    start_date: Optional[str] = Query(default=None, description="Optional YYYY-MM-DD start date"),
    end_date: Optional[str] = Query(default=None, description="Optional YYYY-MM-DD end date")
):
    """GET variant for timeframe analysis with query string parameters."""
    req = TimeframeAnalysisRequest(
        timeframe=timeframe,
        platform=platform,
        start_date=start_date,
        end_date=end_date
    )
    return await analyze_timeframe_reviews(req)
