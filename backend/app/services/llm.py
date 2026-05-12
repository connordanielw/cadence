"""Claude tagging service.

Given raw PDF text or an audio feature dict (including a mel-spectrogram image),
returns structured tags and a one-paragraph natural-language description.

For audio, we pass Claude:
  1. A mel-spectrogram image (3-panel: mel-freq, chromagram, onset strength)
     so its vision model can directly "see" the frequency / rhythm content.
  2. The numeric feature vector for precise BPM, key, dynamics, etc.
"""
from __future__ import annotations

import json
import re
from typing import Any

import anthropic

from app.config import settings

_SYSTEM = """You are an expert music analyst tagging pieces for a semantic search library.

You will receive either:

A) AUDIO — a mel-spectrogram image (3 panels) PLUS a JSON feature vector.

   Reading the spectrogram:
   - Panel 1 (Mel Spectrogram, magma colormap): frequency (y-axis, Hz) over time (x-axis).
     Bright horizontal bands = sustained tones. Bright vertical stripes = percussive attacks.
     Low bright bands (100-500 Hz) = bass / cello / viola / left-hand piano.
     Mid bands (500-3000 Hz) = violin, clarinet, mid piano.
     High bands (3k-8k Hz) = flute overtones, cymbal shimmer, high string harmonics.
     Dense harmonic stacks (multiple parallel bands) = strings ensemble or piano.
     Isolated bright blobs with fast decay = piano key strikes.
   - Panel 2 (Chroma): pitch class energy over time. Use this to understand
     harmonic character and texture — NOT to guess key (always return null for key on audio).
   - Panel 3 (Onset Strength): rhythmic attack density.
     Tall spikes = hard percussion / piano attacks. Low flat line = sustained, legato.

   Feature vector fields:
     tempo_bpm, estimated_key, estimated_mode — use these directly
     mfcc_mean — MFCC[1] high = bright/thin; low = warm/full. MFCC[0] = loudness.
     spectral_contrast_mean — 7 bands. High upper-band contrast = bright/percussive.
     dynamic_range — difference between loudest and quietest moments.
     onset_strength_mean — High = percussive/rhythmic, low = legato/sustained.
     segment_start / segment_middle / segment_end — per-section snapshots.
       Use these for structural changes (quiet intro → climax → outro, etc.)

B) SHEET MUSIC — OCR'd text. Look for tempo markings, dynamics, clefs,
   key signatures, instrument labels.

Return ONLY a single JSON object — no prose, no markdown fences:

  mood:            2-4 mood descriptors. Be specific and honest — if the piece
                   builds from dark to triumphant, use both.
  key:             Always null for audio input — key detection from audio is
                   unreliable and will be set manually by the user. For sheet
                   music only: e.g. "D minor".
  tempo_feel:      "still" | "lethargic" | "moderate" | "brisk" | "driving" | "frantic" | null
  bpm:             integer from tempo_bpm (audio) or metronome mark (sheet music), or null
  era:             "Baroque" | "Classical" | "Romantic" | "Impressionist" |
                   "20th century" | "Contemporary" | "Film/Game" | "Jazz" | null
  instrumentation: array of specific instruments/textures you can confidently identify.
                   Use the spectrogram visually — look for sustained harmonic stacks
                   (strings), isolated bright transients (piano), dense high-frequency
                   shimmer (cymbals/brass). Be specific but honest — only list what
                   the spectrogram clearly shows.
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
    messages = _build_messages(context)
    msg = _client_singleton().messages.create(
        model=settings.claude_model,
        max_tokens=600,
        system=_SYSTEM,
        messages=messages,
    )
    text = "".join(block.text for block in msg.content if block.type == "text")
    return _parse_json(text)


def describe(tags: dict, context: str | dict[str, Any]) -> str:
    """One-paragraph description we then embed for search."""
    # Strip the spectrogram image from context for the describe call (saves tokens)
    if isinstance(context, dict):
        context_clean = {k: v for k, v in context.items() if k != "spectrogram_b64"}
    else:
        context_clean = context
    payload = json.dumps({"tags": tags, "context": _format_context_text(context_clean)[:4000]})
    msg = _client_singleton().messages.create(
        model=settings.claude_model,
        max_tokens=240,
        system=_DESC_SYSTEM,
        messages=[{"role": "user", "content": payload}],
    )
    return "".join(block.text for block in msg.content if block.type == "text").strip()


def _build_messages(context: str | dict[str, Any]) -> list[dict]:
    """Build the messages array, including the spectrogram image for audio."""
    if isinstance(context, dict) and "spectrogram_b64" in context:
        spec_b64 = context["spectrogram_b64"]
        # Feature vector without the image (keep it readable)
        features = {k: v for k, v in context.items() if k != "spectrogram_b64"}
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": spec_b64,
                },
            },
            {
                "type": "text",
                "text": (
                    "Above is the mel-spectrogram (3 panels) for this audio piece.\n\n"
                    "Audio feature vector:\n\n"
                    + json.dumps(features, indent=2)
                ),
            },
        ]
        return [{"role": "user", "content": content}]
    else:
        return [{"role": "user", "content": _format_context_text(context)}]


def _format_context_text(context: str | dict[str, Any]) -> str:
    if isinstance(context, str):
        return f"PDF text (truncated):\n\n{context[:6000]}"
    return f"Audio features:\n\n{json.dumps(context, indent=2)}"


def _parse_json(text: str) -> dict:
    text = text.strip()
    # Strip code fences if Claude wrapped the JSON despite instructions.
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)
