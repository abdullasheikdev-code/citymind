from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from engine import db as db_module
from . import auth


# Swagger accepts an existing JWT access token.
bearer_scheme = HTTPBearer(auto_error=True)


def get_db():
    """Provide a database connection for the current request."""
    conn = db_module.connect()
    try:
        yield conn
    finally:
        conn.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Validate the Bearer token and return its decoded payload."""
    token = credentials.credentials

    try:
        payload = auth.decode_access_token(token)
        return payload
    except auth.TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_permission(permission: str):
    """Restrict an endpoint to users with the required permission."""

    def checker(
        user: dict = Depends(get_current_user),
    ) -> dict:
        role = user.get("role")

        if not role or not auth.has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{role}' lacks permission "
                    f"'{permission}'"
                ),
            )

        return user

    return checker