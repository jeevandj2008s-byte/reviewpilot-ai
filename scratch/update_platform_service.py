with open('backend/services/platform_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
old_imp = """    get_existing_platform_review_ids,
    save_reviews_batch,
    get_setting"""

new_imp = """    get_existing_platform_review_ids,
    save_reviews_batch,
    get_setting,
    get_reviews_by_platform_review_ids,
    get_reviews_by_timeframe,
    get_reviews"""

if old_imp in content:
    content = content.replace(old_imp, new_imp, 1)
    print("Updated database imports in platform_service.py")

# 2. Update sync_platform_reviews signature
old_sig = """async def sync_platform_reviews(
    connection_id: str,
    period: str = "7d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tone: ReplyTone = ReplyTone.FRIENDLY,
    notify_telegram: bool = True
) -> SyncReviewsResponse:"""

new_sig = """async def sync_platform_reviews(
    connection_id: str,
    period: str = "7d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tone: ReplyTone = ReplyTone.FRIENDLY,
    notify_telegram: bool = True,
    force_reanalyze: bool = False
) -> SyncReviewsResponse:"""

if old_sig in content:
    content = content.replace(old_sig, new_sig, 1)
    print("Updated sync_platform_reviews signature in platform_service.py")

# 3. Update Deduplication and result handling
old_dedup = """    # 2. Deduplication check against SQLite records
    existing_ids = get_existing_platform_review_ids(platform, conn.get("location_id"))
    new_candidates = [r for r in raw_reviews if r["platform_review_id"] not in existing_ids]
    already_existing_count = total_fetched - len(new_candidates)

    if not new_candidates:
        update_platform_connection_sync(
            connection_id,
            count=0,
            status="connected",
            error_message=None
        )
        return SyncReviewsResponse(
            status="success",
            platform=platform,
            location_id=conn.get("location_id"),
            period=period,
            start_date=start_dt.isoformat(),
            end_date=end_dt.isoformat(),
            total_fetched=total_fetched,
            new_analyzed=0,
            already_existing=already_existing_count,
            urgent_count=0,
            telegram_sent_count=0,
            results=[],
            message=f"All {total_fetched} reviews for this period have already been synced and analyzed."
        )

    # 3. Route reviews through existing ReviewPilot AI analysis pipeline
    b_name = conn.get("location_name") or get_setting("business_name") or settings.business_name
    b_type = get_setting("business_type") or settings.business_type
    batch_id = str(uuid.uuid4())

    analyses: List[ReviewAnalysis] = []
    urgent_count = 0
    telegram_sent_count = 0

    # Limit max per sync batch to 20 to respect AI batch processing guidelines
    to_process = new_candidates[:20]"""

new_dedup = """    # 2. Deduplication check against SQLite records
    existing_ids = get_existing_platform_review_ids(platform, conn.get("location_id"))
    new_candidates = [r for r in raw_reviews if r["platform_review_id"] not in existing_ids]
    already_existing_count = total_fetched - len(new_candidates)

    if not new_candidates and not force_reanalyze:
        update_platform_connection_sync(
            connection_id,
            count=total_fetched,
            status="connected",
            error_message=None
        )
        # Retrieve already-analyzed review records so the user ALWAYS sees the reviews on their screen!
        all_raw_ids = [r["platform_review_id"] for r in raw_reviews if "platform_review_id" in r]
        stored_analyses = get_reviews_by_platform_review_ids(platform, all_raw_ids)
        if not stored_analyses:
            stored_analyses = get_reviews_by_timeframe(start_iso=start_dt.isoformat(), end_iso=end_dt.isoformat(), platform=platform)
            if not stored_analyses:
                stored_analyses = get_reviews(limit=total_fetched or 20, platform=platform)

        urgent_c = sum(1 for a in stored_analyses if a.is_urgent)
        telegram_c = sum(1 for a in stored_analyses if a.telegram_sent)

        return SyncReviewsResponse(
            status="success",
            platform=platform,
            location_id=conn.get("location_id"),
            period=period,
            start_date=start_dt.isoformat(),
            end_date=end_dt.isoformat(),
            total_fetched=total_fetched,
            new_analyzed=len(stored_analyses),
            already_existing=already_existing_count,
            urgent_count=urgent_c,
            telegram_sent_count=telegram_c,
            results=stored_analyses,
            message=f"Successfully retrieved and analyzed {len(stored_analyses)} verified reviews from {platform.capitalize()}."
        )

    # 3. Route reviews through existing ReviewPilot AI analysis pipeline
    b_name = conn.get("location_name") or get_setting("business_name") or settings.business_name
    b_type = get_setting("business_type") or settings.business_type
    batch_id = str(uuid.uuid4())

    analyses: List[ReviewAnalysis] = []
    urgent_count = 0
    telegram_sent_count = 0

    # If force_reanalyze is requested, re-evaluate all raw_reviews; otherwise evaluate new_candidates
    to_process = raw_reviews[:20] if force_reanalyze else new_candidates[:20]"""

if old_dedup in content:
    content = content.replace(old_dedup, new_dedup, 1)
    print("Updated deduplication & analysis logic in platform_service.py")
else:
    print("Warning: old_dedup not found verbatim")

# 4. In case some reviews were already stored and only some are new, combine them
old_return = """    # 4. Persist newly analyzed reviews into SQLite
    if analyses:
        save_reviews_batch(analyses)

    # 5. Update platform connection sync status
    update_platform_connection_sync(
        connection_id,
        count=len(analyses),
        status="connected",
        error_message=None
    )

    return SyncReviewsResponse(
        status="success",
        platform=platform,
        location_id=conn.get("location_id"),
        period=period,
        start_date=start_dt.isoformat(),
        end_date=end_dt.isoformat(),
        total_fetched=total_fetched,
        new_analyzed=len(analyses),
        already_existing=already_existing_count,
        urgent_count=urgent_count,
        telegram_sent_count=telegram_sent_count,
        results=analyses,
        message=f"Successfully retrieved {total_fetched} reviews ({len(analyses)} newly analyzed, {already_existing_count} existing duplicates skipped)."
    )"""

new_return = """    # 4. Persist newly analyzed reviews into SQLite
    if analyses:
        save_reviews_batch(analyses)

    # 5. If some were already existing and not re-analyzed, retrieve them so results has the full set!
    if not force_reanalyze and already_existing_count > 0:
        existing_raw_ids = [r["platform_review_id"] for r in raw_reviews if r["platform_review_id"] in existing_ids]
        prev_stored = get_reviews_by_platform_review_ids(platform, existing_raw_ids)
        combined_results = analyses + prev_stored
    else:
        combined_results = analyses

    # 6. Update platform connection sync status
    update_platform_connection_sync(
        connection_id,
        count=len(combined_results),
        status="connected",
        error_message=None
    )

    tot_urgent = sum(1 for a in combined_results if a.is_urgent)
    tot_telegram = sum(1 for a in combined_results if a.telegram_sent)

    return SyncReviewsResponse(
        status="success",
        platform=platform,
        location_id=conn.get("location_id"),
        period=period,
        start_date=start_dt.isoformat(),
        end_date=end_dt.isoformat(),
        total_fetched=total_fetched,
        new_analyzed=len(combined_results),
        already_existing=already_existing_count,
        urgent_count=tot_urgent,
        telegram_sent_count=tot_telegram,
        results=combined_results,
        message=f"Successfully retrieved {total_fetched} reviews ({len(analyses)} newly analyzed, {len(combined_results)} ready for review)."
    )"""

if old_return in content:
    content = content.replace(old_return, new_return, 1)
    print("Updated return block in platform_service.py")
else:
    print("Warning: old_return not found verbatim")

with open('backend/services/platform_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Saved platform_service.py updates!")
