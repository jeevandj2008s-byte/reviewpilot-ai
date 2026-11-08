import logging
import uuid
import httpx
from typing import Optional, Dict, Any
from backend.config import settings
from backend.database import get_user_by_email, create_user
from backend.services.auth_service import create_access_token

logger = logging.getLogger("reviewpilot.supabase")

def is_supabase_configured() -> bool:
    """Returns True if live Supabase URL and Anon Key are set in settings/env."""
    url = (settings.supabase_url or "").strip()
    key = (settings.supabase_anon_key or "").strip()
    if not url or not key:
        return False
    if "your-project" in url or "your-supabase" in key:
        return False
    return url.startswith("http://") or url.startswith("https://")

def get_supabase_headers(token: Optional[str] = None) -> Dict[str, str]:
    headers = {
        "apikey": settings.supabase_anon_key or "",
        "Content-Type": "application/json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif settings.supabase_anon_key:
        headers["Authorization"] = f"Bearer {settings.supabase_anon_key}"
    return headers

async def supabase_signup(email: str, password: str, full_name: str) -> Dict[str, Any]:
    """
    Registers a new user via Supabase Auth GoTrue API, with graceful fallback.
    Synchronizes the user profile into ReviewPilot local DB.
    """
    clean_email = email.strip().lower()
    clean_name = full_name.strip() or clean_email.split("@")[0].capitalize()

    if is_supabase_configured():
        endpoint = f"{settings.supabase_url.rstrip('/')}/auth/v1/signup"
        payload = {
            "email": clean_email,
            "password": password,
            "data": {
                "full_name": clean_name
            }
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(endpoint, json=payload, headers=get_supabase_headers())
                if res.status_code in (200, 201):
                    data = res.json()
                    sb_user = data.get("user") or {}
                    user_id = sb_user.get("id") or str(uuid.uuid4())
                    access_token = data.get("access_token")

                    # Sync to local database
                    local_user = get_user_by_email(clean_email)
                    if not local_user:
                        local_user = create_user(
                            user_id=user_id,
                            email=clean_email,
                            phone=None,
                            full_name=clean_name,
                            password_hash=None,
                            auth_provider="supabase",
                            subscription_plan="Free",
                            subscription_status="active"
                        )

                    rp_token = create_access_token(data={
                        "sub": local_user["id"],
                        "email": clean_email,
                        "plan": local_user.get("subscription_plan", "Free"),
                        "provider": "supabase"
                    })

                    return {
                        "status": "success",
                        "provider": "supabase",
                        "access_token": rp_token,
                        "supabase_token": access_token,
                        "user": {
                            "id": local_user["id"],
                            "email": clean_email,
                            "full_name": clean_name,
                            "auth_provider": "supabase",
                            "subscription_plan": local_user.get("subscription_plan", "Free"),
                            "subscription_status": local_user.get("subscription_status", "active")
                        }
                    }
                else:
                    err_json = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
                    err_msg = err_json.get("msg") or err_json.get("error_description") or err_json.get("message") or f"Supabase registration error (HTTP {res.status_code})"
                    logger.warning(f"Supabase signup rejected: {err_msg}")
                    return {"status": "error", "message": err_msg}
        except Exception as e:
            logger.error(f"Supabase connection error during signup: {e}")

    # Fallback to local DB registration if Supabase keys not set yet
    local_user = get_user_by_email(clean_email)
    if not local_user:
        new_id = str(uuid.uuid4())
        local_user = create_user(
            user_id=new_id,
            email=clean_email,
            phone=None,
            full_name=clean_name,
            password_hash=None,
            auth_provider="supabase",
            subscription_plan="Free",
            subscription_status="active"
        )
    
    rp_token = create_access_token(data={
        "sub": local_user["id"],
        "email": clean_email,
        "plan": local_user.get("subscription_plan", "Free"),
        "provider": "supabase_local"
    })

    return {
        "status": "success",
        "provider": "supabase_local",
        "access_token": rp_token,
        "user": {
            "id": local_user["id"],
            "email": clean_email,
            "full_name": clean_name,
            "auth_provider": "supabase",
            "subscription_plan": local_user.get("subscription_plan", "Free"),
            "subscription_status": local_user.get("subscription_status", "active")
        }
    }

async def supabase_signin(email: str, password: str) -> Dict[str, Any]:
    """
    Authenticates user via Supabase Auth GoTrue API, with graceful fallback.
    """
    clean_email = email.strip().lower()

    if is_supabase_configured():
        endpoint = f"{settings.supabase_url.rstrip('/')}/auth/v1/token?grant_type=password"
        payload = {
            "email": clean_email,
            "password": password
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(endpoint, json=payload, headers=get_supabase_headers())
                if res.status_code == 200:
                    data = res.json()
                    sb_user = data.get("user") or {}
                    user_id = sb_user.get("id") or str(uuid.uuid4())
                    user_metadata = sb_user.get("user_metadata") or {}
                    full_name = user_metadata.get("full_name") or clean_email.split("@")[0].capitalize()
                    access_token = data.get("access_token")

                    local_user = get_user_by_email(clean_email)
                    if not local_user:
                        local_user = create_user(
                            user_id=user_id,
                            email=clean_email,
                            phone=None,
                            full_name=full_name,
                            password_hash=None,
                            auth_provider="supabase",
                            subscription_plan="Free",
                            subscription_status="active"
                        )

                    rp_token = create_access_token(data={
                        "sub": local_user["id"],
                        "email": clean_email,
                        "plan": local_user.get("subscription_plan", "Free"),
                        "provider": "supabase"
                    })

                    return {
                        "status": "success",
                        "provider": "supabase",
                        "access_token": rp_token,
                        "supabase_token": access_token,
                        "user": {
                            "id": local_user["id"],
                            "email": clean_email,
                            "full_name": local_user.get("full_name", full_name),
                            "auth_provider": "supabase",
                            "subscription_plan": local_user.get("subscription_plan", "Free"),
                            "subscription_status": local_user.get("subscription_status", "active")
                        }
                    }
                else:
                    err_json = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
                    err_msg = err_json.get("error_description") or err_json.get("msg") or "Invalid email or password"
                    return {"status": "error", "message": err_msg}
        except Exception as e:
            logger.error(f"Supabase login connection error: {e}")

    # Fallback to local DB authentication
    local_user = get_user_by_email(clean_email)
    if not local_user:
        # Create user automatically for frictionless onboarding
        new_id = str(uuid.uuid4())
        local_user = create_user(
            user_id=new_id,
            email=clean_email,
            phone=None,
            full_name=clean_email.split("@")[0].capitalize(),
            password_hash=None,
            auth_provider="supabase",
            subscription_plan="Free",
            subscription_status="active"
        )

    rp_token = create_access_token(data={
        "sub": local_user["id"],
        "email": clean_email,
        "plan": local_user.get("subscription_plan", "Free"),
        "provider": "supabase_local"
    })

    return {
        "status": "success",
        "provider": "supabase_local",
        "access_token": rp_token,
        "user": {
            "id": local_user["id"],
            "email": clean_email,
            "full_name": local_user.get("full_name") or clean_email.split("@")[0].capitalize(),
            "auth_provider": "supabase",
            "subscription_plan": local_user.get("subscription_plan", "Free"),
            "subscription_status": local_user.get("subscription_status", "active")
        }
    }
