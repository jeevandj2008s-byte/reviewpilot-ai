with open('backend/services/platform_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """    # 4. Persist newly analyzed reviews into SQLite
    if analyses:
        save_reviews_batch(analyses)

    # 5. Update connection health status and last sync timestamp
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

replacement = """    # 4. Persist newly analyzed reviews into SQLite
    if analyses:
        save_reviews_batch(analyses)

    # 5. If some were already existing and not re-analyzed, retrieve them so results has the full set!
    if not force_reanalyze and already_existing_count > 0:
        existing_raw_ids = [r["platform_review_id"] for r in raw_reviews if r["platform_review_id"] in existing_ids]
        prev_stored = get_reviews_by_platform_review_ids(platform, existing_raw_ids)
        combined_results = analyses + prev_stored
    else:
        combined_results = analyses

    # 6. Update connection health status and last sync timestamp
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
        message=f"Successfully retrieved and analyzed {len(combined_results)} reviews ({len(analyses)} newly analyzed, {already_existing_count} previous records retrieved)."
    )"""

if target in content:
    content = content.replace(target, replacement, 1)
    with open('backend/services/platform_service.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully updated return in platform_service.py")
else:
    print("Target not found")
