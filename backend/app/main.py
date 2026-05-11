import base64

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import library, search, upload
from app.config import settings

app = FastAPI(title="cadence", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(library.router)
app.include_router(search.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


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
