"""ElevenLabs text-to-speech: the only third-party service SwaBodh can use.

Security: this code runs on your computer (or your server), never in the browser. The API key is
read from the environment (.env) and is only ever sent to api.elevenlabs.io in a request header.
It is not logged, not shown on screen and not included in error messages.
"""
import hashlib
import re

import requests

from .config import (
    AUDIO_CACHE_DIR,
    ELEVENLABS_API_KEY,
    ELEVENLABS_MODEL_ID,
    ELEVENLABS_VOICE_ID,
    ENV_PATH,
)
API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
OUTPUT_FORMAT = "mp3_44100_128"
MAX_CHARS = 2500  # keeps credit use predictable

_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")


def is_configured() -> bool:
    return bool(ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID)


def _say_date(match) -> str:
    month, day = int(match.group(2)), int(match.group(3))
    if 1 <= month <= 12:
        return f"{_MONTHS[month - 1]} {day}"
    return match.group(0)


def to_speech_text(text: str) -> str:
    """Rewrites on-screen text so it sounds natural when spoken (units, dates, signs)."""
    text = _DATE.sub(_say_date, text)
    text = re.sub(r"(\d) bpm\b", r"\1 beats per minute", text)
    text = re.sub(r"(\d) ms\b", r"\1 milliseconds", text)
    text = re.sub(r"(\d) min\b", r"\1 minutes", text)
    text = re.sub(r"(\d)%", r"\1 percent", text)
    text = re.sub(r"(?<![\w.])\+(?=\d)", "plus ", text)
    text = re.sub(r"(?<![\w.])-(?=\d)", "minus ", text)
    return re.sub(r"\s+", " ", text).strip()


def prepare(text: str) -> str:
    """Trims overly long text at a sentence boundary."""
    text = text.strip()
    if len(text) <= MAX_CHARS:
        return text
    cut = text[:MAX_CHARS]
    last = cut.rfind(". ")
    return cut[: last + 1] if last > 200 else cut


def _cache_path(text: str):
    raw = f"{ELEVENLABS_VOICE_ID}|{ELEVENLABS_MODEL_ID}|{text}".encode("utf-8")
    return AUDIO_CACHE_DIR / f"{hashlib.sha256(raw).hexdigest()[:32]}.mp3"


def is_cached(text: str) -> bool:
    return _cache_path(prepare(text)).exists()


def _error_detail(response):
    """Reads ElevenLabs' own error code and message (never contains your key)."""
    try:
        data = response.json()
    except Exception:
        return "", ""
    detail = data.get("detail") if isinstance(data, dict) else None
    if isinstance(detail, dict):
        return str(detail.get("status", "")), str(detail.get("message", ""))
    if isinstance(detail, str):
        return "", detail
    return "", ""


def _friendly_error(status: int, code: str = "", message: str = "") -> str:
    by_code = {
        "detected_unusual_activity": (
            "ElevenLabs blocked this request as 'unusual activity'. Free plans are blocked when a "
            "VPN or proxy is on. Turn the VPN off, or upgrade the plan."
        ),
        "invalid_api_key": "ElevenLabs says the API key is invalid. Copy it again into ELEVENLABS_API_KEY in .env.",
        "missing_permissions": (
            "Your ElevenLabs API key is restricted. In ElevenLabs open Developers > API Keys, edit "
            "the key and set 'Text to Speech' to Access (or create a new unrestricted key)."
        ),
        "voice_not_found": (
            "ElevenLabs cannot find that voice ID on your account. Add the voice to My Voices, "
            "then copy its ID again."
        ),
        "paid_plan_required": (
            "This voice or feature needs a paid ElevenLabs plan. On a free plan, community Voice Library voices "
            "cannot be used through the API. Try a voice you created with Voice Design using model eleven_v3."
        ),
        "quota_exceeded": "Your ElevenLabs credits are used up. Wait for the monthly reset or top up.",
    }
    if code in by_code:
        return f"{by_code[code]} (ElevenLabs code: {code})"
    by_status = {
        401: "ElevenLabs rejected the API key. Check ELEVENLABS_API_KEY in your .env file.",
        402: "ElevenLabs says this voice or feature needs a paid plan. Try a different voice ID.",
        404: "ElevenLabs cannot find that voice ID. Check ELEVENLABS_VOICE_ID in your .env file.",
        422: "ElevenLabs could not accept the request. Check that ELEVENLABS_VOICE_ID is correct.",
        429: "ElevenLabs is rate limiting you, or your credits are used up. Try again later.",
    }
    base = by_status.get(status, f"ElevenLabs returned an error (status {status}).")
    extra = f" (ElevenLabs says: {message[:140]})" if message else ""
    return base + extra


def setup_report() -> list:
    """Checklist for the Privacy/Listen pages: [(ok, title, how_to_fix), ...]."""
    env_txt = ENV_PATH.with_name(".env.txt")
    if ENV_PATH.exists():
        env_hint = ""
    elif env_txt.exists():
        env_hint = "Your file is called .env.txt. Rename it to exactly .env (no .txt)."
    else:
        env_hint = f"Create a file named .env in {ENV_PATH.parent} (copy .env.example)."
    return [
        (ENV_PATH.exists(), ".env file found", env_hint),
        (bool(ELEVENLABS_API_KEY), "ELEVENLABS_API_KEY has a value", "Paste your key after the = sign, then restart the app."),
        (bool(ELEVENLABS_VOICE_ID), "ELEVENLABS_VOICE_ID has a value", "Paste the voice ID after the = sign, then restart the app."),
    ]


def run_voice_check():
    """Speaks one short test sentence. Returns (ok, message)."""
    audio, err = speak("SwaBodh voice is working.")
    if err:
        return False, err
    return True, "Voice works. ElevenLabs accepted your key and voice ID."


def speak(text: str):
    """Returns (mp3_bytes, error_message). Exactly one of the two is None.
    Identical text is replayed from a local cache, which costs no ElevenLabs credits."""
    if not is_configured():
        return None, (
            "ElevenLabs is not set up yet. Add ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID "
            "to your .env file, then restart the app."
        )
    text = prepare(text)
    if not text:
        return None, "There is no text to read aloud."

    path = _cache_path(text)
    if path.exists():
        try:
            return path.read_bytes(), None
        except OSError:
            pass

    try:
        payload = {"text": text, "model_id": ELEVENLABS_MODEL_ID}
        # Eleven v3 does not support the stability/similarity voice_settings fields.
        if ELEVENLABS_MODEL_ID != "eleven_v3":
            payload["voice_settings"] = {"stability": 0.5, "similarity_boost": 0.75}

        response = requests.post(
            API_URL.format(voice_id=ELEVENLABS_VOICE_ID),
            params={"output_format": OUTPUT_FORMAT},
            headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
            json=payload,
            timeout=45,
        )
    except requests.RequestException as exc:
        return None, f"Could not reach ElevenLabs ({type(exc).__name__}). Check your internet connection."
    if response.status_code != 200:
        return None, _friendly_error(response.status_code)

    audio = response.content
    try:
        AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_bytes(audio)
    except OSError:
        pass  # caching is a bonus; playing the audio still works
    return audio, None


def clear_audio_cache() -> int:
    """Deletes every saved audio file. Returns how many were removed."""
    removed = 0
    if AUDIO_CACHE_DIR.exists():
        for file in AUDIO_CACHE_DIR.glob("*.mp3"):
            try:
                file.unlink()
                removed += 1
            except OSError:
                pass
    return removed
