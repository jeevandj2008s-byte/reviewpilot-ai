import json
import time
import asyncio
import logging
import secrets
import uuid
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set

import httpx

from backend.config import settings
from backend.database import (
    save_platform_connection,
    get_platform_connection_by_id,
    get_platform_connections,
    get_platform_connection_by_platform,
    update_platform_connection_tokens,
    update_platform_connection_location,
    update_platform_connection_sync,
    delete_platform_connection,
    save_platform_locations,
    get_platform_locations,
    save_oauth_state,
    verify_and_consume_oauth_state,
    get_existing_platform_review_ids,
    save_reviews_batch,
    get_setting
)
from backend.models import (
    ReviewAnalysis,
    SentimentType,
    ReplyTone,
    PlatformConnection,
    PlatformLocation,
    SyncReviewsResponse
)
from backend.services.crypto_service import encrypt_token, decrypt_token
from backend.services.ai_service import analyze_single_review
from backend.services.telegram_service import send_telegram_alert

logger = logging.getLogger("reviewpilot.platforms")

GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/business.manage",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]

STAR_RATING_MAP = {
    "ONE": 1.0,
    "TWO": 2.0,
    "THREE": 3.0,
    "FOUR": 4.0,
    "FIVE": 5.0
}

def parse_iso_datetime(dt_str: str) -> datetime:
    """Parses ISO/RFC3339 timestamp into timezone-aware UTC datetime."""
    if not dt_str:
        return datetime.now(timezone.utc)
    clean_str = dt_str.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

def calculate_date_boundaries(
    period: str = "7d",
    start_date_str: Optional[str] = None,
    end_date_str: Optional[str] = None
) -> Tuple[datetime, datetime]:
    """
    Computes UTC datetime boundaries for review retrieval based on user selection:
    2d, 7d, 14d, 30d, or custom date range.
    """
    now_utc = datetime.now(timezone.utc)
    period_lower = (period or "7d").lower().strip()

    if period_lower == "2d":
        start_dt = now_utc - timedelta(days=2)
        end_dt = now_utc
    elif period_lower == "7d":
        start_dt = now_utc - timedelta(days=7)
        end_dt = now_utc
    elif period_lower == "14d":
        start_dt = now_utc - timedelta(days=14)
        end_dt = now_utc
    elif period_lower == "30d":
        start_dt = now_utc - timedelta(days=30)
        end_dt = now_utc
    elif period_lower == "custom":
        if start_date_str:
            try:
                start_dt = datetime.fromisoformat(start_date_str).replace(tzinfo=timezone.utc)
            except Exception:
                start_dt = now_utc - timedelta(days=7)
        else:
            start_dt = now_utc - timedelta(days=7)

        if end_date_str:
            try:
                # End of selected custom day
                end_dt = datetime.fromisoformat(end_date_str).replace(
                    hour=23, minute=59, second=59, tzinfo=timezone.utc
                )
            except Exception:
                end_dt = now_utc
        else:
            end_dt = now_utc
    else:
        start_dt = now_utc - timedelta(days=7)
        end_dt = now_utc

    return start_dt, end_dt

# ==========================================
# Google Business Profile OAuth2 Flow
# ==========================================

def get_effective_google_credentials() -> Tuple[Optional[str], Optional[str], str]:
    """Retrieves Google OAuth client credentials from DB runtime settings or .env."""
    client_id = get_setting("google_client_id") or settings.google_client_id
    client_secret = get_setting("google_client_secret") or settings.google_client_secret
    redirect_uri = get_setting("google_redirect_uri") or settings.google_redirect_uri or f"http://localhost:{settings.port}/api/platforms/google/callback"
    return client_id, client_secret, redirect_uri

def generate_google_auth_url(user_id: Optional[str] = None, redirect_uri: Optional[str] = None) -> Tuple[str, str]:
    """
    Generates official Google OAuth2 authorization URL with CSRF protection token.
    Requires business.manage scope to read business profile reviews and locations.
    """
    client_id, _, default_redirect = get_effective_google_credentials()
    if not client_id:
        raise ValueError("Google OAuth Client ID is not configured. Please set GOOGLE_CLIENT_ID in your environment or settings.")

    target_redirect = redirect_uri or default_redirect
    state_token = secrets.token_urlsafe(32)
    save_oauth_state(state=state_token, platform="google", user_id=user_id)

    params = {
        "client_id": client_id,
        "redirect_uri": target_redirect,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state_token,
        "include_granted_scopes": "true"
    }

    auth_url = f"{GOOGLE_AUTH_BASE}?{urllib.parse.urlencode(params)}"
    return auth_url, state_token

async def exchange_google_code(
    code: str,
    state: str,
    user_id: Optional[str] = None,
    redirect_uri: Optional[str] = None
) -> Dict[str, Any]:
    """
    Exchanges authorization code for Google access and refresh tokens.
    Stores encrypted tokens securely on server-side SQLite.
    """
    if not verify_and_consume_oauth_state(state, "google"):
        raise PermissionError("Invalid or expired OAuth CSRF state token.")

    client_id, client_secret, default_redirect = get_effective_google_credentials()
    if not client_id or not client_secret:
        raise ValueError("Google OAuth credentials are missing. Both GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are required.")

    target_redirect = redirect_uri or default_redirect

    async with httpx.AsyncClient(timeout=15.0) as client:
        token_payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": target_redirect,
            "grant_type": "authorization_code"
        }
        token_resp = await client.post(GOOGLE_TOKEN_ENDPOINT, data=token_payload)
        if token_resp.status_code != 200:
            logger.error(f"Google token exchange failed ({token_resp.status_code}): {token_resp.text}")
            raise RuntimeError(f"Google token exchange failed: {token_resp.text}")

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        scopes_granted = token_data.get("scope", "")

        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()

        # Query userinfo for display account name and email
        account_name = "Google Business Owner"
        account_id = None
        try:
            userinfo_resp = await client.get(
                GOOGLE_USERINFO_ENDPOINT,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if userinfo_resp.status_code == 200:
                ui_data = userinfo_resp.json()
                account_id = ui_data.get("id")
                account_name = ui_data.get("name") or ui_data.get("email") or account_name
        except Exception as e:
            logger.warning(f"Could not fetch Google user profile: {e}")

    # Check for existing Google connection
    existing_conn = get_platform_connection_by_platform("google", user_id)
    conn_id = existing_conn["id"] if existing_conn else str(uuid.uuid4())

    # Encrypt tokens before storing
    enc_access = encrypt_token(access_token)
    enc_refresh = encrypt_token(refresh_token) if refresh_token else (
        existing_conn.get("encrypted_refresh_token") if existing_conn else None
    )

    saved_conn = save_platform_connection(
        conn_id=conn_id,
        platform="google",
        user_id=user_id,
        account_id=account_id or "google_account",
        account_name=account_name,
        location_id=existing_conn.get("location_id") if existing_conn else None,
        location_name=existing_conn.get("location_name") if existing_conn else None,
        encrypted_access_token=enc_access,
        encrypted_refresh_token=enc_refresh,
        token_expires_at=expires_at,
        scopes=scopes_granted,
        status="connected"
    )

    # Attempt automatic location discovery in background
    try:
        await refresh_google_locations(conn_id)
    except Exception as e:
        logger.warning(f"Initial Google location discovery had warning: {e}")

    return saved_conn

async def get_valid_google_access_token(conn_dict: Dict[str, Any]) -> str:
    """
    Returns a fresh Google access token. Automatically refreshes using refresh token if expired.
    """
    token_expires_at = conn_dict.get("token_expires_at")
    enc_access = conn_dict.get("encrypted_access_token")
    enc_refresh = conn_dict.get("encrypted_refresh_token")

    is_expired = True
    if token_expires_at:
        try:
            exp_dt = parse_iso_datetime(token_expires_at)
            # If valid for at least another 4 minutes, reuse current token
            if exp_dt > datetime.now(timezone.utc) + timedelta(minutes=4):
                is_expired = False
        except Exception:
            is_expired = True

    if not is_expired and enc_access:
        decrypted = decrypt_token(enc_access)
        if decrypted:
            return decrypted

    # Token needs refresh
    if not enc_refresh:
        update_platform_connection_sync(
            conn_dict["id"], count=0, status="expired",
            error_message="Access token expired and no refresh token is stored. Please re-authorize Google."
        )
        raise PermissionError("Google session expired. Please reconnect your Google account.")

    raw_refresh = decrypt_token(enc_refresh)
    client_id, client_secret, _ = get_effective_google_credentials()
    if not client_id or not client_secret:
        raise ValueError("Google OAuth credentials missing for token refresh.")

    async with httpx.AsyncClient(timeout=15.0) as client:
        refresh_payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": raw_refresh,
            "grant_type": "refresh_token"
        }
        resp = await client.post(GOOGLE_TOKEN_ENDPOINT, data=refresh_payload)
        if resp.status_code != 200:
            err_msg = f"Failed to refresh Google token ({resp.status_code}): {resp.text}"
            logger.error(err_msg)
            update_platform_connection_sync(
                conn_dict["id"], count=0, status="expired",
                error_message="Google refresh token was revoked or expired. Please re-authenticate."
            )
            raise PermissionError("Google token refresh failed. Please reconnect your account.")

        data = resp.json()
        new_access = data.get("access_token")
        new_expires_in = data.get("expires_in", 3600)
        new_expires_at = (datetime.now(timezone.utc) + timedelta(seconds=new_expires_in)).isoformat()

        # Update in DB
        update_platform_connection_tokens(conn_dict["id"], encrypt_token(new_access), new_expires_at)
        return new_access

# ==========================================
# Google Business Profile Locations
# ==========================================

async def refresh_google_locations(conn_id: str) -> List[Dict[str, Any]]:
    """
    Fetches business locations authorized for this Google account via Google's official API.
    Uses Google My Business Account Management & Business Information APIs.
    """
    conn = get_platform_connection_by_id(conn_id)
    if not conn:
        raise ValueError(f"Platform connection '{conn_id}' not found.")

    access_token = await get_valid_google_access_token(conn)
    locations_list = []

    async with httpx.AsyncClient(timeout=20.0) as client:
        # Step 1: List Accounts
        accounts_url = "https://mybusinessaccountmanagement.googleapis.com/v1/accounts"
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        
        acc_resp = await client.get(accounts_url, headers=headers)
        if acc_resp.status_code == 200:
            accounts_data = acc_resp.json()
            accounts = accounts_data.get("accounts", [])
            for acc in accounts:
                acc_name = acc.get("name") # e.g. "accounts/1029384756"
                if not acc_name:
                    continue

                # Step 2: List locations for each account
                loc_url = f"https://mybusinessbusinessinformation.googleapis.com/v1/{acc_name}/locations?readMask=name,title,storefrontAddress"
                loc_resp = await client.get(loc_url, headers=headers)
                if loc_resp.status_code == 200:
                    for item in loc_resp.json().get("locations", []):
                        raw_name = item.get("name", "") # e.g. "locations/9876543210"
                        loc_id = raw_name.split("/")[-1] if "/" in raw_name else raw_name
                        title = item.get("title") or "Business Location"
                        addr_obj = item.get("storefrontAddress", {})
                        addr_lines = addr_obj.get("addressLines", [])
                        locality = addr_obj.get("locality", "")
                        addr_str = f"{', '.join(addr_lines)} {locality}".strip()

                        locations_list.append({
                            "id": f"loc_{loc_id}",
                            "platform_location_id": raw_name,
                            "location_name": title,
                            "address": addr_str,
                            "is_selected": False
                        })
        else:
            logger.warning(f"Could not list Google accounts ({acc_resp.status_code}): {acc_resp.text}")

    # Fallback default location if the account is authorized but has 0 verified locations returned
    if not locations_list:
        default_name = conn.get("account_name") or get_setting("business_name") or "Primary Google Location"
        locations_list.append({
            "id": f"loc_{conn_id[:8]}",
            "platform_location_id": "primary_location",
            "location_name": default_name,
            "address": "Authorized Business Profile",
            "is_selected": True
        })

    # Mark active location if already selected
    active_loc_id = conn.get("location_id")
    if active_loc_id:
        for loc in locations_list:
            if loc["platform_location_id"] == active_loc_id:
                loc["is_selected"] = True
                break
    else:
        # Default first location as selected
        locations_list[0]["is_selected"] = True
        update_platform_connection_location(
            conn_id=conn_id,
            location_id=locations_list[0]["platform_location_id"],
            location_name=locations_list[0]["location_name"]
        )

    save_platform_locations(conn_id, locations_list)
    return locations_list

# ==========================================
# Google Business Profile Review Retrieval
# ==========================================

async def fetch_google_reviews_for_period(
    conn_id: str,
    start_dt: datetime,
    end_dt: datetime
) -> List[Dict[str, Any]]:
    """
    Retrieves reviews from Google Business Profile API within the specified time period.
    Handles pagination (nextPageToken) and maps official review publication timestamps.
    """
    conn = get_platform_connection_by_id(conn_id)
    if not conn:
        raise ValueError("Platform connection not found.")

    access_token = await get_valid_google_access_token(conn)
    location_id = conn.get("location_id") or "primary_location"
    account_id = conn.get("account_id") or "accounts/primary"

    # Normalize account and location resource names
    if not account_id.startswith("accounts/"):
        account_id = f"accounts/{account_id}"
    if not location_id.startswith("locations/"):
        location_id = f"locations/{location_id}"

    reviews_endpoint = f"https://mybusiness.googleapis.com/v4/{account_id}/{location_id}/reviews"
    collected_reviews: List[Dict[str, Any]] = []
    page_token = None
    max_pages = 5 # Safety limit to respect platform quotas

    async with httpx.AsyncClient(timeout=25.0) as client:
        for page_idx in range(max_pages):
            params: Dict[str, Any] = {"pageSize": 50}
            if page_token:
                params["pageToken"] = page_token

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }

            resp = await client.get(reviews_endpoint, params=params, headers=headers)

            # Rate limit handling (HTTP 429)
            if resp.status_code == 429:
                logger.warning("Google API rate limit hit (429). Backing off for 3 seconds...")
                await asyncio.sleep(3.0)
                resp = await client.get(reviews_endpoint, params=params, headers=headers)

            if resp.status_code == 404:
                # Location or reviews endpoint not found for this identifier
                logger.warning(f"Google reviews endpoint returned 404 for {reviews_endpoint}")
                break

            if resp.status_code != 200:
                logger.error(f"Google reviews fetch error ({resp.status_code}): {resp.text}")
                update_platform_connection_sync(conn_id, count=0, status="error", error_message=f"Google API error: {resp.status_code}")
                break

            data = resp.json()
            raw_reviews = data.get("reviews", [])
            if not raw_reviews:
                break

            stop_pagination = False
            for r in raw_reviews:
                rev_id = r.get("reviewId") or r.get("name")
                create_time_str = r.get("createTime") or r.get("updateTime")
                pub_dt = parse_iso_datetime(create_time_str)

                # If review is earlier than our start cutoff, we can stop paginating further
                # because reviews are ordered by createTime desc
                if pub_dt < start_dt:
                    stop_pagination = True
                    break

                # If review falls within [start_dt, end_dt]
                if start_dt <= pub_dt <= end_dt:
                    comment = r.get("comment", "").strip()
                    reviewer = r.get("reviewer", {})
                    author = reviewer.get("displayName", "Google Reviewer")
                    star_enum = r.get("starRating", "FIVE")
                    rating = STAR_RATING_MAP.get(str(star_enum).upper(), 5.0)

                    if comment:
                        collected_reviews.append({
                            "platform_review_id": str(rev_id),
                            "review_text": comment,
                            "author_name": author,
                            "star_rating": rating,
                            "published_at": pub_dt.isoformat()
                        })

            if stop_pagination:
                break

            page_token = data.get("nextPageToken")
            if not page_token:
                break

    return collected_reviews

# ==========================================
# Yelp Fusion & TripAdvisor API Connectors
# ==========================================

async def fetch_yelp_reviews_for_period(
    business_id: str,
    api_key: Optional[str],
    start_dt: datetime,
    end_dt: datetime
) -> List[Dict[str, Any]]:
    """Fetches reviews from official Yelp Fusion API."""
    effective_key = api_key or get_setting("yelp_api_key") or settings.yelp_api_key
    if not effective_key:
        raise ValueError("Yelp Fusion API Key is not configured.")

    url = f"https://api.yelp.com/v3/businesses/{business_id}/reviews?limit=50&sort_by=newest"
    headers = {"Authorization": f"Bearer {effective_key}", "Accept": "application/json"}

    collected: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(f"Yelp API returned status {resp.status_code}: {resp.text}")

        data = resp.json()
        for r in data.get("reviews", []):
            time_created = r.get("time_created") # e.g. "2026-10-18 10:30:00"
            pub_dt = parse_iso_datetime(time_created)
            if start_dt <= pub_dt <= end_dt:
                text = r.get("text", "").strip()
                if text:
                    collected.append({
                        "platform_review_id": str(r.get("id")),
                        "review_text": text,
                        "author_name": r.get("user", {}).get("name", "Yelp Reviewer"),
                        "star_rating": float(r.get("rating", 5.0)),
                        "published_at": pub_dt.isoformat()
                    })

    return collected

async def fetch_tripadvisor_reviews_for_period(
    location_id: str,
    api_key: Optional[str],
    start_dt: datetime,
    end_dt: datetime
) -> List[Dict[str, Any]]:
    """Fetches reviews from official TripAdvisor Content API."""
    effective_key = api_key or get_setting("tripadvisor_api_key") or settings.tripadvisor_api_key
    if not effective_key:
        raise ValueError("TripAdvisor Content API Key is not configured.")

    url = f"https://api.content.tripadvisor.com/api/v1/location/{location_id}/reviews?language=en"
    headers = {"Accept": "application/json", "X-TripAdvisor-API-Key": effective_key}

    collected: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(f"TripAdvisor API returned status {resp.status_code}: {resp.text}")

        data = resp.json()
        for r in data.get("data", []):
            pub_date_str = r.get("published_date")
            pub_dt = parse_iso_datetime(pub_date_str)
            if start_dt <= pub_dt <= end_dt:
                text = r.get("text", "").strip()
                if text:
                    collected.append({
                        "platform_review_id": str(r.get("id")),
                        "review_text": text,
                        "author_name": r.get("user", {}).get("username", "TripAdvisor Member"),
                        "star_rating": float(r.get("rating", 5.0)),
                        "published_at": pub_dt.isoformat()
                    })

    return collected



# ==========================================
# Apple App Store Connect API
# ==========================================

def generate_apple_jwt(issuer_id: str, key_id: str, private_key: str) -> str:
    """Generates official ES256 signed JWT for App Store Connect API."""
    import jwt
    clean_pk = private_key.strip()
    if "-----BEGIN PRIVATE KEY-----" not in clean_pk:
        clean_pk = f"-----BEGIN PRIVATE KEY-----\n{clean_pk}\n-----END PRIVATE KEY-----"

    payload = {
        "iss": issuer_id,
        "exp": int(time.time()) + 1200,  # 20 minutes maximum
        "aud": "appstoreconnect-v1"
    }
    headers = {
        "alg": "ES256",
        "kid": key_id,
        "typ": "JWT"
    }
    return jwt.encode(payload, clean_pk, algorithm="ES256", headers=headers)

async def fetch_apple_app_store_reviews(
    app_id: str,
    issuer_id: str,
    key_id: str,
    private_key: str,
    start_dt: datetime,
    end_dt: datetime
) -> List[Dict[str, Any]]:
    """
    Fetches customer reviews from Apple App Store Connect API:
    Endpoint: https://api.appstoreconnect.apple.com/v1/apps/{appId}/customerReviews
    """
    collected: List[Dict[str, Any]] = []
    
    try:
        jwt_token = generate_apple_jwt(issuer_id, key_id, private_key)
    except Exception as e:
        logger.error(f"Failed to generate Apple ES256 JWT: {e}")
        raise ValueError(f"Invalid Apple App Store Connect credentials: {e}")

    url = f"https://api.appstoreconnect.apple.com/v1/apps/{app_id}/customerReviews?sort=-createdDate&limit=50"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code in (401, 403):
            raise PermissionError("Apple App Store Connect authorization failed. Please verify Issuer ID, Key ID, and .p8 Private Key.")
        if resp.status_code == 404:
            raise ValueError(f"Apple App ID '{app_id}' was not found on App Store Connect.")
        if resp.status_code != 200:
            logger.error(f"Apple App Store Connect API returned {resp.status_code}: {resp.text}")
            raise RuntimeError(f"Apple App Store Connect API error: {resp.status_code}")

        data = resp.json()
        for item in data.get("data", []):
            attrs = item.get("attributes", {})
            created_str = attrs.get("createdDate")
            pub_dt = parse_iso_datetime(created_str)
            
            if start_dt <= pub_dt <= end_dt:
                title = attrs.get("title", "")
                body = attrs.get("body", "")
                full_text = f"{title}. {body}".strip() if title else body.strip()
                if full_text:
                    collected.append({
                        "platform_review_id": str(item.get("id")),
                        "review_text": full_text,
                        "author_name": attrs.get("reviewerNickname", "App Store Customer"),
                        "star_rating": float(attrs.get("rating", 5.0)),
                        "published_at": pub_dt.isoformat()
                    })

    return collected

# ==========================================
# Google Play Developer API
# ==========================================

async def get_google_play_access_token(service_account_json_str: str) -> str:
    """
    Exchanges Google Play service account JSON for an OAuth2 access token
    with 'https://www.googleapis.com/auth/androidpublisher' scope.
    """
    import jwt
    try:
        sa_data = json.loads(service_account_json_str)
    except Exception as e:
        raise ValueError(f"Invalid Google Play service account JSON: {e}")

    client_email = sa_data.get("client_email")
    private_key = sa_data.get("private_key")
    token_uri = sa_data.get("token_uri") or "https://oauth2.googleapis.com/token"

    if not client_email or not private_key:
        raise ValueError("Google Play service account JSON missing 'client_email' or 'private_key'.")

    now_ts = int(time.time())
    payload = {
        "iss": client_email,
        "scope": "https://www.googleapis.com/auth/androidpublisher",
        "aud": token_uri,
        "exp": now_ts + 3600,
        "iat": now_ts
    }

    signed_jwt = jwt.encode(payload, private_key, algorithm="RS256")

    async with httpx.AsyncClient(timeout=15.0) as client:
        token_payload = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": signed_jwt
        }
        resp = await client.post(token_uri, data=token_payload)
        if resp.status_code != 200:
            logger.error(f"Google Play OAuth exchange failed ({resp.status_code}): {resp.text}")
            raise PermissionError(f"Google Play service account authorization failed: {resp.text}")

        return resp.json().get("access_token")

async def fetch_google_play_reviews(
    package_name: str,
    service_account_json_str: str,
    start_dt: datetime,
    end_dt: datetime
) -> List[Dict[str, Any]]:
    """
    Fetches customer reviews from Google Play Developer API (Android Publisher):
    Endpoint: https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{packageName}/reviews
    """
    access_token = await get_google_play_access_token(service_account_json_str)
    url = f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{package_name}/reviews?maxResults=50"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    collected: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code in (401, 403):
            raise PermissionError("Google Play Developer API access denied. Ensure Android Publisher API is enabled.")
        if resp.status_code == 404:
            raise ValueError(f"Package '{package_name}' not found in Google Play Console.")
        if resp.status_code != 200:
            logger.error(f"Google Play reviews fetch error ({resp.status_code}): {resp.text}")
            raise RuntimeError(f"Google Play API error: {resp.status_code}")

        data = resp.json()
        for rev in data.get("reviews", []):
            rev_id = rev.get("reviewId")
            author = rev.get("authorName", "Google Play User")
            comments = rev.get("comments", [])
            for c in comments:
                user_comment = c.get("userComment", {})
                text = user_comment.get("text", "").strip()
                star = float(user_comment.get("starRating", 5.0))
                last_mod = user_comment.get("lastModified", {})
                sec = last_mod.get("seconds")
                
                if sec:
                    pub_dt = datetime.fromtimestamp(int(sec), tz=timezone.utc)
                else:
                    pub_dt = datetime.now(timezone.utc)

                if start_dt <= pub_dt <= end_dt and text:
                    collected.append({
                        "platform_review_id": str(rev_id),
                        "review_text": text,
                        "author_name": author,
                        "star_rating": star,
                        "published_at": pub_dt.isoformat()
                    })

    return collected

# ==========================================
# Unified Synchronization & AI Analysis Pipeline
# ==========================================

async def sync_platform_reviews(
    connection_id: str,
    period: str = "7d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tone: ReplyTone = ReplyTone.FRIENDLY,
    notify_telegram: bool = True
) -> SyncReviewsResponse:
    """
    Main Synchronization Workflow:
    1. Determines date boundaries according to user selection (2d, 7d, 14d, 30d, custom).
    2. Fetches customer reviews via the platform's official API.
    3. Deduplicates against existing records via stable platform review IDs.
    4. Routes newly retrieved reviews directly into ReviewPilot's AI analysis pipeline.
    5. Dispatches Telegram alerts for urgent safety risks and persists results.
    """
    conn = get_platform_connection_by_id(connection_id)
    if not conn:
        raise ValueError("Platform connection does not exist.")

    platform = conn["platform"]
    start_dt, end_dt = calculate_date_boundaries(period, start_date, end_date)

    # 1. Fetch from official platform API
    raw_reviews: List[Dict[str, Any]] = []
    if platform == "google":
        raw_reviews = await fetch_google_reviews_for_period(connection_id, start_dt, end_dt)
    elif platform == "yelp":
        b_id = conn.get("location_id") or conn.get("account_id")
        raw_reviews = await fetch_yelp_reviews_for_period(b_id, None, start_dt, end_dt)
    elif platform == "tripadvisor":
        loc_id = conn.get("location_id") or conn.get("account_id")
        raw_reviews = await fetch_tripadvisor_reviews_for_period(loc_id, None, start_dt, end_dt)
    elif platform in ("apple_app_store", "apple"):
        enc_token = conn.get("encrypted_access_token")
        if not enc_token:
            raise ValueError("Apple App Store credentials missing.")
        raw_creds = json.loads(decrypt_token(enc_token))
        app_id = conn.get("location_id") or conn.get("account_id")
        raw_reviews = await fetch_apple_app_store_reviews(
            app_id=app_id,
            issuer_id=raw_creds["issuer_id"],
            key_id=raw_creds["key_id"],
            private_key=raw_creds["private_key"],
            start_dt=start_dt,
            end_dt=end_dt
        )
    elif platform in ("google_play", "play_store"):
        enc_token = conn.get("encrypted_access_token")
        if not enc_token:
            raise ValueError("Google Play Developer credentials missing.")
        raw_creds = json.loads(decrypt_token(enc_token))
        package_name = conn.get("location_id") or conn.get("account_id")
        raw_reviews = await fetch_google_play_reviews(
            package_name=package_name,
            service_account_json_str=raw_creds["service_account_json"],
            start_dt=start_dt,
            end_dt=end_dt
        )
    else:
        raise ValueError(f"Unsupported review platform: {platform}")

    total_fetched = len(raw_reviews)

    # 2. Deduplication check against SQLite records
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
    to_process = new_candidates[:20]

    for item in to_process:
        review_text = item["review_text"]
        analysis_dict, _ = await analyze_single_review(
            review_text=review_text,
            tone=tone,
            business_name=b_name,
            business_type=b_type
        )

        review_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
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
                business_name=b_name
            )
            telegram_sent = success
            if success:
                telegram_sent_count += 1

        if is_urgent:
            urgent_count += 1

        rev_analysis = ReviewAnalysis(
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
            created_at=created_at,
            platform=platform,
            platform_review_id=item["platform_review_id"],
            platform_location_id=conn.get("location_id"),
            author_name=item.get("author_name"),
            star_rating=item.get("star_rating"),
            published_at=item.get("published_at")
        )
        analyses.append(rev_analysis)

    # 4. Save newly analyzed reviews to SQLite database
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
    )

