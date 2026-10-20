import logging
import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse

from backend.config import settings
from backend.database import (
    get_platform_connections,
    get_platform_connection_by_id,
    delete_platform_connection,
    update_platform_connection_location,
    save_platform_connection,
    save_platform_locations,
    get_platform_locations
)
from backend.models import (
    PlatformConnection,
    PlatformLocation,
    SelectLocationRequest,
    SyncReviewsRequest,
    SyncReviewsResponse,
    ConnectApiKeyRequest,
    GoogleAuthUrlResponse
)
from backend.services.platform_service import (
    generate_google_auth_url,
    exchange_google_code,
    refresh_google_locations,
    sync_platform_reviews,
    get_effective_google_credentials
)
from backend.services.crypto_service import encrypt_token

logger = logging.getLogger("reviewpilot.platforms_router")
router = APIRouter(prefix="/api/platforms", tags=["Platform Integrations"])

@router.get("/google/auth-url", response_model=GoogleAuthUrlResponse)
async def get_google_auth_url(request: Request, redirect_uri: Optional[str] = None):
    """
    Generates official Google Business Profile OAuth2 authorization URL.
    Includes state token for CSRF protection and requests offline access.
    """
    client_id, _, default_redirect = get_effective_google_credentials()
    if not client_id or client_id.startswith("your_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Client ID is not configured. Please configure GOOGLE_CLIENT_ID in your environment variables (.env)."
        )

    # Determine dynamic callback if requested from current host
    eff_redirect = redirect_uri or default_redirect
    if not redirect_uri:
        host = request.headers.get("host")
        scheme = request.url.scheme or "http"
        if host:
            eff_redirect = f"{scheme}://{host}/api/platforms/google/callback"

    try:
        url, state = generate_google_auth_url(redirect_uri=eff_redirect)
        return GoogleAuthUrlResponse(auth_url=url, state=state)
    except Exception as exc:
        logger.error(f"Failed to generate Google auth URL: {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

@router.get("/google/callback")
async def google_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None
):
    """
    Official Google OAuth2 redirect callback handler.
    Exchanges code for tokens, encrypts credentials server-side, and redirects to Settings.
    """
    if error:
        logger.warning(f"Google authorization error callback: {error} - {error_description}")
        return RedirectResponse(url=f"/#settings?error={error}")

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required OAuth 'code' or 'state' parameter in callback."
        )

    try:
        saved_conn = await exchange_google_code(code=code, state=state)
        # Redirect back to settings page with success parameter
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
          <title>Google Account Connected - ReviewPilot</title>
          <meta http-equiv="refresh" content="2; url=/#settings?connected=google" />
          <style>
            body { font-family: system-ui, sans-serif; background: #0b1528; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
            .box { background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(56, 189, 248, 0.3); padding: 2rem; border-radius: 12px; text-align: center; max-width: 420px; }
            h2 { color: #38bdf8; margin-top: 0; }
          </style>
        </head>
        <body>
          <div class="box">
            <h2>✓ Google Account Connected!</h2>
            <p>Your business profile has been connected securely. Redirecting to ReviewPilot settings...</p>
            <p style="font-size: 0.85rem; color: #94a3b8;">If you are not redirected automatically, <a href="/#settings?connected=google" style="color: #38bdf8;">click here</a>.</p>
          </div>
        </body>
        </html>
        """)
    except PermissionError as pe:
        logger.error(f"Google OAuth CSRF validation failed: {pe}")
        return RedirectResponse(url="/#settings?error=csrf_validation_failed")
    except Exception as exc:
        logger.error(f"Google OAuth callback exchange failed: {exc}", exc_info=True)
        return RedirectResponse(url="/#settings?error=connection_failed")

@router.get("/connections", response_model=List[PlatformConnection])
async def list_connections():
    """
    Returns list of connected review platforms with authorized locations and health status.
    Tokens and secrets are strictly filtered and never exposed.
    """
    rows = get_platform_connections()
    results: List[PlatformConnection] = []

    for r in rows:
        locs_raw = get_platform_locations(r["id"])
        locs = [
            PlatformLocation(
                id=l["id"],
                platform_location_id=l["platform_location_id"],
                location_name=l["location_name"],
                address=l.get("address"),
                is_selected=bool(l.get("is_selected"))
            )
            for l in locs_raw
        ]

        results.append(PlatformConnection(
            id=r["id"],
            platform=r["platform"],
            account_id=r.get("account_id"),
            account_name=r.get("account_name"),
            location_id=r.get("location_id"),
            location_name=r.get("location_name"),
            status=r.get("status", "connected"),
            last_synced_at=r.get("last_synced_at"),
            last_sync_count=int(r.get("last_sync_count") or 0),
            error_message=r.get("error_message"),
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            available_locations=locs
        ))

    return results

@router.post("/{connection_id}/locations", response_model=List[PlatformLocation])
async def refresh_locations(connection_id: str):
    """Refreshes and queries available business locations for a connected platform."""
    conn = get_platform_connection_by_id(connection_id)
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform connection not found.")

    if conn["platform"] == "google":
        try:
            locs_raw = await refresh_google_locations(connection_id)
            return [
                PlatformLocation(
                    id=l["id"],
                    platform_location_id=l["platform_location_id"],
                    location_name=l["location_name"],
                    address=l.get("address"),
                    is_selected=bool(l.get("is_selected"))
                )
                for l in locs_raw
            ]
        except Exception as exc:
            logger.error(f"Failed to refresh Google locations: {exc}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    else:
        locs_raw = get_platform_locations(connection_id)
        return [
            PlatformLocation(
                id=l["id"],
                platform_location_id=l["platform_location_id"],
                location_name=l["location_name"],
                address=l.get("address"),
                is_selected=bool(l.get("is_selected"))
            )
            for l in locs_raw
        ]

@router.put("/{connection_id}/location")
async def set_active_location(connection_id: str, payload: SelectLocationRequest):
    """Sets the active business location for review synchronization."""
    conn = get_platform_connection_by_id(connection_id)
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform connection not found.")

    update_platform_connection_location(
        conn_id=connection_id,
        location_id=payload.location_id,
        location_name=payload.location_name
    )
    return {"status": "success", "message": f"Active location updated to '{payload.location_name or payload.location_id}'."}

@router.post("/{connection_id}/sync", response_model=SyncReviewsResponse)
async def sync_reviews(connection_id: str, payload: SyncReviewsRequest):
    """
    Triggers automatic review collection for selected time period:
    - Last 2 days
    - Last 7 days
    - Last 14 days
    - Last 30 days
    - Custom date range
    Deduplicates reviews, passes new reviews through the AI workflow, and sends Telegram alerts.
    """
    conn = get_platform_connection_by_id(connection_id)
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform connection not found.")

    try:
        response = await sync_platform_reviews(
            connection_id=connection_id,
            period=payload.period,
            start_date=payload.start_date,
            end_date=payload.end_date,
            tone=payload.tone,
            notify_telegram=payload.notify_telegram
        )
        return response
    except PermissionError as pe:
        logger.error(f"Permission or token error during sync: {pe}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(pe))
    except ValueError as ve:
        logger.warning(f"Validation error during sync: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as exc:
        logger.error(f"Sync workflow failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Review sync failed: {str(exc)}"
        )

@router.post("/connect/api-key", response_model=PlatformConnection)
async def connect_api_key_platform(payload: ConnectApiKeyRequest):
    """
    Connects Yelp or TripAdvisor via official API credentials.
    Securely stores encrypted API key on server.
    """
    platform_name = payload.platform.lower().strip()
    if platform_name not in ["yelp", "tripadvisor"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only 'yelp' and 'tripadvisor' are supported for direct API connection."
        )

    conn_id = str(uuid.uuid4())
    enc_key = encrypt_token(payload.api_key) if payload.api_key else None
    loc_name = payload.business_name or f"{platform_name.capitalize()} Business ({payload.business_id})"

    saved = save_platform_connection(
        conn_id=conn_id,
        platform=platform_name,
        user_id=None,
        account_id=payload.business_id,
        account_name=loc_name,
        location_id=payload.business_id,
        location_name=loc_name,
        encrypted_access_token=enc_key,
        encrypted_refresh_token=None,
        token_expires_at=None,
        scopes="official_api_read",
        status="connected"
    )

    # Save default location
    save_platform_locations(conn_id, [{
        "id": f"loc_{conn_id[:8]}",
        "platform_location_id": payload.business_id,
        "location_name": loc_name,
        "address": f"Official {platform_name.capitalize()} Profile",
        "is_selected": True
    }])

    return PlatformConnection(
        id=saved["id"],
        platform=saved["platform"],
        account_id=saved.get("account_id"),
        account_name=saved.get("account_name"),
        location_id=saved.get("location_id"),
        location_name=saved.get("location_name"),
        status="connected",
        last_synced_at=None,
        last_sync_count=0,
        error_message=None,
        created_at=saved["created_at"],
        updated_at=saved["updated_at"],
        available_locations=[
            PlatformLocation(
                id=f"loc_{conn_id[:8]}",
                platform_location_id=payload.business_id,
                location_name=loc_name,
                address=f"Official {platform_name.capitalize()} Profile",
                is_selected=True
            )
        ]
    )

@router.delete("/{connection_id}")
async def disconnect_platform(connection_id: str):
    """Disconnects a review platform and purges stored credentials."""
    deleted = delete_platform_connection(connection_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform connection not found.")
    return {"status": "success", "message": "Platform disconnected successfully."}

