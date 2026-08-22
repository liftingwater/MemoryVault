"""Authentication module for Supabase JWT validation."""

from typing import Any, Dict

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

security = HTTPBearer()


class AuthError(Exception):
    """Raised when authentication fails."""

    pass


def decode_jwt(token: str) -> Dict[str, Any]:
    """Decode and verify a Supabase JWT token."""
    try:
        # Decode the JWT using the SUPABASE_JWT_SECRET
        # Supabase tokens have audience "authenticated" for logged-in users
        payload: Dict[str, Any] = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Dependency to extract and validate the current user from JWT.
    Raises HTTPException with 401 if token is invalid or missing.
    """
    token = credentials.credentials
    try:
        payload = decode_jwt(token)
        user_id = payload.get("sub")
        if not isinstance(user_id, str):
            raise AuthError("No user ID in token")
        email = payload.get("email")
        return {"user_id": user_id, "email": email if isinstance(email, str) else None}
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
