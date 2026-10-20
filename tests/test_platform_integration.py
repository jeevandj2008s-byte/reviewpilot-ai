import asyncio
from datetime import datetime, timezone, timedelta
import uuid

from backend.database import (
    init_db,
    save_platform_connection,
    get_platform_connection_by_id,
    get_platform_connections,
    update_platform_connection_location,
    delete_platform_connection,
    save_platform_locations,
    get_platform_locations,
    save_oauth_state,
    verify_and_consume_oauth_state,
    get_existing_platform_review_ids,
    save_reviews_batch,
    get_reviews,
    get_stats
)
from backend.services.crypto_service import encrypt_token, decrypt_token, mask_token
from backend.services.platform_service import (
    calculate_date_boundaries,
    parse_iso_datetime,
    generate_google_auth_url,
    sync_platform_reviews
)
from backend.models import ReviewAnalysis, SentimentType, ReplyTone, SyncReviewsRequest

def test_token_encryption():
    raw_token = "ya29.a0AfH6SMA_mock_google_access_token_super_secret_xyz"
    encrypted = encrypt_token(raw_token)
    assert encrypted != raw_token
    assert len(encrypted) > 20

    decrypted = decrypt_token(encrypted)
    assert decrypted == raw_token

    masked = mask_token(raw_token)
    assert masked.startswith("ya29")
    assert masked.endswith("_xyz")
    assert "secret" not in masked

def test_date_boundary_calculations():
    # 2 days
    s2, e2 = calculate_date_boundaries("2d")
    diff_days_2 = (e2 - s2).total_seconds() / 86400
    assert 1.99 <= diff_days_2 <= 2.01

    # 7 days
    s7, e7 = calculate_date_boundaries("7d")
    diff_days_7 = (e7 - s7).total_seconds() / 86400
    assert 6.99 <= diff_days_7 <= 7.01

    # 14 days
    s14, e14 = calculate_date_boundaries("14d")
    diff_days_14 = (e14 - s14).total_seconds() / 86400
    assert 13.99 <= diff_days_14 <= 14.01

    # 30 days
    s30, e30 = calculate_date_boundaries("30d")
    diff_days_30 = (e30 - s30).total_seconds() / 86400
    assert 29.99 <= diff_days_30 <= 30.01

    # Custom
    s_custom, e_custom = calculate_date_boundaries("custom", "2026-10-01", "2026-10-05")
    assert s_custom.year == 2026 and s_custom.month == 10 and s_custom.day == 1
    assert e_custom.year == 2026 and e_custom.month == 10 and e_custom.day == 5

def test_oauth_csrf_state_handling():
    test_state = "csrf_token_" + str(uuid.uuid4())
    save_oauth_state(test_state, "google")

    # First verification should succeed
    assert verify_and_consume_oauth_state(test_state, "google") is True

    # Replay verification must fail (one-time use)
    assert verify_and_consume_oauth_state(test_state, "google") is False

def test_platform_connection_lifecycle():
    init_db()
    conn_id = "test_google_conn_" + str(uuid.uuid4())
    saved = save_platform_connection(
        conn_id=conn_id,
        platform="google",
        user_id=None,
        account_id="accounts/123456",
        account_name="Alex Bistro Google Account",
        location_id=None,
        location_name=None,
        encrypted_access_token=encrypt_token("access_123"),
        encrypted_refresh_token=encrypt_token("refresh_456"),
        token_expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    )
    assert saved is not None
    assert saved["id"] == conn_id

    # Test Location listing and selection
    locations = [
        {"platform_location_id": "locations/loc_101", "location_name": "Downtown Bistro", "address": "123 Main St", "is_selected": True},
        {"platform_location_id": "locations/loc_102", "location_name": "Uptown Cafe", "address": "456 High St", "is_selected": False}
    ]
    save_platform_locations(conn_id, locations)

    fetched_locs = get_platform_locations(conn_id)
    assert len(fetched_locs) == 2

    # Update active location
    update_platform_connection_location(conn_id, "locations/loc_102", "Uptown Cafe")
    conn_updated = get_platform_connection_by_id(conn_id)
    assert conn_updated["location_id"] == "locations/loc_102"
    assert conn_updated["location_name"] == "Uptown Cafe"

    # Cleanup
    assert delete_platform_connection(conn_id) is True

async def test_review_deduplication_and_ai_pipeline():
    init_db()
    test_platform = "google"
    unique_review_id_1 = "g_rev_" + str(uuid.uuid4())
    unique_review_id_2 = "g_rev_" + str(uuid.uuid4())

    # Check deduplication set before
    existing_before = get_existing_platform_review_ids(test_platform)
    assert unique_review_id_1 not in existing_before

    # Simulate importing review 1
    rev1 = ReviewAnalysis(
        id=str(uuid.uuid4()),
        review_text="The coffee was warm and delicious, highly recommend!",
        sentiment=SentimentType.POSITIVE,
        sentiment_score=0.96,
        category="Coffee & Beverages",
        is_urgent=False,
        tone=ReplyTone.FRIENDLY,
        generated_reply="Thank you so much! We are thrilled you enjoyed the coffee.",
        telegram_sent=False,
        created_at=datetime.now(timezone.utc).isoformat(),
        platform=test_platform,
        platform_review_id=unique_review_id_1,
        platform_location_id="locations/main",
        author_name="Alice Smith",
        star_rating=5.0,
        published_at="2026-10-18T10:00:00Z"
    )
    save_reviews_batch([rev1])

    # Check deduplication set after
    existing_after = get_existing_platform_review_ids(test_platform)
    assert unique_review_id_1 in existing_after
    assert unique_review_id_2 not in existing_after

    # Verify review can be queried with platform metadata
    loaded = get_reviews(limit=10, search="Alice Smith")
    assert len(loaded) > 0
    assert loaded[0].platform == "google"
    assert loaded[0].platform_review_id == unique_review_id_1
    assert loaded[0].star_rating == 5.0
