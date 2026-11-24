import pytest

from swabodh import voice


class FakeResponse:
    def __init__(self, status_code=200, content=b"FAKE-MP3"):
        self.status_code = status_code
        self.content = content


@pytest.fixture()
def configured(monkeypatch, tmp_path):
    monkeypatch.setattr(voice, "ELEVENLABS_API_KEY", "test-key-not-real")
    monkeypatch.setattr(voice, "ELEVENLABS_VOICE_ID", "voice123")
    monkeypatch.setattr(voice, "AUDIO_CACHE_DIR", tmp_path / "audio")


def test_not_configured_gives_friendly_message(monkeypatch):
    monkeypatch.setattr(voice, "ELEVENLABS_API_KEY", "")
    audio, err = voice.speak("Hello")
    assert audio is None and "not set up" in err


def test_speech_text_is_natural():
    spoken = voice.to_speech_text(
        "Ring now reads about 6.3 bpm higher around 2026-11-04. Difference: +20.6 min, range -4.8 to +36.4 min, 99% chance."
    )
    assert "beats per minute" in spoken
    assert "November 4" in spoken
    assert "plus 20.6 minutes" in spoken
    assert "minus 4.8" in spoken
    assert "99 percent" in spoken


def test_successful_call_uses_key_in_header_only_and_caches(configured, monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse()

    monkeypatch.setattr(voice.requests, "post", fake_post)
    audio, err = voice.speak("Your sleep improved.")
    assert audio == b"FAKE-MP3" and err is None
    url, kwargs = calls[0]
    assert "test-key-not-real" not in url
    assert kwargs["headers"]["xi-api-key"] == "test-key-not-real"
    assert "test-key-not-real" not in str(kwargs["json"])
    assert voice.is_cached("Your sleep improved.")

    audio2, _ = voice.speak("Your sleep improved.")  # second time: from cache, no new call
    assert audio2 == b"FAKE-MP3" and len(calls) == 1


@pytest.mark.parametrize("status", [401, 402, 429, 500])
def test_errors_are_friendly_and_never_leak_the_key(configured, monkeypatch, status):
    monkeypatch.setattr(voice.requests, "post", lambda url, **kw: FakeResponse(status, b""))
    audio, err = voice.speak("Hello there")
    assert audio is None and err
    assert "test-key-not-real" not in err


def test_network_failure_is_handled(configured, monkeypatch):
    def boom(url, **kw):
        raise voice.requests.ConnectionError("no internet")

    monkeypatch.setattr(voice.requests, "post", boom)
    audio, err = voice.speak("Hello there")
    assert audio is None and "Could not reach ElevenLabs" in err


def test_clear_audio_cache(configured, monkeypatch):
    monkeypatch.setattr(voice.requests, "post", lambda url, **kw: FakeResponse())
    voice.speak("Some text")
    assert voice.clear_audio_cache() == 1
    assert not voice.is_cached("Some text")
