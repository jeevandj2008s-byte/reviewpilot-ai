import csv
import io
import json
from fastapi import APIRouter, Response
from backend.database import get_reviews

router = APIRouter(prefix="/api/export", tags=["Export"])

@router.get("/csv")
async def export_reviews_csv():
    """Generates and downloads a CSV of all analyzed reviews and drafted replies."""
    reviews = get_reviews(limit=1000)
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "Created At",
        "Sentiment",
        "Confidence Score",
        "Category",
        "Is Urgent",
        "Urgent Reason",
        "Tone",
        "Customer Review",
        "Generated Reply",
        "Telegram Alerted"
    ])

    for r in reviews:
        writer.writerow([
            r.id,
            r.created_at,
            r.sentiment.value,
            f"{r.sentiment_score:.2f}",
            r.category,
            "YES" if r.is_urgent else "NO",
            r.urgent_reason or "",
            r.tone.value,
            r.review_text,
            r.generated_reply,
            "YES" if r.telegram_sent else "NO"
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="reviewpilot_reviews.csv"'}
    )

@router.get("/json")
async def export_reviews_json():
    """Generates and downloads a JSON export of all analyzed reviews."""
    reviews = get_reviews(limit=1000)
    data = [r.model_dump() for r in reviews]
    json_str = json.dumps(data, indent=2)

    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="reviewpilot_reviews.json"'}
    )

