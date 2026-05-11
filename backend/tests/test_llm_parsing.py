"""Confirm the JSON-extraction helper handles Claude's common quirks."""
import pytest

from app.services.llm import _parse_json


def test_plain_json():
    out = _parse_json('{"mood": ["sad"], "key": "C minor"}')
    assert out["mood"] == ["sad"]


def test_fenced_json():
    text = """```json
{"mood": ["sad"], "key": "C minor"}
```"""
    out = _parse_json(text)
    assert out["key"] == "C minor"


def test_invalid_json_raises():
    with pytest.raises(Exception):
        _parse_json("not json at all")
