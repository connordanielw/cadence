"""Test fixtures: an in-memory app with the LLM + embedding services stubbed.

Real model calls would make the test suite slow and require API keys in CI.
"""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Force an env-friendly default before anything imports app.config
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://cadence:cadence@db:5432/cadence")


@pytest.fixture
def fake_embed():
    """Return a deterministic 1024-dim vector keyed off the input string."""
    def _embed(text: str, input_type: str = "document"):
        import hashlib
        seed = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
        # Simple PRNG so the vector is reproducible without numpy
        out: list[float] = []
        x = seed
        for _ in range(1024):
            x = (1103515245 * x + 12345) & 0x7FFFFFFF
            out.append((x / 0x7FFFFFFF) - 0.5)
        return out
    return _embed


@pytest.fixture
def fake_tag():
    def _tag(context):
        return {
            "mood": ["melancholy", "still"],
            "key": "C minor",
            "tempo_feel": "lethargic",
            "era": "Romantic",
            "instrumentation": ["solo piano"],
            "summary": "A quiet, melancholy solo piano piece in C minor.",
        }
    return _tag


@pytest.fixture
def fake_describe():
    def _describe(tags, context):
        return "A quiet, melancholy solo piano piece in C minor with a still, lethargic feel."
    return _describe
