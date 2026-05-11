"""Voyage AI embedding service."""
from __future__ import annotations

import voyageai

from app.config import settings

_client: voyageai.Client | None = None


def _client_singleton() -> voyageai.Client:
    global _client
    if _client is None:
        _client = voyageai.Client(api_key=settings.voyage_api_key)
    return _client


def embed(text: str, input_type: str = "document") -> list[float]:
    """input_type is 'document' for indexing, 'query' for search-time."""
    result = _client_singleton().embed(
        texts=[text],
        model=settings.voyage_model,
        input_type=input_type,
    )
    return result.embeddings[0]
