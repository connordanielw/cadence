"""Clerk JWT verification for FastAPI routes."""
from __future__ import annotations

import base64
import logging

import jwt
from fastapi import Header, HTTPException
from jwt import PyJWKClient

from app.config import settings

logger = logging.getLogger(__name__)

_jwks_client: PyJWKClient | None = None


def _derive_jwks_url(publishable_key: str) -> str:
    """Derive Clerk JWKS URL from the publishable key.

    Format: pk_test_<base64url_frontend_api>$ or pk_live_<base64url_frontend_api>$
    The base64url segment decodes to the Clerk Frontend API hostname.
    """
    b64 = publishable_key.split("_", 2)[2].rstrip("$")
    padded = b64 + "=" * (-len(b64) % 4)
    frontend_api = base64.urlsafe_b64decode(padded).decode()
    return f"https://{frontend_api}/.well-known/jwks.json"


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        if not settings.clerk_publishable_key:
            raise RuntimeError("CLERK_PUBLISHABLE_KEY is not set")
        jwks_url = _derive_jwks_url(settings.clerk_publishable_key)
        logger.info("Clerk JWKS URL: %s", jwks_url)
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
    return _jwks_client


async def get_current_user_id(authorization: str | None = Header(None)) -> str:
    """FastAPI dependency — returns the Clerk user ID from the Bearer JWT."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return str(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as exc:
        logger.warning("JWT verification failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid token")
