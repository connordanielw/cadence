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
