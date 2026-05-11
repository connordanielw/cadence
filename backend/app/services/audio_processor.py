"""Extract a compact audio feature vector with librosa.

We deliberately keep the feature surface small — Claude does the heavy lifting
turning these numbers into descriptive tags.
"""
from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np

# Krumhansl-Schmuckler key profiles
_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
_PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def extract_features(audio_path: Path) -> dict:
    y, sr = librosa.load(str(audio_path), mono=True, duration=120.0)  # cap at 2 min

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
    rms = float(librosa.feature.rms(y=y).mean())
    zcr = float(librosa.feature.zero_crossing_rate(y=y).mean())
    duration = float(librosa.get_duration(y=y, sr=sr))

    key, mode = _estimate_key(chroma)

    return {
        "tempo_bpm": float(tempo),
        "estimated_key": key,
        "estimated_mode": mode,
        "spectral_centroid_hz": centroid,
        "rms_energy": rms,
        "zero_crossing_rate": zcr,
        "duration_sec": duration,
        "chroma_profile": [float(x) for x in chroma],
    }


def _estimate_key(chroma: np.ndarray) -> tuple[str, str]:
    """Return (pitch_class, 'major'|'minor') via correlation against KS profiles."""
    scores: list[tuple[float, str, str]] = []
    for i in range(12):
        rolled_maj = np.roll(_MAJ, i)
        rolled_min = np.roll(_MIN, i)
        scores.append((float(np.corrcoef(chroma, rolled_maj)[0, 1]), _PITCH_NAMES[i], "major"))
        scores.append((float(np.corrcoef(chroma, rolled_min)[0, 1]), _PITCH_NAMES[i], "minor"))
    scores.sort(reverse=True)
    _, pitch, mode = scores[0]
    return pitch, mode
