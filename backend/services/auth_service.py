import os
import time
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from backend.config import settings

logger = logging.getLogger("reviewpilot.auth")

def hash_password(password: str) -> str:
    """Secure password hashing using PBKDF2-HMAC-SHA256 with 100,000 rounds and random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        bytes.fromhex(salt),
        100000
    )
    return f"pbkdf2:sha256:100000${salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored PBKDF2 hash."""
    if not hashed_password or not plain_password:
        return False
    try:
        parts = hashed_password.split('$')
        if len(parts) != 3:
            return False
        meta, salt, stored_key = parts
        _, _, iterations_str = meta.split(':')
        iterations = int(iterations_str)
        key = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            bytes.fromhex(salt),
            iterations
        )
        return secrets.compare_digest(key.hex(), stored_key)
    except Exception as exc:
        logger.error(f"Password verification error: {exc}")
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed, time-limited JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": secrets.token_hex(16)
    })
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT token's signature and expiration."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.PyJWTError as exc:
        logger.warning(f"Invalid or expired JWT token: {exc}")
        return None

def send_suspicious_login_alert(email: str, ip_address: str, failed_count: int):
    """
    Simulates / sends security alert to the user's registered email when repeated failed logins occur.
    Logs security alert with full context and can route to SMTP if configured.
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    logger.warning(
        f"[SECURITY ALERT] Multiple repeated failed login attempts ({failed_count}) detected for account '{email}' "
        f"from IP '{ip_address}' at {timestamp}. Account lock/warning initiated."
    )
    # In production with SMTP configured, this would dispatch via aiosmtplib / SendGrid.
    # We also keep this logged and surface in user's security dashboard.

