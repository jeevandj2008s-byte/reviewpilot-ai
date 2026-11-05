with open('backend/database.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = "def get_existing_platform_review_ids(platform: str, location_id: Optional[str] = None) -> Set[str]:"

new_func = """def get_reviews_by_platform_review_ids(platform: str, platform_review_ids: List[str]) -> List[ReviewAnalysis]:
    \"\"\"Retrieves all analyzed review records matching a list of platform_review_id strings.\"\"\"
    if not platform_review_ids:
        return []
    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in platform_review_ids)
    query = f"SELECT * FROM reviews WHERE platform = ? AND platform_review_id IN ({placeholders}) ORDER BY COALESCE(published_at, created_at) DESC"
    cursor.execute(query, [platform.lower()] + platform_review_ids)
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_review_analysis(r) for r in rows]

def get_existing_platform_review_ids(platform: str, location_id: Optional[str] = None) -> Set[str]:"""

if target in content and "def get_reviews_by_platform_review_ids" not in content:
    content = content.replace(target, new_func, 1)
    with open('backend/database.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added get_reviews_by_platform_review_ids to database.py")
else:
    print("Target not found or already present")
