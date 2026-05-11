import numpy as np
import soundfile as sf

from app.services import audio_processor


def test_extract_features_on_sine_tone(tmp_path):
    """A 440 Hz A sine wave should report an estimated key in the A family."""
    sr = 22050
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = 0.3 * np.sin(2 * np.pi * 440.0 * t)
    p = tmp_path / "sine.wav"
    sf.write(p, y, sr)

    feats = audio_processor.extract_features(p)
    assert feats["duration_sec"] > 1.5
    assert feats["estimated_key"] in {"A", "G#", "A#"}  # neighborhood tolerance
    assert feats["estimated_mode"] in {"major", "minor"}
    assert len(feats["chroma_profile"]) == 12
