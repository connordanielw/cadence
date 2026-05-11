import base64

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import library, search, upload
from app.config import settings

app = FastAPI(title="cadence", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(library.router)
app.include_router(search.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/health/verify")
async def health_verify(request: Request) -> dict:
    """Debug — tries to verify the Bearer token and returns the result."""
    from app.auth import _derive_jwks_url, _get_jwks_client
    import jwt as pyjwt
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return {"error": "No Bearer token in Authorization header"}
    token = auth.split(" ", 1)[1]
    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        payload = pyjwt.decode(token, signing_key.key, algorithms=["RS256"], options={"verify_aud": False})
        return {"ok": True, "sub": payload.get("sub"), "iss": payload.get("iss")}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


@app.get("/health/headers")
async def health_headers(request: Request) -> dict:
    """Debug — shows which headers arrived (auth token partially redacted)."""
    auth = request.headers.get("authorization", "")
    return {
        "authorization_present": bool(auth),
        "authorization_preview": auth[:30] + "…" if len(auth) > 30 else auth,
        "origin": request.headers.get("origin", ""),
    }


@app.get("/health/clerk")
def health_clerk() -> dict:
    """Debug endpoint — confirms Clerk config is loaded correctly."""
    key = settings.clerk_publishable_key
    if not key:
        return {"clerk_key_set": False, "jwks_url": None}
    try:
        b64 = key.split("_", 2)[2]
        padded = b64 + "=" * (-len(b64) % 4)
        frontend_api = base64.urlsafe_b64decode(padded).decode().rstrip("$")
        jwks_url = f"https://{frontend_api}/.well-known/jwks.json"
        return {"clerk_key_set": True, "jwks_url": jwks_url}
    except Exception as exc:
        return {"clerk_key_set": True, "jwks_url": None, "error": str(exc)}
