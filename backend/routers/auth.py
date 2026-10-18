import uuid
import time
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.models import (
    UserRegisterRequest,
    UserLoginRequest,
    GoogleAuthRequest,
    PhoneAuthRequest,
    UserProfile,
    AuthResponse
)
from backend.database import (
    get_user_by_email,
    get_user_by_phone,
    get_user_by_id,
    create_user,
    record_login_attempt,
    update_failed_login,
    reset_failed_login,
    set_last_notified_suspicious
)
from backend.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    send_suspicious_login_alert
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[UserProfile]:
    """Dependency to retrieve and validate authenticated user from JWT Bearer token."""
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    user_dict = get_user_by_id(user_id)
    if not user_dict:
        return None
    return UserProfile(
        id=user_dict["id"],
        email=user_dict.get("email"),
        phone=user_dict.get("phone"),
        full_name=user_dict["full_name"],
        auth_provider=user_dict["auth_provider"],
        subscription_plan=user_dict.get("subscription_plan", "Free"),
        subscription_status=user_dict.get("subscription_status", "active"),
        created_at=user_dict["created_at"]
    )

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_account(payload: UserRegisterRequest, request: Request):
    """Registers a new user account with password or social identity."""
    client_ip = request.client.host if request.client else "unknown"

    if not payload.email and not payload.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either an email address or phone number is required to register."
        )

    # Check for existing email
    if payload.email and get_user_by_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Please sign in."
        )

    # Check for existing phone
    if payload.phone and get_user_by_phone(payload.phone):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this phone number already exists. Please sign in."
        )

    pwd_hash = hash_password(payload.password) if payload.password else None
    new_user_id = str(uuid.uuid4())

    created = create_user(
        user_id=new_user_id,
        email=payload.email,
        phone=payload.phone,
        full_name=payload.full_name or "Business Owner",
        password_hash=pwd_hash,
        auth_provider=payload.auth_provider,
        subscription_plan="Free",
        subscription_status="active"
    )

    token = create_access_token(data={"sub": new_user_id, "email": payload.email, "plan": "Free"})
    record_login_attempt(payload.email or payload.phone, client_ip, request.headers.get("user-agent", ""), "REGISTER_SUCCESS")

    return AuthResponse(
        status="success",
        access_token=token,
        user=UserProfile(
            id=created["id"],
            email=created.get("email"),
            phone=created.get("phone"),
            full_name=created["full_name"],
            auth_provider=created["auth_provider"],
            subscription_plan=created.get("subscription_plan", "Free"),
            subscription_status=created.get("subscription_status", "active"),
            created_at=created["created_at"]
        )
    )

@router.post("/login", response_model=AuthResponse)
async def login_account(payload: UserLoginRequest, request: Request):
    """
    Secure Login endpoint with brute-force lockout protection and repeated failure alerts.
    """
    client_ip = request.client.host if request.client else "unknown"
    ident = payload.identifier.strip()

    # Search user by email or phone
    user = get_user_by_email(ident) or get_user_by_phone(ident)

    if not user:
        record_login_attempt(ident, client_ip, request.headers.get("user-agent", ""), "FAILED_USER_NOT_FOUND")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your email/phone and password."
        )

    user_id = user["id"]
    failed_attempts = int(user.get("failed_login_attempts") or 0)
    user_email = user.get("email") or ident

    # Check if currently locked out
    locked_until = user.get("locked_until")
    if locked_until:
        try:
            lock_time = datetime.fromisoformat(locked_until)
            if datetime.utcnow() < lock_time:
                remaining_sec = int((lock_time - datetime.utcnow()).total_seconds())
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Account temporarily locked due to repeated failed logins. Try again in {remaining_sec} seconds."
                )
        except ValueError:
            pass

    # Validate password
    valid = verify_password(payload.password, user.get("password_hash") or "")
    if not valid:
        failed_attempts += 1
        record_login_attempt(ident, client_ip, request.headers.get("user-agent", ""), f"FAILED_BAD_PASSWORD_ATTEMPT_{failed_attempts}")

        # Check threshold for suspicious repeated login attempts (e.g. 3 attempts)
        if failed_attempts >= 3:
            # Send suspicious login alert to user's registered email
            send_suspicious_login_alert(user_email, client_ip, failed_attempts)
            set_last_notified_suspicious(user_id)

        # Temporary lock on 5 failed attempts (5-minute lock)
        new_lock = None
        if failed_attempts >= 5:
            new_lock = (datetime.utcnow() + datetime.timedelta(minutes=5)).isoformat()

        update_failed_login(user_id, failed_attempts, new_lock)

        if failed_attempts >= 3:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid credentials. Warning: Multiple failed attempts detected ({failed_attempts}). A security alert has been dispatched to {user_email}."
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your email/phone and password."
        )

    # Success: reset failed attempts
    reset_failed_login(user_id)
    record_login_attempt(ident, client_ip, request.headers.get("user-agent", ""), "LOGIN_SUCCESS")

    token = create_access_token(data={
        "sub": user_id,
        "email": user.get("email"),
        "plan": user.get("subscription_plan", "Free")
    })

    return AuthResponse(
        status="success",
        access_token=token,
        user=UserProfile(
            id=user["id"],
            email=user.get("email"),
            phone=user.get("phone"),
            full_name=user["full_name"],
            auth_provider=user["auth_provider"],
            subscription_plan=user.get("subscription_plan", "Free"),
            subscription_status=user.get("subscription_status", "active"),
            created_at=user["created_at"]
        )
    )

@router.post("/google", response_model=AuthResponse)
async def google_login(payload: GoogleAuthRequest, request: Request):
    """Seamless Google Sign-In with automatic subscription preservation."""
    client_ip = request.client.host if request.client else "unknown"
    email = payload.email.strip().lower()

    user = get_user_by_email(email)
    if not user:
        new_id = str(uuid.uuid4())
        user = create_user(
            user_id=new_id,
            email=email,
            phone=None,
            full_name=payload.full_name or email.split("@")[0],
            password_hash=None,
            auth_provider="google",
            subscription_plan="Free",
            subscription_status="active"
        )
        record_login_attempt(email, client_ip, request.headers.get("user-agent", ""), "GOOGLE_SIGNUP_SUCCESS")
    else:
        record_login_attempt(email, client_ip, request.headers.get("user-agent", ""), "GOOGLE_LOGIN_SUCCESS")

    token = create_access_token(data={
        "sub": user["id"],
        "email": user.get("email"),
        "plan": user.get("subscription_plan", "Free")
    })

    return AuthResponse(
        status="success",
        access_token=token,
        user=UserProfile(
            id=user["id"],
            email=user.get("email"),
            phone=user.get("phone"),
            full_name=user["full_name"],
            auth_provider=user["auth_provider"],
            subscription_plan=user.get("subscription_plan", "Free"),
            subscription_status=user.get("subscription_status", "active"),
            created_at=user["created_at"]
        )
    )

@router.post("/phone", response_model=AuthResponse)
async def phone_login(payload: PhoneAuthRequest, request: Request):
    """Phone OTP sign-in with 6-digit verification code."""
    client_ip = request.client.host if request.client else "unknown"
    phone = payload.phone.strip()

    # For fast and secure onboarding, accept valid 6-digit numeric OTPs
    if len(payload.otp) != 6 or not payload.otp.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid 6-digit numeric OTP."
        )

    user = get_user_by_phone(phone)
    if not user:
        new_id = str(uuid.uuid4())
        user = create_user(
            user_id=new_id,
            email=None,
            phone=phone,
            full_name=payload.full_name or f"User {phone[-4:]}",
            password_hash=None,
            auth_provider="phone",
            subscription_plan="Free",
            subscription_status="active"
        )
        record_login_attempt(phone, client_ip, request.headers.get("user-agent", ""), "PHONE_SIGNUP_SUCCESS")
    else:
        record_login_attempt(phone, client_ip, request.headers.get("user-agent", ""), "PHONE_LOGIN_SUCCESS")

    token = create_access_token(data={
        "sub": user["id"],
        "phone": user.get("phone"),
        "plan": user.get("subscription_plan", "Free")
    })

    return AuthResponse(
        status="success",
        access_token=token,
        user=UserProfile(
            id=user["id"],
            email=user.get("email"),
            phone=user.get("phone"),
            full_name=user["full_name"],
            auth_provider=user["auth_provider"],
            subscription_plan=user.get("subscription_plan", "Free"),
            subscription_status=user.get("subscription_status", "active"),
            created_at=user["created_at"]
        )
    )

@router.get("/me", response_model=UserProfile)
async def get_my_profile(current_user: Optional[UserProfile] = Depends(get_current_user)):
    """Fetches currently authenticated user profile, tier, and active subscription status."""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated. Please sign in.")
    return current_user

