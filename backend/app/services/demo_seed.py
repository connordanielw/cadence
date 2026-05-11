"""Seed a demo piece called 'Arrival' for new users with empty libraries."""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import soundfile as sf
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Piece
from app.services import embedding

logger = logging.getLogger(__name__)

_DEMO_FILENAME = "arrival_demo.wav"

_DESCRIPTION = (
    "A slow, introspective ambient piece built around an arpeggiated A minor chord. "
    "Sparse and still, with delicate piano-like tones layered across three octaves. "
    "Contemplative and hushed — the feeling of arriving somewhere quiet after a long journey."
)

_TAGS: dict = {
    "mood": ["introspective", "atmospheric", "still"],
    "key": "A minor",
    "tempo_feel": "still",
    "bpm": 52,
    "era": "Contemporary",
    "instrumentation": ["piano", "ambient"],
    "summary": "Sparse ambient piano in A minor — slow, contemplative, and hushed.",
}


def _demo_audio_path() -> Path:
    root = Path(settings.storage_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root / _DEMO_FILENAME


def _generate_demo_audio(path: Path) -> None:
    """Synthesise a simple ambient piano chord and write it to disk."""
    sr = 22050
    duration = 40  # seconds

    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # Global fade-in / fade-out envelope
    fade = np.ones(len(t))
    fl = int(sr * 4)
    fade[:fl] = np.linspace(0, 1, fl) ** 2
    fade[-fl:] = np.linspace(1, 0, fl) ** 2

    y = np.zeros(len(t))

    # A minor arpeggio: A2 E3 A3 C4 E4 A4
    notes = [110.0, 164.81, 220.0, 261.63, 329.63, 440.0]
    for i, freq in enumerate(notes):
        delay = int(i * sr * 0.55)
        if delay >= len(t):
            continue
        dur = len(t) - delay
        # Piano envelope: instant attack, exponential decay (~6 s)
        env = np.exp(-np.arange(dur) / (sr * 6.0))
        wave = (
            np.sin(2 * np.pi * freq * t[delay:]) * 0.55
            + np.sin(2 * np.pi * freq * 2 * t[delay:]) * 0.20
            + np.sin(2 * np.pi * freq * 3 * t[delay:]) * 0.08
        )
        sig = np.zeros(len(t))
        sig[delay:] = env * wave * 0.18
        y += sig

    # Simple reverb: mix in a delayed + attenuated copy
    delay_samples = int(sr * 0.25)
    y_reverb = np.zeros_like(y)
    y_reverb[delay_samples:] = y[:-delay_samples] * 0.35
    y = (y + y_reverb) * fade

    peak = np.max(np.abs(y))
    if peak > 0:
        y = y / peak * 0.80

    sf.write(str(path), y.astype(np.float32), sr)
    logger.info("Generated demo audio: %s", path)


def ensure_demo_for_new_user(user_id: str, db: Session) -> None:
    """If this user has no pieces yet, create the Arrival demo piece."""
    count = db.scalar(
        select(func.count(Piece.id)).where(Piece.clerk_user_id == user_id)
    )
    if count and count > 0:
        return  # already has pieces

    # Generate (or reuse) the demo audio file
    demo_path = _demo_audio_path()
    if not demo_path.exists():
        try:
            _generate_demo_audio(demo_path)
        except Exception as exc:
            logger.warning("Could not generate demo audio: %s", exc)
            return

    # Embed the description so the demo piece is searchable
    vec = None
    try:
        vec = embedding.embed(_DESCRIPTION, input_type="document")
    except Exception as exc:
        logger.warning("Could not embed demo description: %s", exc)

    piece = Piece(
        clerk_user_id=user_id,
        title="Arrival",
        source_type="audio",
        source_path=_DEMO_FILENAME,
        status="ready",
        description=_DESCRIPTION,
        llm_tags=_TAGS,
        embedding=vec,
    )
    db.add(piece)
    db.commit()
    logger.info("Seeded demo piece 'Arrival' for user %s", user_id)
