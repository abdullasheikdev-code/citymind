"""
Auth: password hashing (PBKDF2-HMAC-SHA256, stdlib hashlib) + JWT (pyjwt).
"""

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt  # PyJWT

JWT_SECRET = os.environ.get("CITYMIND_JWT_SECRET", "dev-only-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = 60
PBKDF2_ITERATIONS = 260_000


def hash_password(password: str, salt: bytes = None) -> tuple:
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return digest.hex(), salt.hex()


def verify_password(password: str, hash_hex: str, salt_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    expected = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return hmac.compare_digest(expected.hex(), hash_hex)


def create_access_token(user_id: int, email: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id), "email": email, "role": role,
        "iat": now, "exp": now + timedelta(minutes=JWT_EXPIRY_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


class TokenError(Exception):
    pass


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise TokenError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise TokenError(f"Invalid token: {e}")
    return payload


ROLE_PERMISSIONS = {
    "viewer": {"view"},
    "planner": {"view", "simulate", "save_scenario"},
    "admin": {"view", "simulate", "save_scenario", "edit_infrastructure", "manage_users"},
}


def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())