import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any, Set
from backend.config import settings
from backend.models import ReviewAnalysis, SentimentType, ReplyTone, DashboardStats

DB_PATH = settings.database_path

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _row_to_review_analysis(r: sqlite3.Row) -> ReviewAnalysis:
    keys = r.keys()
    return ReviewAnalysis(
        id=r["id"],
        batch_id=r["batch_id"],
        review_text=r["review_text"],
        sentiment=SentimentType(r["sentiment"]),
        sentiment_score=float(r["sentiment_score"] or 0.85),
        category=r["category"] or "General",
        is_urgent=bool(r["is_urgent"]),
        urgent_reason=r["urgent_reason"],
        tone=ReplyTone(r["tone"]) if r["tone"] in [t.value for t in ReplyTone] else ReplyTone.FRIENDLY,
        generated_reply=r["generated_reply"],
        telegram_sent=bool(r["telegram_sent"]),
        created_at=r["created_at"],
        platform=r["platform"] if "platform" in keys and r["platform"] else "manual",
        platform_review_id=r["platform_review_id"] if "platform_review_id" in keys else None,
        platform_location_id=r["platform_location_id"] if "platform_location_id" in keys else None,
        author_name=r["author_name"] if "author_name" in keys else None,
        star_rating=float(r["star_rating"]) if ("star_rating" in keys and r["star_rating"] is not None) else None,
        published_at=r["published_at"] if "published_at" in keys else None
    )

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Base reviews table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id TEXT PRIMARY KEY,
        batch_id TEXT,
        review_text TEXT NOT NULL,
        sentiment TEXT NOT NULL,
        sentiment_score REAL DEFAULT 0.85,
        category TEXT DEFAULT 'General',
        is_urgent INTEGER DEFAULT 0,
        urgent_reason TEXT,
        tone TEXT DEFAULT 'Friendly',
        generated_reply TEXT NOT NULL,
        telegram_sent INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """)

    # Safe column migration for reviews table
    cursor.execute("PRAGMA table_info(reviews)")
    existing_cols = {row["name"] for row in cursor.fetchall()}
    
    new_cols = [
        ("platform", "TEXT DEFAULT 'manual'"),
        ("platform_review_id", "TEXT"),
        ("platform_location_id", "TEXT"),
        ("author_name", "TEXT"),
        ("star_rating", "REAL"),
        ("published_at", "TEXT")
    ]
    for col_name, col_def in new_cols:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE reviews ADD COLUMN {col_name} {col_def}")

    # Unique index for deduplication across connected review platforms
    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_reviews_platform_unique 
    ON reviews (platform, platform_review_id) 
    WHERE platform_review_id IS NOT NULL AND platform != 'manual'
    """)

    # 2. Settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    # 3. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE,
        phone TEXT UNIQUE,
        full_name TEXT NOT NULL,
        password_hash TEXT,
        auth_provider TEXT DEFAULT 'email',
        is_verified INTEGER DEFAULT 1,
        subscription_plan TEXT DEFAULT 'Free',
        subscription_status TEXT DEFAULT 'active',
        subscription_expires_at TEXT,
        failed_login_attempts INTEGER DEFAULT 0,
        locked_until TEXT,
        last_notified_suspicious TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # 4. Login activity table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS login_activity (
        id TEXT PRIMARY KEY,
        identifier TEXT NOT NULL,
        ip_address TEXT,
        user_agent TEXT,
        status TEXT NOT NULL,
        attempted_at TEXT NOT NULL
    )
    """)

    # 5. Review Platform Connections table (stores encrypted tokens, accounts, locations)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS platform_connections (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        platform TEXT NOT NULL,
        account_id TEXT,
        account_name TEXT,
        location_id TEXT,
        location_name TEXT,
        encrypted_access_token TEXT,
        encrypted_refresh_token TEXT,
        token_expires_at TEXT,
        scopes TEXT,
        status TEXT DEFAULT 'connected',
        last_synced_at TEXT,
        last_sync_count INTEGER DEFAULT 0,
        error_message TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # 6. Platform Locations cache table (locations authorized under a connection)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS platform_locations (
        id TEXT PRIMARY KEY,
        connection_id TEXT NOT NULL,
        platform_location_id TEXT NOT NULL,
        location_name TEXT NOT NULL,
        address TEXT,
        is_selected INTEGER DEFAULT 0,
        FOREIGN KEY(connection_id) REFERENCES platform_connections(id) ON DELETE CASCADE
    )
    """)

    # 7. OAuth CSRF State tracking table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS oauth_states (
        state TEXT PRIMARY KEY,
        platform TEXT NOT NULL,
        user_id TEXT,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

def save_reviews_batch(analyses: List[ReviewAnalysis]):
    conn = get_connection()
    cursor = conn.cursor()
    for item in analyses:
        cursor.execute("""
        INSERT OR REPLACE INTO reviews (
            id, batch_id, review_text, sentiment, sentiment_score,
            category, is_urgent, urgent_reason, tone,
            generated_reply, telegram_sent, created_at,
            platform, platform_review_id, platform_location_id,
            author_name, star_rating, published_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.id,
            item.batch_id,
            item.review_text,
            item.sentiment.value if hasattr(item.sentiment, 'value') else str(item.sentiment),
            item.sentiment_score,
            item.category,
            1 if item.is_urgent else 0,
            item.urgent_reason,
            item.tone.value if hasattr(item.tone, 'value') else str(item.tone),
            item.generated_reply,
            1 if item.telegram_sent else 0,
            item.created_at,
            item.platform or "manual",
            item.platform_review_id,
            item.platform_location_id,
            item.author_name,
            item.star_rating,
            item.published_at
        ))
    conn.commit()
    conn.close()

def get_reviews(
    limit: int = 100,
    offset: int = 0,
    sentiment: Optional[str] = None,
    urgent_only: Optional[bool] = None,
    search: Optional[str] = None,
    platform: Optional[str] = None
) -> List[ReviewAnalysis]:
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM reviews WHERE 1=1"
    params = []
    
    if sentiment and sentiment.lower() != "all":
        query += " AND sentiment = ?"
        params.append(sentiment.capitalize())
        
    if urgent_only is True:
        query += " AND is_urgent = 1"

    if platform and platform.lower() != "all":
        query += " AND platform = ?"
        params.append(platform.lower())
        
    if search:
        query += " AND (review_text LIKE ? OR generated_reply LIKE ? OR category LIKE ? OR author_name LIKE ?)"
        like_search = f"%{search}%"
        params.extend([like_search, like_search, like_search, like_search])
        
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [_row_to_review_analysis(r) for r in rows]

def get_review_by_id(review_id: str) -> Optional[ReviewAnalysis]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
    r = cursor.fetchone()
    conn.close()
    if not r:
        return None
    return _row_to_review_analysis(r)

def get_existing_platform_review_ids(platform: str, location_id: Optional[str] = None) -> Set[str]:
    """Returns set of platform review IDs already stored to prevent duplicate processing."""
    conn = get_connection()
    cursor = conn.cursor()
    if location_id:
        cursor.execute("SELECT platform_review_id FROM reviews WHERE platform = ? AND platform_location_id = ? AND platform_review_id IS NOT NULL", (platform, location_id))
    else:
        cursor.execute("SELECT platform_review_id FROM reviews WHERE platform = ? AND platform_review_id IS NOT NULL", (platform,))
    rows = cursor.fetchall()
    conn.close()
    return {r["platform_review_id"] for r in rows if r["platform_review_id"]}

def update_review_reply(review_id: str, new_reply: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reviews SET generated_reply = ? WHERE id = ?", (new_reply, review_id))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected

def update_review_telegram_status(review_id: str, sent: bool = True):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reviews SET telegram_sent = ? WHERE id = ?", (1 if sent else 0, review_id))
    conn.commit()
    conn.close()

def delete_review(review_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected

def clear_all_reviews() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reviews")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

def get_stats() -> DashboardStats:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM reviews")
    total = cursor.fetchone()["total"]
    
    if total == 0:
        conn.close()
        return DashboardStats(
            total_reviews=0,
            positive_count=0,
            neutral_count=0,
            negative_count=0,
            urgent_count=0,
            positive_percentage=0.0,
            neutral_percentage=0.0,
            negative_percentage=0.0,
            most_common_category=None,
            most_common_complaint=None,
            categories_breakdown={},
            sentiment_distribution={"Positive": 0, "Neutral": 0, "Negative": 0},
            recent_reviews=[]
        )
    
    cursor.execute("SELECT sentiment, COUNT(*) as count FROM reviews GROUP BY sentiment")
    sent_rows = cursor.fetchall()
    sent_dict = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for row in sent_rows:
        s = row["sentiment"]
        if s in sent_dict:
            sent_dict[s] = row["count"]
            
    pos_count = sent_dict["Positive"]
    neu_count = sent_dict["Neutral"]
    neg_count = sent_dict["Negative"]
    
    cursor.execute("SELECT COUNT(*) as urgent FROM reviews WHERE is_urgent = 1")
    urgent_count = cursor.fetchone()["urgent"]
    
    # Categories breakdown
    cursor.execute("SELECT category, COUNT(*) as count FROM reviews GROUP BY category ORDER BY count DESC")
    cat_rows = cursor.fetchall()
    categories_breakdown = {r["category"]: r["count"] for r in cat_rows if r["category"]}
    
    most_common_category = cat_rows[0]["category"] if cat_rows else None
    
    # Most common complaint (negative category)
    cursor.execute("SELECT category, COUNT(*) as count FROM reviews WHERE sentiment = 'Negative' GROUP BY category ORDER BY count DESC LIMIT 1")
    neg_cat_row = cursor.fetchone()
    most_common_complaint = neg_cat_row["category"] if neg_cat_row else None
    
    # Recent reviews
    cursor.execute("SELECT * FROM reviews ORDER BY created_at DESC LIMIT 6")
    recent_rows = cursor.fetchall()
    recent = [_row_to_review_analysis(r) for r in recent_rows]
        
    conn.close()
    
    return DashboardStats(
        total_reviews=total,
        positive_count=pos_count,
        neutral_count=neu_count,
        negative_count=neg_count,
        urgent_count=urgent_count,
        positive_percentage=round((pos_count / total) * 100, 1) if total else 0.0,
        neutral_percentage=round((neu_count / total) * 100, 1) if total else 0.0,
        negative_percentage=round((neg_count / total) * 100, 1) if total else 0.0,
        most_common_category=most_common_category,
        most_common_complaint=most_common_complaint,
        categories_breakdown=categories_breakdown,
        sentiment_distribution=sent_dict,
        recent_reviews=recent
    )

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key: str, value: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def clear_all_settings() -> int:
    """Removes all stored runtime settings, personal business profiles, and credentials."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM settings")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

# Platform Connection Database Queries
def save_platform_connection(
    conn_id: str,
    platform: str,
    user_id: Optional[str],
    account_id: Optional[str],
    account_name: Optional[str],
    location_id: Optional[str],
    location_name: Optional[str],
    encrypted_access_token: Optional[str],
    encrypted_refresh_token: Optional[str],
    token_expires_at: Optional[str],
    scopes: Optional[str] = None,
    status: str = "connected"
) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.utcnow().isoformat() + "Z"
    
    cursor.execute("""
    INSERT INTO platform_connections (
        id, user_id, platform, account_id, account_name,
        location_id, location_name, encrypted_access_token,
        encrypted_refresh_token, token_expires_at, scopes,
        status, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        account_id=excluded.account_id,
        account_name=excluded.account_name,
        location_id=excluded.location_id,
        location_name=excluded.location_name,
        encrypted_access_token=excluded.encrypted_access_token,
        encrypted_refresh_token=COALESCE(excluded.encrypted_refresh_token, platform_connections.encrypted_refresh_token),
        token_expires_at=excluded.token_expires_at,
        scopes=excluded.scopes,
        status=excluded.status,
        updated_at=excluded.updated_at
    """, (
        conn_id, user_id, platform, account_id, account_name,
        location_id, location_name, encrypted_access_token,
        encrypted_refresh_token, token_expires_at, scopes,
        status, now_iso, now_iso
    ))
    conn.commit()
    conn.close()
    return get_platform_connection_by_id(conn_id)

def get_platform_connection_by_id(conn_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM platform_connections WHERE id = ?", (conn_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_platform_connections(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT * FROM platform_connections WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    else:
        cursor.execute("SELECT * FROM platform_connections ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_platform_connection_by_platform(platform: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT * FROM platform_connections WHERE platform = ? AND user_id = ? ORDER BY created_at DESC LIMIT 1", (platform, user_id))
    else:
        cursor.execute("SELECT * FROM platform_connections WHERE platform = ? ORDER BY created_at DESC LIMIT 1", (platform,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_platform_connection_tokens(conn_id: str, encrypted_access_token: str, expires_at: Optional[str]):
    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.utcnow().isoformat() + "Z"
    cursor.execute("""
    UPDATE platform_connections 
    SET encrypted_access_token = ?, token_expires_at = ?, updated_at = ?
    WHERE id = ?
    """, (encrypted_access_token, expires_at, now_iso, conn_id))
    conn.commit()
    conn.close()

def update_platform_connection_location(conn_id: str, location_id: str, location_name: Optional[str]):
    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.utcnow().isoformat() + "Z"
    cursor.execute("""
    UPDATE platform_connections 
    SET location_id = ?, location_name = ?, updated_at = ?
    WHERE id = ?
    """, (location_id, location_name, now_iso, conn_id))
    # Update platform_locations table selected status
    cursor.execute("UPDATE platform_locations SET is_selected = 0 WHERE connection_id = ?", (conn_id,))
    cursor.execute("UPDATE platform_locations SET is_selected = 1 WHERE connection_id = ? AND platform_location_id = ?", (conn_id, location_id))
    conn.commit()
    conn.close()

def update_platform_connection_sync(conn_id: str, count: int, status: str = "connected", error_message: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.utcnow().isoformat() + "Z"
    cursor.execute("""
    UPDATE platform_connections 
    SET last_synced_at = ?, last_sync_count = ?, status = ?, error_message = ?, updated_at = ?
    WHERE id = ?
    """, (now_iso, count, status, error_message, now_iso, conn_id))
    conn.commit()
    conn.close()

def delete_platform_connection(conn_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM platform_locations WHERE connection_id = ?", (conn_id,))
    cursor.execute("DELETE FROM platform_connections WHERE id = ?", (conn_id,))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected

def save_platform_locations(conn_id: str, locations: List[Dict[str, Any]]):
    conn = get_connection()
    cursor = conn.cursor()
    # Clear old cached locations for this connection
    cursor.execute("DELETE FROM platform_locations WHERE connection_id = ?", (conn_id,))
    for loc in locations:
        cursor.execute("""
        INSERT INTO platform_locations (
            id, connection_id, platform_location_id, location_name, address, is_selected
        ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            loc.get("id") or str(datetime.utcnow().timestamp()) + "_" + loc["platform_location_id"],
            conn_id,
            loc["platform_location_id"],
            loc.get("location_name", "Primary Location"),
            loc.get("address"),
            1 if loc.get("is_selected") else 0
        ))
    conn.commit()
    conn.close()

def get_platform_locations(conn_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM platform_locations WHERE connection_id = ? ORDER BY location_name ASC", (conn_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# OAuth CSRF State Helpers
def save_oauth_state(state: str, platform: str, user_id: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.utcnow().isoformat() + "Z"
    cursor.execute("""
    INSERT INTO oauth_states (state, platform, user_id, created_at)
    VALUES (?, ?, ?, ?)
    """, (state, platform, user_id, now_iso))
    conn.commit()
    conn.close()

def verify_and_consume_oauth_state(state: str, platform: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT state FROM oauth_states WHERE state = ? AND platform = ?", (state, platform))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    # Consume one-time state token
    cursor.execute("DELETE FROM oauth_states WHERE state = ?", (state,))
    conn.commit()
    conn.close()
    return True

# User Account & Auth Database Queries
def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    if not email:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    if not phone:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE phone = ?", (phone.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    if not user_id:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(
    user_id: str,
    email: Optional[str],
    phone: Optional[str],
    full_name: str,
    password_hash: Optional[str],
    auth_provider: str = 'email',
    subscription_plan: str = 'Free',
    subscription_status: str = 'active'
) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.utcnow().isoformat()
    cursor.execute("""
    INSERT INTO users (
        id, email, phone, full_name, password_hash,
        auth_provider, is_verified, subscription_plan, subscription_status,
        failed_login_attempts, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, 0, ?)
    """, (
        user_id,
        email.strip().lower() if email else None,
        phone.strip() if phone else None,
        full_name.strip(),
        password_hash,
        auth_provider,
        subscription_plan,
        subscription_status,
        now_iso
    ))
    conn.commit()
    conn.close()
    return get_user_by_id(user_id)

def update_user_subscription(user_id: str, plan: str, status: str = 'active'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE users SET subscription_plan = ?, subscription_status = ? WHERE id = ?
    """, (plan, status, user_id))
    conn.commit()
    conn.close()

def record_login_attempt(identifier: str, ip_address: str, user_agent: str, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    attempt_id = str(datetime.utcnow().timestamp())
    now_iso = datetime.utcnow().isoformat()
    cursor.execute("""
    INSERT INTO login_activity (id, identifier, ip_address, user_agent, status, attempted_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (attempt_id, identifier.lower(), ip_address, user_agent, status, now_iso))
    conn.commit()
    conn.close()

def update_failed_login(user_id: str, failed_count: int, locked_until: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE users SET failed_login_attempts = ?, locked_until = ? WHERE id = ?
    """, (failed_count, locked_until, user_id))
    conn.commit()
    conn.close()

def reset_failed_login(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE id = ?
    """, (user_id,))
    conn.commit()
    conn.close()

def set_last_notified_suspicious(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.utcnow().isoformat()
    cursor.execute("UPDATE users SET last_notified_suspicious = ? WHERE id = ?", (now_iso, user_id))
    conn.commit()
    conn.close()
