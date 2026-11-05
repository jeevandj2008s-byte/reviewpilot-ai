with open('backend/routers/platforms.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        response = await sync_platform_reviews(
            connection_id=connection_id,
            period=payload.period,
            start_date=payload.start_date,
            end_date=payload.end_date,
            tone=payload.tone,
            notify_telegram=payload.notify_telegram
        )"""

replacement = """        response = await sync_platform_reviews(
            connection_id=connection_id,
            period=payload.period,
            start_date=payload.start_date,
            end_date=payload.end_date,
            tone=payload.tone,
            notify_telegram=payload.notify_telegram,
            force_reanalyze=getattr(payload, 'force_reanalyze', False)
        )"""

if target in content:
    content = content.replace(target, replacement, 1)
    with open('backend/routers/platforms.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully updated platforms.py")
else:
    print("Target not found in platforms.py")
