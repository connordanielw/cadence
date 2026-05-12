"""Claude LLM service.

Two jobs:
  1. expand_description — takes a user's rough description + piece title,
     returns a polished 2-3 sentence paragraph ready for semantic embedding.
  2. describe (sheet music only) — generates description from OCR'd PDF text.
"""
from __future__ import annotations

import json
import re
from typing import Any

import anthropic

from app.config import settings

_EXPAND_SYSTEM = """You are writing a description of a piece of music for a semantic search index.

The user has given you a rough description of what the piece sounds like. Expand it into
a rich, specific 2-3 sentence paragraph that captures instruments, texture, mood, tempo feel,
and any structural arc (e.g. builds, transitions, quiet endings).

Rules:
- Plain prose only — no headers, no bullets
- No hedging phrases like "seems to" or "appears to" — write with confidence
- Stay true to what the user described; do not invent details they didn't mention
- Be specific enough that a semantic search for "dark driving strings" or "calm impressionist piano"
  would correctly match or not match this piece
- Do not mention the title or composer"""

_PDF_SYSTEM = """You are an expert music analyst tagging sheet music for a semantic search library.

You receive OCR'd text from a score. Look for tempo markings, dynamics, clefs,
key signatures, instrument labels, and style indications.

Return ONLY a single JSON object — no prose, no markdown fences:

  mood:            2-4 mood descriptors
  key:             e.g. "D minor" or null if unclear
  tempo_feel:      "still" | "lethargic" | "moderate" | "brisk" | "driving" | "frantic" | null
  bpm:             integer from metronome mark, or null
  era:             "Baroque" | "Classical" | "Romantic" | "Impressionist" |
                   "20th century" | "Contemporary" | "Film/Game" | "Jazz" | null
  instrumentation: array of instruments found in the score
  summary:         one sentence capturing the piece's character

Never invent composer names or titles. Null beats a wrong answer."""

_PDF_DESC_SYSTEM = """Write a single paragraph (2-3 sentences) describing this piece's sound, feel,
and character for semantic search. Be specific: mention instruments, key, tempo, style, mood.
Plain prose — no headers, no bullets, no hedging phrases. Write as if you read the score."""


_client: anthropic.Anthropic | None = None


def _client_singleton() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def expand_description(user_text: str, title: str) -> str:
    """Expand a rough user description into a rich searchable paragraph."""
    prompt = f'Title: "{title}"\n\nUser description: {user_text}'
    msg = _client_singleton().messages.create(
        model=settings.claude_model,
        max_tokens=300,
        system=_EXPAND_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in msg.content if b.type == "text").strip()


# ── Sheet music (PDF) path ────────────────────────────────────────────────────

def tag_pdf(text: str) -> dict:
    """Return structured tags for a PDF score."""
    msg = _client_singleton().messages.create(
        model=settings.claude_model,
        max_tokens=600,
        system=_PDF_SYSTEM,
        messages=[{"role": "user", "content": f"PDF text (truncated):\n\n{text[:6000]}"}],
    )
    raw = "".join(b.text for b in msg.content if b.type == "text")
    return _parse_json(raw)


def describe_pdf(tags: dict, text: str) -> str:
    """One-paragraph description for a PDF score."""
    payload = json.dumps({"tags": tags, "score_text": text[:4000]})
    msg = _client_singleton().messages.create(
        model=settings.claude_model,
        max_tokens=240,
        system=_PDF_DESC_SYSTEM,
        messages=[{"role": "user", "content": payload}],
    )
    return "".join(b.text for b in msg.content if b.type == "text").strip()


def _parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)
