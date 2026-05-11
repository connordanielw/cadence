"""Claude tagging service.

Given raw PDF text or an audio feature dict, returns structured tags and a one-paragraph
natural-language description that we'll later embed.
"""
from __future__ import annotations

import json
import re
from typing import Any

import anthropic

from app.config import settings

_SYSTEM = """You are a musicologist tagging a music library. Given some context about a piece
(either OCR'd sheet music text or a feature vector from audio analysis), return a single JSON
object — no prose, no markdown — with these keys:

  mood:            array of 1-4 mood words ("melancholy", "driving", "playful", ...)
  key:             best-guess key e.g. "C minor" or "E♭ major". For sheet music look for
                   explicit key markings, title clues, or signature accidentals. For audio
                   use the estimated_key + estimated_mode fields. Return null if genuinely unclear.
  tempo_feel:      one of "still", "lethargic", "moderate", "brisk", "driving", "frantic", or null
  bpm:             numeric BPM as an integer, or null. For audio use tempo_bpm rounded to nearest
                   integer. For sheet music look for metronome marks like "♩= 120" or "q = 96",
                   or convert Italian tempo words (Largo≈50, Adagio≈66, Andante≈80, Moderato≈100,
                   Allegro≈130, Presto≈180). Return null if no indication exists.
  era:             rough era — "Baroque", "Classical", "Romantic", "Impressionist",
                   "20th century", "Contemporary", "Jazz", or null
  instrumentation: array of detected instruments / textures
  summary:         one-sentence plain-English summary of what this piece sounds or looks like

Be conservative on key — null is better than a wrong answer. Never invent composers or titles."""

_DESC_SYSTEM = """Write a single paragraph (2-3 sentences) describing this piece's overall sound
and feel, suitable as the basis for semantic search. Plain prose. No headers, no bullets."""


_client: anthropic.Anthropic | None = None


def _client_singleton() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def tag(context: str | dict[str, Any]) -> dict:
    """Return the parsed JSON tag object."""
    user = _format_context(context)
    msg = _client_singleton().messages.create(
        model=settings.claude_model,
        max_tokens=600,
        system=_SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(block.text for block in msg.content if block.type == "text")
    return _parse_json(text)


def describe(tags: dict, context: str | dict[str, Any]) -> str:
    """One-paragraph description we then embed for search."""
    payload = json.dumps({"tags": tags, "context": _format_context(context)[:4000]})
    msg = _client_singleton().messages.create(
        model=settings.claude_model,
        max_tokens=240,
        system=_DESC_SYSTEM,
        messages=[{"role": "user", "content": payload}],
    )
    return "".join(block.text for block in msg.content if block.type == "text").strip()


def _format_context(context: str | dict[str, Any]) -> str:
    if isinstance(context, str):
        return f"PDF text (truncated):\n\n{context[:6000]}"
    return f"Audio features:\n\n{json.dumps(context, indent=2)}"


def _parse_json(text: str) -> dict:
    text = text.strip()
    # Strip code fences if Claude wrapped the JSON despite instructions.
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)
