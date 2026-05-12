"""Extract a rich audio feature vector with librosa and render a mel-spectrogram image.

Features are grouped into:
  - Global: tempo, key, duration, energy, brightness
  - Timbre:  MFCCs, spectral contrast (helps Claude infer instrument families)
  - Dynamics: onset strength, dynamic range across the piece
  - Segments: beginning / middle / end snapshots so Claude can detect transitions
    (e.g. quiet intro → lush climax → cinematic drum outro)
  - Spectrogram: a base64-encoded mel-spectrogram PNG sent directly to Claude vision
"""
from __future__ import annotations

import base64
import io
from pathlib import Path

import librosa
import librosa.display
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")  # non-interactive backend — no display needed


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


def _render_spectrogram(y: np.ndarray, sr: int) -> str:
    """Render a mel-spectrogram as a base64-encoded PNG string.

    The image gives Claude's vision model direct access to frequency/time content:
      - Sustained horizontal bands → strings, pads, sustained piano
      - Vertical striations → percussive transients, piano attacks, drums
      - Harmonic overtone series → instrument family identification
      - Brightness distribution → timbral character
    """
    # Use a 2-panel layout: mel-spectrogram top, onset/chroma bottom
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), facecolor="#111")
    fig.subplots_adjust(hspace=0.45)

    # ── Panel 1: Mel-spectrogram ──────────────────────────────────────
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
    mel_db = librosa.power_to_db(mel, ref=np.max)
    img = librosa.display.specshow(
        mel_db, y_axis="mel", x_axis="time", sr=sr, fmax=8000, ax=axes[0], cmap="magma"
    )
    axes[0].set_title("Mel Spectrogram", color="white", fontsize=9)
    axes[0].tick_params(colors="white", labelsize=7)
    axes[0].set_ylabel("Hz", color="white", fontsize=7)
    axes[0].set_facecolor("#111")
    for spine in axes[0].spines.values():
        spine.set_edgecolor("#444")

    # ── Panel 2: Chromagram ───────────────────────────────────────────
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    librosa.display.specshow(
        chroma, y_axis="chroma", x_axis="time", sr=sr, ax=axes[1], cmap="coolwarm"
    )
    axes[1].set_title("Chroma (Pitch Content)", color="white", fontsize=9)
    axes[1].tick_params(colors="white", labelsize=7)
    axes[1].set_ylabel("Pitch", color="white", fontsize=7)
    axes[1].set_facecolor("#111")
    for spine in axes[1].spines.values():
        spine.set_edgecolor("#444")

    # ── Panel 3: Onset strength (rhythm profile) ──────────────────────
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    times = librosa.times_like(onset_env, sr=sr)
    axes[2].fill_between(times, onset_env, color="#e85d04", alpha=0.8)
    axes[2].set_title("Onset Strength (Rhythm / Attack)", color="white", fontsize=9)
    axes[2].tick_params(colors="white", labelsize=7)
    axes[2].set_xlabel("Time (s)", color="white", fontsize=7)
    axes[2].set_ylabel("Strength", color="white", fontsize=7)
    axes[2].set_facecolor("#111")
    for spine in axes[2].spines.values():
        spine.set_edgecolor("#444")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=90, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return base64.standard_b64encode(buf.read()).decode()


def extract_features(audio_path: Path) -> dict:
    y, sr = librosa.load(str(audio_path), mono=True, duration=180.0)  # cap at 3 min

    duration = float(librosa.get_duration(y=y, sr=sr))

    # ── Global tempo ──────────────────────────────────────────────────
    tempo_raw, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(np.asarray(tempo_raw).flat[0])

    # Key detection intentionally omitted — Krumhansl-Schmuckler is
    # unreliable on real recordings. Users set key manually via the edit UI.
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)

    # ── Timbre: MFCCs ─────────────────────────────────────────────────
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_mean = [round(float(x), 2) for x in mfcc.mean(axis=1)]

    # ── Spectral contrast (7 bands) ───────────────────────────────────
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

    # ── Mel-spectrogram image for Claude vision ───────────────────────
    spectrogram_b64 = _render_spectrogram(y, sr)

    return {
        # Basics
        "duration_sec": round(duration, 1),
        "tempo_bpm": round(tempo, 1),

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

        # Spectrogram image (base64 PNG) — sent to Claude vision
        "spectrogram_b64": spectrogram_b64,
    }
