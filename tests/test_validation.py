import pytest

from engine import validate_request


def test_minimal_cover_request_defaults():
    result = validate_request({"source_audio_url": "https://example.com/song.mp3"})
    assert result["melody_only"] is True
    assert result["dtype"] == "bf16"
    assert result["preset"] == "default"


def test_requires_source_url():
    with pytest.raises(ValueError, match="source_audio_url"):
        validate_request({})


def test_rejects_unknown_field():
    with pytest.raises(ValueError, match="unsupported"):
        validate_request({"source_audio_url": "https://example.com/a.mp3", "lyrics": "nope"})


def test_rejects_invalid_dtype():
    with pytest.raises(ValueError, match="dtype"):
        validate_request({"source_audio_url": "https://example.com/a.mp3", "dtype": "fp16"})
