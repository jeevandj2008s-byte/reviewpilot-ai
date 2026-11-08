import base64
import hashlib
import logging
from typing import Optional
from cryptography.fernet import Fernet
from backend.config import settings

logger = logging.getLogger("reviewpilot.crypto")

def _get_fernet_key() -> bytes:
    seed = (settings.token_encryption_key or settings.jwt_secret_key or "reviewpilot_default_token_key_32b").encode("utf-8")
    return base64.urlsafe_b64encode(hashlib.sha256(seed).digest())

def encrypt_token(plain_token: Optional[str]) -> Optional[str]:
    """Encrypts a sensitive API token or OAuth refresh token for database persistence."""
    if not plain_token:
        return None
    try:
        fernet = Fernet(_get_fernet_key())
        return fernet.encrypt(plain_token.encode("utf-8")).decode("utf-8")
    except Exception as exc:
        raise ValueError(f"Failed to encrypt credential token: {exc}")

def decrypt_token(cipher_token: Optional[str]) -> Optional[str]:
    """Decrypts a previously encrypted token from persistent storage."""
    if not cipher_token or not cipher_token.strip():
        return None
    try:
        fernet = Fernet(_get_fernet_key())
        return fernet.decrypt(cipher_token.strip().encode("utf-8")).decode("utf-8")
    except Exception as exc:
        # If decryption fails (e.g. legacy plain text), return as-is for backward compatibility
        logger.debug(f"Token decryption fallback triggered: {exc}")
        return cipher_token.strip()

def mask_token(token: Optional[str]) -> Optional[str]:
    """Returns a masked representation of a secret token for safe UI display."""
    if not token:
        return None
    if len(token) <= 8:
        return "••••••••"
    return f"{token[:4]}••••{token[-4:]}"

