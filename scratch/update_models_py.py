with open('backend/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = "    notify_telegram: bool = True"
replacement = "    notify_telegram: bool = True\n    force_reanalyze: bool = False"

if target in content and "force_reanalyze" not in content:
    content = content.replace(target, replacement, 1)
    with open('backend/models.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added force_reanalyze to SyncReviewsRequest in models.py")
else:
    print("Target not found or already present")
