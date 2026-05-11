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

_SYSTEM = """You are an expert music analyst tagging pieces for a semantic search library.

For AUDIO features you receive a JSON object with:
  - tempo_bpm, estimated_key, estimated_mode — use these directly
  - mfcc_mean — timbral fingerprint. High MFCC[1] = bright/thin; low = warm/full.
    MFCC[0] is loudness. Higher-order MFCCs capture texture.
  - spectral_contrast_mean — 7 frequency bands. High values in bands 4-6 suggest
    bright/percussive timbres (strings, brass, cymbals, piano attacks).
    Low, uniform contrast = smooth pads, choir, sustained textures.
  - dynamic_range — difference between loudest and quietest moments. High = dramatic.
  - onset_strength_mean — rhythmic attack density. High = percussive/rhythmic,
    low = legato/sustained.
  - segment_start / segment_middle / segment_end — per-section snapshots of energy
    and onset strength. USE THESE to detect structural changes: e.g. if segment_end
    has much higher onset_strength_peak than the middle, there are likely drums or
    strong percussive events at the end. If rms_energy rises dramatically in the
    middle, there is a climax or build.

For SHEET MUSIC you receive OCR'd text. Look for tempo markings, dynamics, clefs,
key signatures, and instrument labels.

Return ONLY a single JSON object — no prose, no markdown fences:

  mood:            2-4 mood descriptors. Be specific and honest — if the piece
                   builds from dark to triumphant, use both.
  key:             e.g. "D minor" or null if unclear
  tempo_feel:      "still" | "lethargic" | "moderate" | "brisk" | "driving" | "frantic" | null
  bpm:             integer from tempo_bpm (audio) or metronome mark (sheet music), or null
  era:             "Baroque" | "Classical" | "Romantic" | "Impressionist" |
                   "20th century" | "Contemporary" | "Film/Game" | "Jazz" | null
  instrumentation: array of specific instruments/textures you can infer. For audio,
                   use spectral_contrast and mfcc to infer (e.g. high upper-band
                   contrast + high onset = strings/percussion; smooth low contrast =
                   pads/choir). Be as specific as features allow.
  summary:         one sentence capturing the piece's arc — mention if it builds,
                   transitions, or ends differently than it begins.

Never invent composer names or titles. Null beats a wrong answer."""

_DESC_SYSTEM = """Write a single paragraph (2-3 sentences) describing this piece's sound, feel,
and arc for semantic search. Be specific: mention instruments, textures, mood shifts, and how
the piece moves from beginning to end if it changes. Plain prose — no headers, no bullets,
no hedging phrases like "seems to" or "appears to". Write as if you heard it."""


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
