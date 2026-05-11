"""Local-disk storage. Swap for S3 by re-implementing the two functions."""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from app.config import settings


def _root() -> Path:
    p = Path(settings.storage_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_upload(filename: str, source) -> str:
    """Persist an upload stream. Returns the stored path (relative to storage root)."""
    ext = Path(filename).suffix.lower()
    stored = f"{uuid.uuid4().hex}{ext}"
    dest = _root() / stored
    with dest.open("wb") as f:
        shutil.copyfileobj(source, f)
    return stored


def absolute_path(stored: str) -> Path:
    return _root() / stored
