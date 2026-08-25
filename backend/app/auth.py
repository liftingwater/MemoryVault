"""Authentication module for Supabase JWT validation."""

from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

security = HTTPBearer()

# Supabase signs access tokens with an ES256 asymmetric key. We verify against
# the project's published JWKS and accept ES256 only — there is no symmetric
# fallback, which removes any shared-secret forgery/algorithm-confusion path.
_ALGORITHM = "ES256"

_jwks_client: Optional[jwt.PyJWKClient] = None


def _get_jwks_client() -> jwt.PyJWKClient:
    """Return a cached PyJWKClient pointed at the Supabase JWKS endpoint."""
    global _jwks_client
    if _jwks_client is None:
        base = settings.supabase_url.rstrip("/")
        _jwks_client = jwt.PyJWKClient(
            f"{base}/auth/v1/.well-known/jwks.json",
            cache_keys=True,
        )
    return _jwks_client


class AuthError(Exception):
    """Raised when authentication fails."""

    pass


def decode_jwt(token: str) -> Dict[str, Any]:
    """Decode and verify a Supabase ES256 JWT via the project's JWKS."""
    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") != _ALGORITHM:
            raise AuthError("Invalid token")

        signing_key = _get_jwks_client().get_signing_key_from_jwt(token).key
        # Supabase tokens have audience "authenticated" for logged-in users
        payload: Dict[str, Any] = jwt.decode(
            token,
            signing_key,
            algorithms=[_ALGORITHM],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")
    except AuthError:
        raise
    except Exception:
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
