"""Extract a rich audio feature vector with librosa.

Features are grouped into:
  - Global: tempo, key, duration, energy, brightness
  - Timbre:  MFCCs, spectral contrast (helps Claude infer instrument families)
  - Dynamics: onset strength, dynamic range across the piece
  - Segments: beginning / middle / end snapshots so Claude can detect transitions
    (e.g. quiet intro → lush climax → cinematic drum outro)
"""
from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np

# Krumhansl-Schmuckler key profiles
_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
_PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _estimate_key(chroma: np.ndarray) -> tuple[str, str]:
    scores: list[tuple[float, str, str]] = []
    for i in range(12):
        scores.append((float(np.corrcoef(chroma, np.roll(_MAJ, i))[0, 1]), _PITCH_NAMES[i], "major"))
        scores.append((float(np.corrcoef(chroma, np.roll(_MIN, i))[0, 1]), _PITCH_NAMES[i], "minor"))
    scores.sort(reverse=True)
    return scores[0][1], scores[0][2]


def _segment_features(y: np.ndarray, sr: int) -> dict:
    """Return energy + brightness + onset_mean for this audio segment."""
    if len(y) < sr:  # too short
        return {}
    rms = float(librosa.feature.rms(y=y).mean())
    centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_mean = float(onset_env.mean())
    onset_peak = float(onset_env.max())
    return {
        "rms_energy": round(rms, 5),
        "spectral_centroid_hz": round(centroid, 1),
        "onset_strength_mean": round(onset_mean, 4),
        "onset_strength_peak": round(onset_peak, 4),
    }


def extract_features(audio_path: Path) -> dict:
    y, sr = librosa.load(str(audio_path), mono=True, duration=180.0)  # cap at 3 min

    duration = float(librosa.get_duration(y=y, sr=sr))

    # ── Global tempo & key ────────────────────────────────────────────
    tempo_raw, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(np.asarray(tempo_raw).flat[0])

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    key, mode = _estimate_key(chroma)

    # ── Timbre: MFCCs ─────────────────────────────────────────────────
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_mean = [round(float(x), 2) for x in mfcc.mean(axis=1)]

    # ── Spectral contrast (7 bands) ───────────────────────────────────
    # High contrast in upper bands → bright, percussive (strings, brass, cymbals)
    # Low overall contrast → smooth, sustained (pads, choir)
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    contrast_mean = [round(float(x), 2) for x in contrast.mean(axis=1)]

    # ── Global dynamics ───────────────────────────────────────────────
    rms_full = librosa.feature.rms(y=y)[0]
    dynamic_range = round(float(rms_full.max() - rms_full.min()), 5)
    rms_mean = round(float(rms_full.mean()), 5)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_mean = round(float(onset_env.mean()), 4)

    rolloff = float(librosa.feature.spectral_rolloff(y=y, sr=sr).mean())
    zcr = float(librosa.feature.zero_crossing_rate(y=y).mean())

    # ── Segment analysis: split into thirds ───────────────────────────
    third = len(y) // 3
    seg_start  = _segment_features(y[:third], sr)
    seg_middle = _segment_features(y[third:2*third], sr)
    seg_end    = _segment_features(y[2*third:], sr)

    return {
        # Basics
        "duration_sec": round(duration, 1),
        "tempo_bpm": round(tempo, 1),
        "estimated_key": key,
        "estimated_mode": mode,

        # Global energy & colour
        "rms_energy_mean": rms_mean,
        "dynamic_range": dynamic_range,
        "spectral_centroid_hz": round(rolloff, 1),
        "zero_crossing_rate": round(zcr, 5),
        "onset_strength_mean": onset_mean,

        # Timbre
        "mfcc_mean": mfcc_mean,
        "spectral_contrast_mean": contrast_mean,

        # Segment snapshots (beginning / middle / end)
        "segment_start":  seg_start,
        "segment_middle": seg_middle,
        "segment_end":    seg_end,

        # Raw chroma
        "chroma_profile": [round(float(x), 4) for x in chroma],
    }
