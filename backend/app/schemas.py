from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class PieceTags(BaseModel):
    mood: list[str] = []
    key: str | None = None  # e.g. "C minor"
    tempo_feel: str | None = None  # "lethargic" | "driving" | etc
    bpm: int | None = None
    era: str | None = None
    instrumentation: list[str] = []
    summary: str | None = None


class PieceOut(BaseModel):
    id: int
    title: str
    source_type: Literal["pdf", "audio"]
    status: str
    llm_tags: PieceTags | None = None
    description: str | None = None
    error: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class PieceWithScore(PieceOut):
    score: float


class PiecePatch(BaseModel):
    description: str | None = None
    llm_tags: PieceTags | None = None


class SearchRequest(BaseModel):
    q: str
    limit: int = 20
    mood: str | None = None
    key: str | None = None
    era: str | None = None
